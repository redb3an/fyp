import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from django.contrib.auth.models import User

from ..models import (
    Conversation, Message, ConversationMemory, 
    KnowledgeBaseEntry, TrainingDataset, ProgramRecommendation
)

logger = logging.getLogger(__name__)


class ConversationMemoryManager:
    """
    Manager class for strategic memory operations based on memory strategy selection.
    
    This class provides the core implementation for the three memory strategies:
    1. SHORT_TERM: Recent conversation context (5-10 messages)
    2. CROSS_LEARNING: Knowledge base updates from interactions
    3. RAG_CONTEXT: Context-aware retrieval augmentation
    """
    
    def __init__(self, strategy: str = 'hybrid'):
        """
        Initialize the memory manager with a specific strategy.
        
        Args:
            strategy: Memory strategy to use ('short_term', 'cross_learning', 'rag_context', 'hybrid')
        """
        self.strategy = strategy
        self.strategy_config = self._get_strategy_config()
        
    def _get_strategy_config(self) -> Dict[str, Any]:
        """Get configuration for the current memory strategy"""
        configs = {
            'short_term': {
                'retention_days': 1,
                'max_messages': 10,
                'memory_types': ['context'],
                'priority_levels': ['low', 'medium'],
                'auto_expire': True
            },
            'cross_learning': {
                'retention_days': 180,
                'max_messages': 5,
                'memory_types': ['correction', 'feedback', 'insight'],
                'priority_levels': ['high', 'critical'],
                'auto_expire': False
            },
            'rag_context': {
                'retention_days': 7,
                'max_messages': 15,
                'memory_types': ['intent', 'preference', 'topic', 'context'],
                'priority_levels': ['medium', 'high'],
                'auto_expire': True
            },
            'hybrid': {
                'retention_days': 30,
                'max_messages': 12,
                'memory_types': ['context', 'intent', 'preference', 'topic', 'feedback', 'correction', 'insight'],
                'priority_levels': ['low', 'medium', 'high', 'critical'],
                'auto_expire': True
            }
        }
        return configs.get(self.strategy, configs['hybrid'])
    
    def create_memory(self, conversation: Conversation, user: User, memory_type: str, 
                     content: str, context: Dict[str, Any] = None, 
                     priority: str = 'medium', confidence: float = 0.7, 
                     relevance: float = 0.5) -> ConversationMemory:
        """
        Create a new memory with the current strategy configuration.
        
        Args:
            conversation: The conversation this memory belongs to
            user: The user this memory belongs to
            memory_type: Type of memory ('context', 'intent', etc.)
            content: The actual memory content
            context: Additional context data
            priority: Priority level
            confidence: Confidence score (0.0-1.0)
            relevance: Relevance score (0.0-1.0)
            
        Returns:
            ConversationMemory: The created memory instance
        """
        # Only create memory if the type is supported by current strategy
        if memory_type not in self.strategy_config['memory_types']:
            logger.debug(f"Memory type {memory_type} not supported by {self.strategy} strategy")
            return None
        
        # Calculate expiry based on strategy
        expires_at = None
        if self.strategy_config['auto_expire']:
            expires_at = timezone.now() + timedelta(days=self.strategy_config['retention_days'])
        
        # Create memory with strategy-specific configuration
        memory = ConversationMemory.objects.create(
            conversation=conversation,
            user=user,
            memory_strategy=self.strategy,
            memory_type=memory_type,
            content=content,
            context=context or {},
            priority=priority,
            confidence_score=confidence,
            relevance_score=relevance,
            expires_at=expires_at,
            rag_weight=self.strategy_config.get('rag_weight', 1.0)
        )
        
        logger.info(f"Created {memory_type} memory with {self.strategy} strategy: {content[:50]}...")
        return memory
    
    def get_short_term_context(self, conversation: Conversation) -> List[Dict[str, Any]]:
        """
        Get short-term conversation context (Strategy 1: SHORT_TERM)
        
        Args:
            conversation: The conversation to get context for
            
        Returns:
            List of recent messages with metadata
        """
        if self.strategy not in ['short_term', 'hybrid']:
            return []
        
        # Get recent messages directly from the conversation
        recent_messages = conversation.messages.order_by('-created_at')[:self.strategy_config['max_messages']]
        
        context_messages = []
        for msg in reversed(recent_messages):
            context_messages.append({
                'content': msg.content,
                'sender': msg.sender,
                'timestamp': msg.created_at.isoformat(),
                'message_id': str(msg.id)
            })
        
        # Also get stored short-term memories
        short_term_memories = ConversationMemory.get_short_term_context(conversation)
        
        # Combine and deduplicate
        all_messages = context_messages + short_term_memories
        seen_ids = set()
        unique_messages = []
        
        for msg in all_messages:
            msg_id = msg.get('message_id')
            if msg_id and msg_id not in seen_ids:
                seen_ids.add(msg_id)
                unique_messages.append(msg)
        
        return unique_messages[:self.strategy_config['max_messages']]
    
    def process_cross_learning(self, user: User = None) -> Dict[str, int]:
        """
        Process cross-conversation learning (Strategy 2: CROSS_LEARNING)
        
        Args:
            user: Optional user filter
            
        Returns:
            Dict with processing results
        """
        if self.strategy not in ['cross_learning', 'hybrid']:
            return {'message': 'Cross-learning not enabled for this strategy'}
        
        results = {
            'corrections_processed': 0,
            'feedback_processed': 0,
            'insights_generated': 0,
            'kb_entries_created': 0
        }
        
        # Get memories that should influence knowledge base
        learning_memories = ConversationMemory.get_cross_learning_insights(user)
        
        for memory in learning_memories:
            try:
                if memory.memory_type == 'correction':
                    if self._process_correction_memory(memory):
                        results['corrections_processed'] += 1
                
                elif memory.memory_type == 'feedback':
                    if self._process_feedback_memory(memory):
                        results['feedback_processed'] += 1
                
                elif memory.memory_type == 'insight':
                    if self._process_insight_memory(memory):
                        results['insights_generated'] += 1
                
                # Mark as processed
                memory.has_influenced_kb = True
                memory.save()
                
            except Exception as e:
                logger.error(f"Error processing {memory.memory_type} memory: {str(e)}")
        
        return results
    
    def get_rag_context(self, conversation: Conversation, user: User = None) -> str:
        """
        Get context for RAG enhancement (Strategy 3: RAG_CONTEXT)
        
        Args:
            conversation: Current conversation
            user: User for cross-conversation context
            
        Returns:
            Formatted context string for RAG
        """
        if self.strategy not in ['rag_context', 'hybrid']:
            return ""
        
        # Get RAG-optimized memories
        rag_memories = ConversationMemory.get_rag_context_memories(conversation, user)
        
        if not rag_memories:
            return ""
        
        context_parts = ["Enhanced conversation context for RAG:"]
        
        # Group memories by type for better organization
        memory_groups = {}
        for memory in rag_memories:
            if memory.memory_type not in memory_groups:
                memory_groups[memory.memory_type] = []
            memory_groups[memory.memory_type].append(memory)
        
        # Format each group
        for memory_type, memories in memory_groups.items():
            if memories:
                context_parts.append(f"\n{memory_type.title()} Context:")
                for memory in memories[:3]:  # Limit per type
                    weight_indicator = "🔥" if memory.rag_weight > 0.8 else "⭐" if memory.rag_weight > 0.6 else "•"
                    context_parts.append(f"{weight_indicator} {memory.content}")
        
        return "\n".join(context_parts)
    
    def _process_correction_memory(self, memory: ConversationMemory) -> bool:
        """Process a correction memory for knowledge base updates"""
        try:
            # Extract what was corrected
            correction_context = memory.context
            
            # This is where you would implement logic to:
            # 1. Identify the incorrect information
            # 2. Find related KB entries
            # 3. Flag them for review or update
            
            # For now, log the correction for manual review
            logger.info(f"Correction flagged for KB review: {memory.content}")
            
            return True
        except Exception as e:
            logger.error(f"Error processing correction memory: {str(e)}")
            return False
    
    def _process_feedback_memory(self, memory: ConversationMemory) -> bool:
        """Process feedback memory for response improvements"""
        try:
            feedback_context = memory.context
            sentiment = feedback_context.get('sentiment', 0)
            
            # Process negative feedback
            if sentiment < 0:
                logger.warning(f"Negative feedback recorded: {memory.content}")
                # This could trigger response quality analysis
            
            return True
        except Exception as e:
            logger.error(f"Error processing feedback memory: {str(e)}")
            return False
    
    def _process_insight_memory(self, memory: ConversationMemory) -> bool:
        """Process insight memory for pattern recognition"""
        try:
            # This is where you would implement insight processing
            # For example, identifying common user patterns or preferences
            
            logger.info(f"Insight processed: {memory.content}")
            return True
        except Exception as e:
            logger.error(f"Error processing insight memory: {str(e)}")
            return False


