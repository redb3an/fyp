import logging
from typing import List, Dict, Any, Optional
from django.db.models import Q
from chatbot.models import KnowledgeBaseEntry, TrainingDataset
import re
from collections import Counter

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval Augmented Generation service for enhancing chatbot responses
    with relevant knowledge from the database
    """
    
    def __init__(self, max_results: int = 5, min_confidence: float = 0.3):
        self.max_results = max_results
        self.min_confidence = min_confidence
    
    def retrieve_relevant_knowledge(self, query: str, categories: List[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge entries based on the user query
        
        Args:
            query: User's question or message
            categories: Optional list of categories to filter by
            
        Returns:
            List of relevant knowledge entries with metadata
        """
        try:
            # Extract keywords from the query
            keywords = self._extract_keywords(query)
            logger.info(f"Extracted keywords from query: {keywords}")
            
            # Search for relevant entries
            relevant_entries = self._search_knowledge_base(keywords, categories)
            
            # Score and rank the results
            scored_results = self._score_and_rank_results(query, keywords, relevant_entries)
            
            # Filter by minimum confidence and limit results
            filtered_results = [
                result for result in scored_results 
                if result['relevance_score'] >= self.min_confidence
            ][:self.max_results]
            
            logger.info(f"Retrieved {len(filtered_results)} relevant knowledge entries")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {str(e)}")
            return []
    
    def get_context_for_prompt(self, query: str, categories: List[str] = None) -> str:
        """
        Get formatted context string to include in the chatbot prompt
        
        Args:
            query: User's question or message
            categories: Optional list of categories to filter by
            
        Returns:
            Formatted context string for the prompt
        """
        knowledge_entries = self.retrieve_relevant_knowledge(query, categories)
        
        if not knowledge_entries:
            return ""
        
        context_parts = ["Here is relevant information from APU's knowledge base:"]
        
        for i, entry in enumerate(knowledge_entries, 1):
            kb_entry = entry['entry']
            score = entry['relevance_score']
            
            context_parts.append(
                f"\n{i}. {kb_entry.question}\n"
                f"   Answer: {kb_entry.answer}\n"
                f"   Category: {kb_entry.category}\n"
                f"   (Relevance: {score:.2f})"
            )
        
        context_parts.append("\nPlease use this information to provide accurate and helpful responses about APU.")
        
        return "\n".join(context_parts)
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords from the user query"""
        # Convert to lowercase and remove punctuation
        clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
        
        # Split into words and filter out common stop words
        stop_words = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
            'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
            'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
            'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
            'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
            'just', 'don', 'should', 'now', 'tell', 'about', 'please', 'help'
        }
        
        words = [word for word in clean_query.split() if len(word) > 2 and word not in stop_words]
        
        # Add some academic-specific keywords if present
        academic_keywords = []
        if any(word in query.lower() for word in ['program', 'programme', 'course', 'degree']):
            academic_keywords.extend(['program', 'programme', 'course', 'degree'])
        if any(word in query.lower() for word in ['faculty', 'school', 'department']):
            academic_keywords.extend(['faculty', 'school'])
        if any(word in query.lower() for word in ['admission', 'apply', 'application']):
            academic_keywords.extend(['admission', 'application'])
        
        return list(set(words + academic_keywords))
    
    def _search_knowledge_base(self, keywords: List[str], categories: List[str] = None) -> List[KnowledgeBaseEntry]:
        """Search the knowledge base using keywords and categories"""
        
        # Start with validated entries from active datasets
        queryset = KnowledgeBaseEntry.objects.filter(
            dataset__status='active',
            is_validated=True
        ).select_related('dataset')
        
        # Filter by categories if provided
        if categories:
            queryset = queryset.filter(category__in=categories)
        
        # Build search query
        search_q = Q()
        
        for keyword in keywords:
            # Search in question, answer, and keywords fields
            keyword_q = (
                Q(question__icontains=keyword) |
                Q(answer__icontains=keyword) |
                Q(keywords__icontains=keyword) |
                Q(category__icontains=keyword)
            )
            search_q |= keyword_q
        
        # Execute search
        results = queryset.filter(search_q).distinct()
        
        return list(results)
    
    def _score_and_rank_results(self, query: str, keywords: List[str], entries: List[KnowledgeBaseEntry]) -> List[Dict[str, Any]]:
        """Score and rank knowledge entries based on relevance"""
        
        scored_results = []
        
        for entry in entries:
            score = self._calculate_relevance_score(query, keywords, entry)
            
            scored_results.append({
                'entry': entry,
                'relevance_score': score,
                'matching_keywords': self._get_matching_keywords(keywords, entry)
            })
        
        # Sort by relevance score (descending)
        scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return scored_results
    
    def _calculate_relevance_score(self, query: str, keywords: List[str], entry: KnowledgeBaseEntry) -> float:
        """Calculate relevance score for a knowledge entry"""
        
        score = 0.0
        
        # Base confidence score from the entry
        score += entry.confidence_score * 0.2
        
        # Keyword matching in different fields (weighted)
        entry_text = f"{entry.question} {entry.answer} {entry.category}".lower()
        entry_keywords = [kw.lower() for kw in entry.keywords] if entry.keywords else []
        
        # Count keyword matches
        keyword_matches = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Question title match (highest weight)
            if keyword_lower in entry.question.lower():
                score += 0.3
                keyword_matches += 1
            
            # Answer content match
            if keyword_lower in entry.answer.lower():
                score += 0.2
                keyword_matches += 1
            
            # Category match
            if keyword_lower in entry.category.lower():
                score += 0.15
                keyword_matches += 1
            
            # Keywords list match
            if keyword_lower in entry_keywords:
                score += 0.25
                keyword_matches += 1
        
        # Bonus for multiple keyword matches
        if keyword_matches > 1:
            score += 0.1 * (keyword_matches - 1)
        
        # Exact phrase matching bonus
        query_lower = query.lower()
        if any(phrase in entry_text for phrase in [query_lower[:20], query_lower[-20:]]):
            score += 0.15
        
        # Normalize score to 0-1 range
        return min(score, 1.0)
    
    def _get_matching_keywords(self, keywords: List[str], entry: KnowledgeBaseEntry) -> List[str]:
        """Get list of keywords that match the entry"""
        
        matching = []
        entry_text = f"{entry.question} {entry.answer} {entry.category}".lower()
        entry_keywords = [kw.lower() for kw in entry.keywords] if entry.keywords else []
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if (keyword_lower in entry_text or keyword_lower in entry_keywords):
                matching.append(keyword)
        
        return matching
    
    def get_category_suggestions(self, query: str) -> List[str]:
        """Get suggested categories based on the query"""
        
        keywords = self._extract_keywords(query)
        
        # Get categories that match the keywords
        category_counts = Counter()
        
        entries = KnowledgeBaseEntry.objects.filter(
            dataset__status='active',
            is_validated=True
        ).values_list('category', flat=True)
        
        for category in entries:
            category_lower = category.lower()
            for keyword in keywords:
                if keyword.lower() in category_lower:
                    category_counts[category] += 1
        
        # Return top 3 matching categories
        return [cat for cat, count in category_counts.most_common(3)]
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        
        active_datasets = TrainingDataset.objects.filter(status='active').count()
        total_entries = KnowledgeBaseEntry.objects.filter(dataset__status='active').count()
        validated_entries = KnowledgeBaseEntry.objects.filter(
            dataset__status='active', 
            is_validated=True
        ).count()
        
        categories = KnowledgeBaseEntry.objects.filter(
            dataset__status='active'
        ).values_list('category', flat=True).distinct()
        
        return {
            'active_datasets': active_datasets,
            'total_entries': total_entries,
            'validated_entries': validated_entries,
            'categories': list(categories),
            'validation_rate': validated_entries / total_entries if total_entries > 0 else 0
        } 