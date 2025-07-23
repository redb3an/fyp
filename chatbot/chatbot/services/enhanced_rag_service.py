import logging
from typing import List, Dict, Any, Optional
from django.db.models import Q
from chatbot.models import KnowledgeBaseEntry, TrainingDataset
import re
from collections import Counter
from difflib import SequenceMatcher

# Defer vector library imports to avoid Django startup issues
VECTOR_SUPPORT = None  # Will be determined on first use

logger = logging.getLogger(__name__)


class EnhancedRAGService:
    """
    Enhanced Retrieval Augmented Generation service with comprehensive training data
    and optional vector embeddings (falls back to keyword search if vector libs unavailable)
    """
    
    def __init__(self, max_results: int = 8, min_confidence: float = 0.3):
        self.max_results = max_results
        self.min_confidence = min_confidence
        self.vector_enabled = None  # Will be determined on first use
        self.vector_initialized = False
        
        # Chunking parameters
        self.chunk_size = 512  # Characters per chunk
        self.chunk_overlap = 128  # Overlap between chunks
        
        # Category weights for enhanced relevance scoring
        self.category_weights = {
            'Programs and Courses': 1.2,
            'Curriculum and Modules': 1.15,
            'Fees and Financial Aid': 1.1,
            'Admissions': 1.1,
            'School of Computing': 1.1,
            'School of Business': 1.1,
            'School of Engineering': 1.1,
            'School of Accounting & Finance': 1.1,
            'Campus and Facilities': 1.0,
            'Student Life': 1.0,
            'General Information': 0.9,
            'Accommodation': 1.1,  # Added weight for accommodation queries
            'Study Mode': 1.1      # Added weight for study mode queries
        }
        
        # Program level hierarchy for better matching
        self.program_levels = {
            'Certificate': 1,
            'Foundation': 2, 
            'Diploma': 3,
            'Undergraduate': 4,
            'Postgraduate': 5,
            'Doctoral': 6,
            'Short & Language': 0
        }

    def _check_vector_support(self):
        """Check if vector libraries are available and initialize if needed"""
        global VECTOR_SUPPORT
        
        if self.vector_enabled is not None:
            return self.vector_enabled
        
        # Try to import vector libraries
        try:
            import numpy as np
            import faiss
            from sentence_transformers import SentenceTransformer
            
            self.vector_enabled = True
            VECTOR_SUPPORT = True
            logger.info("✓ Vector embeddings enabled (numpy, faiss, sentence-transformers)")
            
            # Store the imports for later use
            self.np = np
            self.faiss = faiss
            self.SentenceTransformer = SentenceTransformer
            
        except ImportError as e:
            self.vector_enabled = False
            VECTOR_SUPPORT = False
            logger.warning(f"⚠ Vector embeddings disabled due to import error: {e}")
            logger.info("🔄 Falling back to keyword-based search only")
        
        return self.vector_enabled

    def _initialize_vector_components(self):
        """Initialize vector processing components"""
        if not self._check_vector_support() or self.vector_initialized:
            return
            
        try:
            # Initialize sentence transformer for embeddings
            self.embedding_model = self.SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = 384  # Dimension of embeddings from the model
            
            # Initialize FAISS index for full entries and chunks
            self.full_index = self.faiss.IndexFlatL2(self.embedding_dim)
            self.chunk_index = self.faiss.IndexFlatL2(self.embedding_dim)
            self.entry_ids = []  # To map full_index indices to KnowledgeBaseEntry ids
            self.chunk_mappings = []  # To map chunk_index indices to parent entries
            
            # Load existing entries into indices
            self._initialize_indices()
            self.vector_initialized = True
            logger.info("✓ Vector components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector components: {e}")
            self.vector_enabled = False
        
    def _create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks from text"""
        chunks = []
        start = 0
        
        while start < len(text):
            # Get chunk with overlap
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Adjust chunk boundaries to avoid cutting words
            if end < len(text):
                # Find last space within chunk
                last_space = chunk.rfind(' ')
                if last_space != -1:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            
            # Move start position considering overlap
            start = end - self.chunk_overlap
        
        return chunks

    def _initialize_indices(self):
        """Initialize FAISS indices with existing knowledge base entries"""
        if not self.vector_enabled:
            return
            
        try:
            entries = KnowledgeBaseEntry.objects.filter(is_validated=True)
            
            if not entries:
                logger.warning("No validated entries found for indices")
                return
                
            # Prepare full entries
            full_texts = []
            self.entry_ids = []
            
            # Prepare chunks
            chunk_texts = []
            self.chunk_mappings = []
            
            for entry in entries:
                # Full entry embedding
                full_text = f"{entry.question} {entry.answer}"
                full_texts.append(full_text)
                self.entry_ids.append(entry.id)
                
                # Create and store chunks
                entry_text = f"{entry.question}\n{entry.answer}"
                chunks = self._create_chunks(entry_text)
                
                for chunk in chunks:
                    chunk_texts.append(chunk)
                    self.chunk_mappings.append({
                        'entry_id': entry.id,
                        'chunk_text': chunk
                    })
            
            # Generate and add full entry embeddings
            if full_texts:
                full_embeddings = self.embedding_model.encode(full_texts)
                self.full_index.add(self.np.array(full_embeddings).astype('float32'))
            
            # Generate and add chunk embeddings
            if chunk_texts:
                chunk_embeddings = self.embedding_model.encode(chunk_texts)
                self.chunk_index.add(self.np.array(chunk_embeddings).astype('float32'))
            
            logger.info(f"Initialized indices with {len(full_texts)} entries and {len(chunk_texts)} chunks")
            
        except Exception as e:
            logger.error(f"Error initializing indices: {str(e)}")

    def add_to_indices(self, entry: KnowledgeBaseEntry):
        """Add a new entry to both indices"""
        if not self._check_vector_support():
            return
            
        # Initialize vector components if not already done
        if not self.vector_initialized:
            self._initialize_vector_components()
            
        try:
            # Add to full entry index
            full_text = f"{entry.question} {entry.answer}"
            full_embedding = self.embedding_model.encode([full_text])[0]
            self.full_index.add(self.np.array([full_embedding]).astype('float32'))
            self.entry_ids.append(entry.id)
            
            # Create and add chunks
            entry_text = f"{entry.question}\n{entry.answer}"
            chunks = self._create_chunks(entry_text)
            
            chunk_embeddings = self.embedding_model.encode(chunks)
            self.chunk_index.add(self.np.array(chunk_embeddings).astype('float32'))
            
            for chunk in chunks:
                self.chunk_mappings.append({
                    'entry_id': entry.id,
                    'chunk_text': chunk
                })
            
            logger.info(f"Added entry {entry.id} with {len(chunks)} chunks to indices")
            
        except Exception as e:
            logger.error(f"Error adding entry to indices: {str(e)}")

    def _search_vector_similarity(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar entries using vector similarity in both full entries and chunks"""
        if not self._check_vector_support():
            return []
            
        # Initialize vector components if not already done
        if not self.vector_initialized:
            self._initialize_vector_components()
            
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            query_vector = self.np.array([query_embedding]).astype('float32')
            
            results = []
            seen_entries = set()
            
            # Search in full entries
            full_distances, full_indices = self.full_index.search(query_vector, k)
            
            for i, idx in enumerate(full_indices[0]):
                if idx < len(self.entry_ids):
                    entry_id = self.entry_ids[idx]
                    if entry_id not in seen_entries:
                        try:
                            entry = KnowledgeBaseEntry.objects.get(id=entry_id)
                            similarity_score = 1 / (1 + full_distances[0][i])
                            
                            results.append({
                                'entry': entry,
                                'strategy': 'vector_full',
                                'base_score': similarity_score,
                                'matching_keywords': []
                            })
                            seen_entries.add(entry_id)
                        except KnowledgeBaseEntry.DoesNotExist:
                            continue
            
            # Search in chunks
            chunk_distances, chunk_indices = self.chunk_index.search(query_vector, k)
            
            for i, idx in enumerate(chunk_indices[0]):
                if idx < len(self.chunk_mappings):
                    chunk_data = self.chunk_mappings[idx]
                    entry_id = chunk_data['entry_id']
                    
                    if entry_id not in seen_entries:
                        try:
                            entry = KnowledgeBaseEntry.objects.get(id=entry_id)
                            similarity_score = 1 / (1 + chunk_distances[0][i])
                            
                            results.append({
                                'entry': entry,
                                'strategy': 'vector_chunk',
                                'base_score': similarity_score,
                                'matching_keywords': [],
                                'matching_chunk': chunk_data['chunk_text']
                            })
                            seen_entries.add(entry_id)
                        except KnowledgeBaseEntry.DoesNotExist:
                            continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vector similarity search: {str(e)}")
            return []

    def _extract_program_info(self, entry: KnowledgeBaseEntry) -> Dict[str, Any]:
        """Extract structured program information from entry"""
        program_info = {
            'level': None,
            'name': None,
            'specialization': None,
            'duration': None,
            'study_mode': None,
            'core_modules': [],
            'specialized_modules': []
        }
        
        # Extract program level and name
        for level in self.program_levels.keys():
            if level.lower() in entry.question.lower():
                program_info['level'] = level
                break
        
        # Extract program name
        if 'programme' in entry.answer.lower():
            name_match = re.search(r'"([^"]+)"', entry.answer)
            if name_match:
                program_info['name'] = name_match.group(1)
        
        # Extract study mode
        if 'study mode' in entry.answer.lower():
            if 'full-time' in entry.answer.lower():
                program_info['study_mode'] = 'Full-time'
            elif 'part-time' in entry.answer.lower():
                program_info['study_mode'] = 'Part-time'
            elif 'online' in entry.answer.lower() or 'odl' in entry.answer.lower():
                program_info['study_mode'] = 'Online/ODL'
        
        # Extract modules if present
        if 'core modules' in entry.answer.lower():
            core_modules = re.findall(r'core modules:?\s*\n((?:[-*]\s*[^\n]+\n)+)', entry.answer, re.I)
            if core_modules:
                program_info['core_modules'] = [m.strip('- *') for m in core_modules[0].split('\n') if m.strip()]
        
        if 'specialized modules' in entry.answer.lower():
            spec_modules = re.findall(r'specialized modules:?\s*\n((?:[-*]\s*[^\n]+\n)+)', entry.answer, re.I)
            if spec_modules:
                program_info['specialized_modules'] = [m.strip('- *') for m in spec_modules[0].split('\n') if m.strip()]
        
        return program_info

    def _extract_accommodation_info(self, entry: KnowledgeBaseEntry) -> Dict[str, Any]:
        """Extract structured accommodation information from entry"""
        accommodation_info = {
            'location': None,
            'single_rent': None,
            'sharing_rent': None,
            'facilities': [],
            'distance': None
        }
        
        # Extract location
        location_match = re.search(r'location:\s*([^,\n]+)', entry.answer, re.I)
        if location_match:
            accommodation_info['location'] = location_match.group(1).strip()
        
        # Extract rent information
        single_rent = re.search(r'single[^:]*:\s*RM\s*([\d,]+)', entry.answer, re.I)
        if single_rent:
            accommodation_info['single_rent'] = float(single_rent.group(1).replace(',', ''))
            
        sharing_rent = re.search(r'sharing[^:]*:\s*RM\s*([\d,]+)', entry.answer, re.I)
        if sharing_rent:
            accommodation_info['sharing_rent'] = float(sharing_rent.group(1).replace(',', ''))
        
        # Extract facilities
        facilities_match = re.findall(r'facilities:?\s*\n((?:[-*]\s*[^\n]+\n)+)', entry.answer, re.I)
        if facilities_match:
            accommodation_info['facilities'] = [f.strip('- *') for f in facilities_match[0].split('\n') if f.strip()]
        
        # Extract distance
        distance_match = re.search(r'(\d+(?:\.\d+)?)\s*km from campus', entry.answer, re.I)
        if distance_match:
            accommodation_info['distance'] = float(distance_match.group(1))
            
        return accommodation_info

    def _calculate_program_relevance(self, query: str, entry: KnowledgeBaseEntry) -> float:
        """Calculate program-specific relevance score"""
        base_score = self._calculate_text_similarity(query, entry.question)
        
        # Extract program info
        program_info = self._extract_program_info(entry)
        
        # Boost score based on matching program level
        query_lower = query.lower()
        if program_info['level'] and program_info['level'].lower() in query_lower:
            base_score *= 1.2
            
        # Boost for matching specialization keywords
        if program_info['specialization'] and any(spec.lower() in query_lower for spec in program_info['specialization'].split()):
            base_score *= 1.15
            
        # Boost for matching study mode
        if program_info['study_mode'] and program_info['study_mode'].lower() in query_lower:
            base_score *= 1.1
            
        return min(base_score, 1.0)

    def _calculate_accommodation_relevance(self, query: str, entry: KnowledgeBaseEntry) -> float:
        """Calculate accommodation-specific relevance score"""
        base_score = self._calculate_text_similarity(query, entry.question)
        
        # Extract accommodation info
        accommodation_info = self._extract_accommodation_info(entry)
        
        # Boost score based on matching location
        query_lower = query.lower()
        if accommodation_info['location'] and accommodation_info['location'].lower() in query_lower:
            base_score *= 1.2
            
        # Boost for rent-related queries
        if any(term in query_lower for term in ['rent', 'price', 'cost']):
            if accommodation_info['single_rent'] or accommodation_info['sharing_rent']:
                base_score *= 1.15
                
        # Boost for facility-related queries
        if any(term in query_lower for term in ['facility', 'amenity', 'feature']):
            if accommodation_info['facilities']:
                base_score *= 1.1
                
        return min(base_score, 1.0)
    
    def retrieve_relevant_knowledge(self, query: str, categories: List[str] = None, 
                                   conversation=None, user=None) -> List[Dict[str, Any]]:
        """
        Enhanced knowledge retrieval with multiple ranking strategies including optional vector similarity
        and conversation-aware context
        """
        try:
            # Extract keywords from query
            keywords = self._extract_keywords(query)
            logger.info(f"Extracted keywords: {keywords}")
            
            # Get conversation context using memory strategies
            conversation_context = ""
            user_context = ""
            
            if conversation or user:
                try:
                    from .conversation_memory_service import ConversationMemoryService
                    
                    # Use RAG context strategy for enhanced retrieval
                    memory_service = ConversationMemoryService(default_strategy='rag_context')
                    
                    if conversation:
                        conversation_context = memory_service.get_conversation_context(
                            conversation=conversation,
                            strategy='rag_context'
                        )
                        # Add conversation context to query for better matching
                        if conversation_context:
                            enhanced_query = f"{query}\n\nConversation context: {conversation_context}"
                            additional_keywords = self._extract_keywords(conversation_context)
                            keywords.extend(additional_keywords)
                            keywords = list(dict.fromkeys(keywords))  # Remove duplicates
                    
                    if user:
                        user_context = memory_service.get_user_context(
                            user=user,
                            strategy='rag_context'
                        )
                        if user_context:
                            user_keywords = self._extract_keywords(user_context)
                            keywords.extend(user_keywords)
                            keywords = list(dict.fromkeys(keywords))  # Remove duplicates
                            
                except ImportError:
                    logger.warning("ConversationMemoryService not available")
                except Exception as e:
                    logger.error(f"Error getting conversation context: {str(e)}")
            
            # Multi-strategy search
            results = []
            
            # Strategy 1: Vector similarity search (if enabled)
            if self._check_vector_support():
                # Use enhanced query with conversation context for vector search
                search_query = query
                if conversation_context:
                    search_query = f"{query} {conversation_context}"
                vector_matches = self._search_vector_similarity(search_query)
                results.extend(vector_matches)
            
            # Strategy 2: Exact question matching
            exact_matches = self._search_exact_questions(query)
            results.extend(exact_matches)
            
            # Strategy 3: Semantic similarity
            semantic_matches = self._search_semantic_similarity(query, keywords)
            results.extend(semantic_matches)
            
            # Strategy 4: Keyword matching
            keyword_matches = self._search_keyword_matches(keywords, categories)
            results.extend(keyword_matches)
            
            # Strategy 5: Category-based search
            if categories:
                category_matches = self._search_by_category(query, categories)
                results.extend(category_matches)
            
            # Strategy 6: Context-aware search (if conversation available)
            if conversation_context:
                context_matches = self._search_context_aware(query, conversation_context, keywords)
                results.extend(context_matches)
            
            # Remove duplicates and rank results
            unique_results = self._deduplicate_results(results)
            ranked_results = self._rank_and_score_results(
                query, keywords, unique_results, 
                conversation_context=conversation_context,
                user_context=user_context
            )
            
            # Filter by confidence and limit results
            filtered_results = [
                result for result in ranked_results 
                if result['relevance_score'] >= self.min_confidence
            ][:self.max_results]
            
            logger.info(f"Retrieved {len(filtered_results)} relevant knowledge entries (conversation-aware)")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {str(e)}")
            return []
    
    def _search_exact_questions(self, query: str) -> List[Dict[str, Any]]:
        """Search for exact question matches"""
        results = []
        
        # Clean query for matching
        clean_query = self._clean_text(query)
        
        # Find questions with high similarity
        entries = KnowledgeBaseEntry.objects.filter(
            Q(question__icontains=clean_query[:50]) |
            Q(answer__icontains=clean_query[:50])
        )
        
        for entry in entries:
            similarity = SequenceMatcher(None, clean_query, self._clean_text(entry.question)).ratio()
            if similarity > 0.7:  # High similarity threshold
                results.append({
                    'entry': entry,
                    'strategy': 'exact_question',
                    'base_score': similarity,
                    'matching_keywords': []
                })
        
        return results
    
    def _search_semantic_similarity(self, query: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search based on semantic similarity"""
        results = []
        
        # Search in questions and answers
        search_conditions = Q()
        for keyword in keywords:
            search_conditions |= Q(question__icontains=keyword)
            search_conditions |= Q(answer__icontains=keyword)
        
        entries = KnowledgeBaseEntry.objects.filter(search_conditions).distinct()
        
        for entry in entries:
            # Calculate semantic similarity score
            question_similarity = self._calculate_text_similarity(query, entry.question)
            answer_similarity = self._calculate_text_similarity(query, entry.answer)
            
            # Find matching keywords
            matching_keywords = self._find_matching_keywords(keywords, entry.keywords)
            
            # Combined score
            semantic_score = max(question_similarity, answer_similarity * 0.8)
            keyword_boost = min(len(matching_keywords) * 0.1, 0.5)
            
            total_score = semantic_score + keyword_boost
            
            if total_score > 0.2:  # Minimum threshold
                results.append({
                    'entry': entry,
                    'strategy': 'semantic',
                    'base_score': total_score,
                    'matching_keywords': matching_keywords
                })
        
        return results
    
    def _search_keyword_matches(self, keywords: List[str], categories: List[str] = None) -> List[Dict[str, Any]]:
        """Search based on keyword matching"""
        results = []
        
        # Build search conditions
        search_conditions = Q()
        for keyword in keywords:
            search_conditions |= Q(keywords__icontains=keyword)
        
        # Add category filter if specified
        if categories:
            category_condition = Q()
            for category in categories:
                category_condition |= Q(category__icontains=category)
            search_conditions &= category_condition
        
        entries = KnowledgeBaseEntry.objects.filter(search_conditions).distinct()
        
        for entry in entries:
            matching_keywords = self._find_matching_keywords(keywords, entry.keywords)
            
            # Score based on keyword matches
            keyword_score = len(matching_keywords) / len(keywords) if keywords else 0
            
            if keyword_score > 0.1:  # Minimum keyword match
                results.append({
                    'entry': entry,
                    'strategy': 'keyword',
                    'base_score': keyword_score,
                    'matching_keywords': matching_keywords
                })
        
        return results
    
    def _search_by_category(self, query: str, categories: List[str]) -> List[Dict[str, Any]]:
        """Search within specific categories"""
        results = []
        
        for category in categories:
            entries = KnowledgeBaseEntry.objects.filter(category__icontains=category)
            
            for entry in entries:
                # Calculate relevance within category
                question_relevance = self._calculate_text_similarity(query, entry.question)
                answer_relevance = self._calculate_text_similarity(query, entry.answer)
                
                category_score = max(question_relevance, answer_relevance * 0.7)
                
                if category_score > 0.15:  # Category-specific threshold
                    results.append({
                        'entry': entry,
                        'strategy': 'category',
                        'base_score': category_score,
                        'matching_keywords': []
                    })
        
        return results
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entries, keeping the one with highest score"""
        seen_entries = {}
        
        for result in results:
            entry_id = result['entry'].id
            if entry_id not in seen_entries or result['base_score'] > seen_entries[entry_id]['base_score']:
                seen_entries[entry_id] = result
        
        return list(seen_entries.values())
    
    def _search_context_aware(self, query: str, conversation_context: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search using conversation context for better relevance"""
        results = []
        
        try:
            # Extract intent and topics from conversation context
            context_keywords = self._extract_keywords(conversation_context)
            
            # Combine query and context keywords
            combined_keywords = list(set(keywords + context_keywords))
            
            # Search with enhanced keyword set
            search_conditions = Q()
            for keyword in combined_keywords:
                search_conditions |= Q(question__icontains=keyword)
                search_conditions |= Q(answer__icontains=keyword)
                search_conditions |= Q(keywords__icontains=keyword)
            
            entries = KnowledgeBaseEntry.objects.filter(search_conditions).distinct()
            
            for entry in entries:
                # Calculate context relevance
                context_relevance = self._calculate_context_relevance(
                    query, conversation_context, entry
                )
                
                if context_relevance > 0.2:  # Minimum context relevance
                    results.append({
                        'entry': entry,
                        'strategy': 'context_aware',
                        'base_score': context_relevance,
                        'matching_keywords': self._find_matching_keywords(combined_keywords, entry.keywords),
                        'context_boost': True
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in context-aware search: {str(e)}")
            return []

    def _calculate_context_relevance(self, query: str, conversation_context: str, entry: KnowledgeBaseEntry) -> float:
        """Calculate relevance based on conversation context"""
        
        # Base similarity with query
        query_similarity = self._calculate_text_similarity(query, entry.question)
        
        # Context similarity
        context_similarity = self._calculate_text_similarity(conversation_context, entry.answer)
        
        # Weight the scores
        relevance_score = (query_similarity * 0.7) + (context_similarity * 0.3)
        
        # Boost for follow-up questions
        if any(word in query.lower() for word in ['also', 'what about', 'and', 'additionally']):
            relevance_score *= 1.1
        
        return min(relevance_score, 1.0)

    def _rank_and_score_results(self, query: str, keywords: List[str], results: List[Dict[str, Any]], 
                               conversation_context: str = "", user_context: str = "") -> List[Dict[str, Any]]:
        """Rank and score results using multiple factors including conversation context"""
        for result in results:
            entry = result['entry']
            base_score = result['base_score']
            
            # Category weight
            category_weight = self.category_weights.get(entry.category, 1.0)
            
            # Special handling for program and accommodation entries
            if 'program' in entry.category.lower():
                program_score = self._calculate_program_relevance(query, entry)
                base_score = max(base_score, program_score)
            elif 'accommodation' in entry.category.lower():
                accommodation_score = self._calculate_accommodation_relevance(query, entry)
                base_score = max(base_score, accommodation_score)
            
            # Strategy bonus
            strategy_bonus = {
                'vector_full': 0.3,      # Prioritize full vector matches
                'vector_chunk': 0.25,    # Chunk matches slightly lower
                'context_aware': 0.2,    # Context-aware matches
                'exact_question': 0.15,
                'semantic': 0.1,
                'keyword': 0.05,
                'category': 0.02
            }.get(result['strategy'], 0.0)
            
            # Conversation context bonus
            context_bonus = 0.0
            if conversation_context and result.get('context_boost'):
                context_bonus = 0.15
            
            # User context bonus (for personalization)
            user_bonus = 0.0
            if user_context:
                user_relevance = self._calculate_text_similarity(user_context, entry.answer)
                user_bonus = user_relevance * 0.1
            
            # Chunk relevance bonus
            if 'matching_chunk' in result:
                chunk_similarity = self._calculate_text_similarity(query, result['matching_chunk'])
                base_score = max(base_score, chunk_similarity)
            
            # Confidence score from entry
            confidence_boost = entry.confidence_score * 0.1
            
            # Recent entries bonus (newer training data)
            recency_bonus = 0.05 if entry.is_validated else 0.0
            
            # Calculate final relevance score
            relevance_score = (
                base_score * category_weight + 
                confidence_boost + 
                strategy_bonus + 
                context_bonus +
                user_bonus +
                recency_bonus
            )
            
            # Ensure score doesn't exceed 1.0
            result['relevance_score'] = min(relevance_score, 1.0)
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple word-based similarity
        words1 = set(self._extract_keywords(text1))
        words2 = set(self._extract_keywords(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Extract words (3+ characters)
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Filter out stop words
        stop_words = {
            'the', 'is', 'are', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'a', 'an', 'this', 'that', 'these', 'those', 'what', 'how', 'why', 'when', 'where', 'who', 'which',
            'can', 'could', 'should', 'would', 'will', 'shall', 'may', 'might', 'must', 'have', 'has', 'had',
            'do', 'does', 'did', 'be', 'been', 'being', 'was', 'were', 'get', 'got', 'tell', 'know', 'about'
        }
        
        keywords = [word for word in words if word not in stop_words]
        
        # Return unique keywords
        return list(dict.fromkeys(keywords))
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters (keep alphanumeric and spaces)
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        return text
    
    def _find_matching_keywords(self, query_keywords: List[str], entry_keywords: List[str]) -> List[str]:
        """Find keywords that match between query and entry"""
        if not query_keywords or not entry_keywords:
            return []
        
        # Convert to lowercase for comparison
        query_set = set(word.lower() for word in query_keywords)
        entry_set = set(word.lower() for word in entry_keywords)
        
        # Find exact matches
        matches = query_set.intersection(entry_set)
        
        # Find partial matches (substring matching)
        partial_matches = set()
        for query_word in query_keywords:
            for entry_word in entry_keywords:
                if query_word.lower() in entry_word.lower() or entry_word.lower() in query_word.lower():
                    partial_matches.add(query_word.lower())
        
        # Combine exact and partial matches
        all_matches = matches.union(partial_matches)
        
        return list(all_matches)
    
    def get_context_for_prompt(self, query: str, categories: List[str] = None, 
                              max_context_length: int = 2000, conversation=None, 
                              user=None) -> str:
        """Get formatted context string for the chatbot prompt with conversation awareness"""
        
        # Get conversation-aware knowledge entries
        knowledge_entries = self.retrieve_relevant_knowledge(
            query, categories, conversation=conversation, user=user
        )
        
        if not knowledge_entries:
            return ""
        
        context_parts = ["Here is relevant information from APU's comprehensive knowledge base:"]
        current_length = len(context_parts[0])
        
        # Add conversation context if available
        if conversation:
            try:
                from .conversation_memory_service import conversation_memory_service
                conv_context = conversation_memory_service.get_conversation_context(conversation, max_messages=5)
                if conv_context:
                    context_parts.append(f"\nConversation context:\n{conv_context}")
                    current_length += len(context_parts[-1])
            except Exception as e:
                logger.error(f"Error adding conversation context: {str(e)}")
        
        # Add knowledge entries
        for i, entry in enumerate(knowledge_entries, 1):
            kb_entry = entry['entry']
            score = entry['relevance_score']
            strategy = entry['strategy']
            
            entry_text = (
                f"\n{i}. Q: {kb_entry.question}\n"
                f"   A: {kb_entry.answer}\n"
                f"   Category: {kb_entry.category} (Relevance: {score:.2f}, Strategy: {strategy})"
            )
            
            # Check if adding this entry would exceed max context length
            if current_length + len(entry_text) > max_context_length:
                break
            
            context_parts.append(entry_text)
            current_length += len(entry_text)
        
        context_parts.append("\nPlease use this comprehensive information along with the conversation context to provide accurate, detailed, and contextually relevant responses about APU. Consider the conversation history when formulating your response.")
        
        return "\n".join(context_parts)
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        total_entries = KnowledgeBaseEntry.objects.count()
        categories = KnowledgeBaseEntry.objects.values_list('category', flat=True).distinct()
        
        category_counts = {}
        for category in categories:
            category_counts[category] = KnowledgeBaseEntry.objects.filter(category=category).count()
        
        return {
            'total_entries': total_entries,
            'categories': list(categories),
            'category_counts': category_counts,
            'enhanced_features': [
                'Multi-strategy search',
                'Semantic similarity matching',
                'Category-weighted ranking',
                'Comprehensive training data integration'
            ]
        }


# Create enhanced RAG service instance
enhanced_rag_service = EnhancedRAGService(max_results=8, min_confidence=0.3) 