class ConversationMemoryService:
    """
    Enhanced conversation memory service with strategic memory management.
    
    This service orchestrates the three memory strategies:
    1. SHORT_TERM: Remembers recent message context (5-10 messages)
    2. CROSS_LEARNING: Updates knowledge base from user interactions  
    3. RAG_CONTEXT: Uses conversation history in retrieval-augmented generation
    """
    
    def __init__(self, default_strategy: str = 'hybrid'):
        """
        Initialize the conversation memory service.
        
        Args:
            default_strategy: Default memory strategy to use
        """
        self.default_strategy = default_strategy
        self.memory_manager = ConversationMemoryManager(default_strategy)
        
        # Memory retention periods (in days) - Enhanced with strategy awareness
        self.memory_retention = {
            'context': 1,      # Short-term context
            'intent': 7,       # User intent tracking
            'preference': 30,  # User preferences
            'topic': 3,        # Discussion topics
            'feedback': 90,    # User feedback
            'correction': 180, # User corrections (important for learning)
            'insight': 365,    # Extracted insights
        }
        
        # Keywords that indicate different types of memory
        self.memory_indicators = {
            'intent': ['want', 'need', 'looking for', 'interested in', 'plan to', 'hoping to'],
            'preference': ['prefer', 'like', 'dislike', 'favorite', 'best', 'better'],
            'feedback': ['good', 'bad', 'helpful', 'not helpful', 'wrong', 'correct', 'thanks'],
            'correction': ['actually', 'no', 'wrong', 'incorrect', 'meant', 'should be'],
            'topic': ['about', 'regarding', 'concerning', 'question about'],
        }
    
    def set_strategy(self, strategy: str):
        """
        Change the memory strategy dynamically.
        
        Args:
            strategy: New memory strategy ('short_term', 'cross_learning', 'rag_context', 'hybrid')
        """
        self.memory_manager = ConversationMemoryManager(strategy)
        logger.info(f"Memory strategy changed to: {strategy}")
    
    def extract_memory_from_message(self, message: Message, conversation: Conversation, 
                                  strategy: str = None) -> List[ConversationMemory]:
        """
        Extract different types of memory from a user message using specified strategy.
        
        Args:
            message: The message to extract memory from
            conversation: The conversation context
            strategy: Optional strategy override
            
        Returns:
            List of extracted memories
        """
        if strategy:
            manager = ConversationMemoryManager(strategy)
        else:
            manager = self.memory_manager
        
        memories = []
        content = message.content.lower()
        
        try:
            # Store recent messages for short-term strategy
            if manager.strategy in ['short_term', 'hybrid']:
                context_memory = self._extract_context_with_strategy(message, conversation, manager)
                if context_memory:
                    memories.append(context_memory)
            
            # Extract intent for RAG context strategy
            if manager.strategy in ['rag_context', 'hybrid']:
                intent_memory = self._extract_intent_with_strategy(message, conversation, manager)
                if intent_memory:
                    memories.append(intent_memory)
            
            # Extract preferences for RAG context strategy
            if manager.strategy in ['rag_context', 'hybrid']:
                preference_memory = self._extract_preferences_with_strategy(message, conversation, manager)
                if preference_memory:
                    memories.append(preference_memory)
            
            # Extract feedback for cross-learning strategy
            if manager.strategy in ['cross_learning', 'hybrid']:
                feedback_memory = self._extract_feedback_with_strategy(message, conversation, manager)
                if feedback_memory:
                    memories.append(feedback_memory)
            
            # Extract corrections for cross-learning strategy
            if manager.strategy in ['cross_learning', 'hybrid']:
                correction_memory = self._extract_corrections_with_strategy(message, conversation, manager)
                if correction_memory:
                    memories.append(correction_memory)
            
            # Extract topics for RAG context strategy
            if manager.strategy in ['rag_context', 'hybrid']:
                topic_memory = self._extract_topics_with_strategy(message, conversation, manager)
                if topic_memory:
                    memories.append(topic_memory)
            
            # Update recent messages for short-term memories
            for memory in memories:
                if memory.memory_strategy in ['short_term', 'hybrid']:
                    recent_messages = self._get_recent_messages(conversation, 10)
                    memory.update_recent_messages(recent_messages)
            
            logger.info(f"Extracted {len(memories)} memories using {manager.strategy} strategy")
            return memories
            
        except Exception as e:
            logger.error(f"Error extracting memory from message: {str(e)}")
            return []
    
    def _get_recent_messages(self, conversation: Conversation, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from conversation"""
        messages = conversation.messages.order_by('-created_at')[:count]
        return [
            {
                'content': msg.content,
                'sender': msg.sender,
                'timestamp': msg.created_at.isoformat(),
                'message_id': str(msg.id)
            }
            for msg in reversed(messages)
        ]
    
    def _extract_context_with_strategy(self, message: Message, conversation: Conversation, 
                                     manager: ConversationMemoryManager) -> Optional[ConversationMemory]:
        """Extract context memory using strategy-specific logic"""
        return manager.create_memory(
            conversation=conversation,
            user=conversation.user,
            memory_type='context',
            content=message.content,
            context={
                'message_id': str(message.id),
                'sender': message.sender,
                'timestamp': message.created_at.isoformat()
            },
            priority='low',
            confidence=0.5,
            relevance=0.3
        )
    
    def _extract_intent_with_strategy(self, message: Message, conversation: Conversation, 
                                    manager: ConversationMemoryManager) -> Optional[ConversationMemory]:
        """Extract intent memory using strategy-specific logic"""
        content = message.content.lower()
        
        # Look for intent indicators
        for indicator in self.memory_indicators['intent']:
            if indicator in content:
                # Extract the text after the indicator
                pattern = rf"{indicator}\s+(.+?)(?:\.|$|,|\?)"
                match = re.search(pattern, content)
                if match:
                    intent_text = match.group(1).strip()
                    
                    return manager.create_memory(
                        conversation=conversation,
                        user=conversation.user,
                        memory_type='intent',
                        content=f"User {indicator} {intent_text}",
                        context={
                            'original_message': message.content,
                            'indicator': indicator,
                            'extracted_intent': intent_text
                        },
                        priority='high',
                        confidence=0.8,
                        relevance=0.9
                    )
        return None
    
    def _extract_preferences_with_strategy(self, message: Message, conversation: Conversation, 
                                         manager: ConversationMemoryManager) -> Optional[ConversationMemory]:
        """Extract preferences memory using strategy-specific logic"""
        content = message.content.lower()
        
        for indicator in self.memory_indicators['preference']:
            if indicator in content:
                # Extract preference context
                pattern = rf"(.*?{indicator}\s+.+?)(?:\.|$|,|\?)"
                match = re.search(pattern, content)
                if match:
                    preference_text = match.group(1).strip()
                    
                    return manager.create_memory(
                        conversation=conversation,
                        user=conversation.user,
                        memory_type='preference',
                        content=preference_text,
                        context={
                            'original_message': message.content,
                            'indicator': indicator,
                            'preference_type': self._classify_preference(preference_text)
                        },
                        priority='medium',
                        confidence=0.7,
                        relevance=0.8
                    )
        return None
    
    def _extract_feedback_with_strategy(self, message: Message, conversation: Conversation, 
                                      manager: ConversationMemoryManager) -> Optional[ConversationMemory]:
        """Extract feedback memory using strategy-specific logic"""
        content = message.content.lower()
        
        # Look for feedback indicators
        feedback_patterns = [
            r'(that was|this is|it\'s)\s+(good|bad|helpful|not helpful|wrong|correct)',
            r'(thanks|thank you|helpful|not helpful)',
            r'(wrong|incorrect|right|correct)',
        ]
        
        for pattern in feedback_patterns:
            match = re.search(pattern, content)
            if match:
                feedback_text = match.group(0)
                sentiment = self._analyze_feedback_sentiment(feedback_text)
                
                return manager.create_memory(
                    conversation=conversation,
                    user=conversation.user,
                    memory_type='feedback',
                    content=f"User feedback: {feedback_text}",
                    context={
                        'original_message': message.content,
                        'sentiment': sentiment,
                        'feedback_type': 'positive' if sentiment > 0 else 'negative'
                    },
                    priority='high' if sentiment < 0 else 'medium',
                    confidence=0.8,
                    relevance=0.7
                )
        return None
    
    def _extract_corrections_with_strategy(self, message: Message, conversation: Conversation, 
                                         manager: ConversationMemoryManager) -> Optional[ConversationMemory]:
        """Extract corrections memory using strategy-specific logic"""
        content = message.content.lower()
        
        for indicator in self.memory_indicators['correction']:
            if indicator in content:
                return manager.create_memory(
                    conversation=conversation,
                    user=conversation.user,
                    memory_type='correction',
                    content=f"User correction: {message.content}",
                    context={
                        'original_message': message.content,
                        'correction_indicator': indicator,
                        'needs_kb_update': True
                    },
                    priority='critical',
                    confidence=0.9,
                    relevance=1.0
                )
        return None
    
    def _extract_topics_with_strategy(self, message: Message, conversation: Conversation, 
                                    manager: ConversationMemoryManager) -> Optional[ConversationMemory]:
        """Extract topics memory using strategy-specific logic"""
        content = message.content.lower()
        
        # Extract key topics/subjects being discussed
        topics = []
        
        # Look for APU-specific topics
        apu_topics = [
            'programs?', 'courses?', 'fees?', 'admission', 'requirements?',
            'accommodation', 'facilities', 'campus', 'scholarships?',
            'engineering', 'business', 'computing', 'it', 'finance'
        ]
        
        for topic_pattern in apu_topics:
            if re.search(rf'\b{topic_pattern}\b', content):
                topics.append(topic_pattern.rstrip('?'))
        
        if topics:
            return manager.create_memory(
                conversation=conversation,
                user=conversation.user,
                memory_type='topic',
                content=f"Discussion topics: {', '.join(topics)}",
                context={
                    'original_message': message.content,
                    'topics': topics,
                    'topic_count': len(topics)
                },
                priority='low',
                confidence=0.6,
                relevance=0.5
            )
        return None
    
    def get_conversation_context(self, conversation: Conversation, max_messages: int = 10, 
                                strategy: str = None) -> str:
        """
        Get formatted conversation context for RAG enhancement using memory strategy
        
        Args:
            conversation: The conversation to get context for
            max_messages: Maximum number of messages to include
            strategy: Optional strategy override
            
        Returns:
            Formatted context string
        """
        try:
            # Use specified strategy or default
            if strategy:
                manager = ConversationMemoryManager(strategy)
            else:
                manager = self.memory_manager
            
            context_parts = []
            
            # Get short-term context if strategy supports it
            if manager.strategy in ['short_term', 'rag_context', 'hybrid']:
                recent_context = manager.get_short_term_context(conversation)
                if recent_context:
                    context_parts.append("Recent conversation context:")
                    for msg in recent_context[-max_messages:]:
                        context_parts.append(f"{msg['sender']}: {msg['content']}")
            
            # Get RAG context if strategy supports it
            if manager.strategy in ['rag_context', 'hybrid']:
                rag_context = manager.get_rag_context(conversation)
                if rag_context:
                    context_parts.append(f"\n{rag_context}")
            
            # Add high-priority memories for all strategies
            memories = ConversationMemory.get_active_memories(
                conversation=conversation,
                strategy=manager.strategy if manager.strategy != 'hybrid' else None
            )
            high_priority_memories = memories.filter(priority__in=['high', 'critical'])[:5]
            if high_priority_memories:
                context_parts.append("\nImportant context from this conversation:")
                for memory in high_priority_memories:
                    context_parts.append(f"- {memory.content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            return ""
    
    def get_user_context(self, user: User, max_memories: int = 20, strategy: str = None) -> str:
        """
        Get user context from across all conversations using memory strategy
        
        Args:
            user: The user to get context for
            max_memories: Maximum number of memories to include
            strategy: Optional strategy override
            
        Returns:
            Formatted user context string
        """
        try:
            # Use specified strategy or default
            if strategy:
                manager = ConversationMemoryManager(strategy)
            else:
                manager = self.memory_manager
            
            # Get user's important memories across all conversations
            user_memories = ConversationMemory.get_active_memories(
                user=user,
                strategy=manager.strategy if manager.strategy != 'hybrid' else None
            ).filter(
                priority__in=['high', 'critical']
            )[:max_memories]
            
            if not user_memories:
                return ""
            
            context_parts = [f"User context from previous conversations ({manager.strategy} strategy):"]
            
            # Group memories by type
            memory_groups = {}
            for memory in user_memories:
                if memory.memory_type not in memory_groups:
                    memory_groups[memory.memory_type] = []
                memory_groups[memory.memory_type].append(memory)
            
            # Format by type based on strategy
            strategy_config = manager._get_strategy_config()
            relevant_types = strategy_config.get('memory_types', ['intent', 'preference', 'correction'])
            
            for memory_type, memories in memory_groups.items():
                if memory_type in relevant_types:
                    context_parts.append(f"\n{memory_type.title()}s:")
                    for memory in memories[:3]:  # Limit per type
                        weight_indicator = "🔥" if memory.rag_weight > 0.8 else "⭐" if memory.rag_weight > 0.6 else "•"
                        context_parts.append(f"{weight_indicator} {memory.content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return ""
    
    def process_cross_conversation_learning(self, user: User = None, strategy: str = None) -> Dict[str, int]:
        """
        Process corrections and feedback to update knowledge base using memory strategy
        
        Args:
            user: Optional user filter
            strategy: Optional strategy override
            
        Returns:
            Dict with processing results
        """
        # Use specified strategy or default
        if strategy:
            manager = ConversationMemoryManager(strategy)
        else:
            manager = self.memory_manager
        
        # Delegate to the memory manager's cross-learning processing
        return manager.process_cross_learning(user)
    
    def _process_correction(self, correction: ConversationMemory) -> bool:
        """Process a user correction to potentially update KB"""
        try:
            # Mark as processed
            correction.has_influenced_kb = True
            correction.save()
            
            # Here you could implement logic to:
            # 1. Identify what was corrected
            # 2. Find related KB entries
            # 3. Update or flag them for review
            
            logger.info(f"Processed correction: {correction.content[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error processing correction: {str(e)}")
            return False
    
    def _process_negative_feedback(self, feedback: ConversationMemory) -> bool:
        """Process negative feedback to improve responses"""
        try:
            # Mark as processed
            feedback.has_influenced_kb = True
            feedback.save()
            
            # Log for analysis
            logger.info(f"Processed negative feedback: {feedback.content[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error processing negative feedback: {str(e)}")
            return False
    
    def _generate_insights_from_patterns(self) -> int:
        """Generate insights from conversation patterns"""
        try:
            # Find common topics users ask about
            topic_memories = ConversationMemory.objects.filter(
                memory_type='topic',
                is_active=True,
                created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            # Analyze patterns and create insights
            # This is a simplified version - you could implement more sophisticated analysis
            
            return 0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return 0
    
    def _classify_preference(self, preference_text: str) -> str:
        """Classify the type of preference"""
        text = preference_text.lower()
        
        if any(word in text for word in ['program', 'course', 'study']):
            return 'academic'
        elif any(word in text for word in ['time', 'schedule', 'mode']):
            return 'schedule'
        elif any(word in text for word in ['location', 'campus', 'distance']):
            return 'location'
        elif any(word in text for word in ['fee', 'cost', 'price', 'budget']):
            return 'financial'
        else:
            return 'general'
    
    def _analyze_feedback_sentiment(self, feedback_text: str) -> float:
        """Simple sentiment analysis for feedback"""
        positive_words = ['good', 'great', 'helpful', 'thanks', 'correct', 'right', 'perfect']
        negative_words = ['bad', 'wrong', 'incorrect', 'not helpful', 'useless', 'terrible']
        
        text = feedback_text.lower()
        
        positive_score = sum(1 for word in positive_words if word in text)
        negative_score = sum(1 for word in negative_words if word in text)
        
        if positive_score > negative_score:
            return 1.0
        elif negative_score > positive_score:
            return -1.0
        else:
            return 0.0
    
    def cleanup_expired_memories(self) -> Dict[str, int]:
        """Clean up expired memories"""
        try:
            expired_count = ConversationMemory.cleanup_expired()
            
            return {
                'expired_memories_deactivated': expired_count
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up memories: {str(e)}")
            return {'expired_memories_deactivated': 0}
    
    def get_memory_stats(self, strategy: str = None) -> Dict[str, Any]:
        """
        Get statistics about conversation memory with strategy breakdown
        
        Args:
            strategy: Optional strategy filter
            
        Returns:
            Dict with memory statistics
        """
        try:
            # Filter by strategy if specified
            queryset = ConversationMemory.objects.all()
            if strategy:
                queryset = queryset.filter(memory_strategy=strategy)
            
            total_memories = queryset.count()
            active_memories = queryset.filter(is_active=True).count()
            
            # Memory type breakdown
            memory_by_type = queryset.filter(is_active=True).values(
                'memory_type'
            ).annotate(count=Count('id'))
            
            # Strategy breakdown
            strategy_breakdown = ConversationMemory.objects.values('memory_strategy').annotate(
                count=Count('id')
            )
            
            # Priority breakdown
            priority_breakdown = queryset.values('priority').annotate(
                count=Count('id')
            )
            
            # Recent activity
            recent_memories = queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            # Cross-learning statistics
            cross_learning_stats = {
                'influenced_kb': queryset.filter(has_influenced_kb=True).count(),
                'pending_processing': queryset.filter(
                    memory_type__in=['correction', 'feedback', 'insight'],
                    has_influenced_kb=False,
                    is_active=True
                ).count()
            }
            
            return {
                'total_memories': total_memories,
                'active_memories': active_memories,
                'current_strategy': self.memory_manager.strategy,
                'memory_by_type': {item['memory_type']: item['count'] for item in memory_by_type},
                'strategy_breakdown': {sb['memory_strategy']: sb['count'] for sb in strategy_breakdown},
                'priority_breakdown': {pb['priority']: pb['count'] for pb in priority_breakdown},
                'recent_activity': recent_memories,
                'cross_learning_stats': cross_learning_stats,
                'retention_periods': self.memory_retention,
                'cleanup_needed': queryset.filter(
                    expires_at__lt=timezone.now()
                ).count()
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return {}


# Create global instance
conversation_memory_service = ConversationMemoryService() 