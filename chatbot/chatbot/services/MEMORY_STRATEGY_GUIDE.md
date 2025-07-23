# Conversation Memory Strategy Guide

## Overview

The enhanced conversation memory system provides strategic memory management for chatbot interactions. This system supports three main memory strategies with comprehensive documentation and usage examples.

## Memory Strategies

### 1. Short-term Memory Strategy (`'short_term'`)
**Purpose**: Remembers recent message context (5-10 messages)

**Use Cases**:
- Maintaining context within a single conversation
- Quick follow-up questions
- Immediate conversation continuity

**Configuration**:
```python
# Initialize with short-term strategy
memory_service = ConversationMemoryService(default_strategy='short_term')

# Or switch to short-term strategy
memory_service.set_strategy('short_term')
```

**Features**:
- Stores recent 5-10 messages
- Low memory retention (1 day)
- Focuses on 'context' memory type
- Auto-expires quickly to maintain efficiency

### 2. Cross-conversation Learning Strategy (`'cross_learning'`)
**Purpose**: Updates knowledge base from user interactions

**Use Cases**:
- Learning from user corrections
- Processing user feedback
- Improving chatbot responses over time
- Building institutional knowledge

**Configuration**:
```python
# Initialize with cross-learning strategy
memory_service = ConversationMemoryService(default_strategy='cross_learning')

# Process cross-conversation learning
results = memory_service.process_cross_conversation_learning(user=user)
```

**Features**:
- Long retention period (180 days)
- Focuses on 'correction', 'feedback', 'insight' memory types
- High priority processing
- Influences knowledge base updates

### 3. RAG Context-aware Strategy (`'rag_context'`)
**Purpose**: Uses conversation history in retrieval-augmented generation

**Use Cases**:
- Enhancing RAG pipeline with conversation context
- Personalized responses based on conversation history
- Intent and preference tracking
- Context-aware information retrieval

**Configuration**:
```python
# Initialize with RAG context strategy
memory_service = ConversationMemoryService(default_strategy='rag_context')

# Get RAG-enhanced context
context = memory_service.get_conversation_context(conversation, strategy='rag_context')
```

**Features**:
- Medium retention (7 days)
- Focuses on 'intent', 'preference', 'topic', 'context' memory types
- Weighted for RAG relevance
- Auto-expires for performance

### 4. Hybrid Strategy (`'hybrid'`)
**Purpose**: Combines all three approaches for comprehensive memory management

**Use Cases**:
- General-purpose chatbot deployment
- Balanced performance and learning
- Complete memory coverage
- Production environments

**Configuration**:
```python
# Default strategy - combines all approaches
memory_service = ConversationMemoryService(default_strategy='hybrid')
```

**Features**:
- Moderate retention (30 days)
- Supports all memory types
- Balanced priority handling
- Comprehensive memory coverage

## Usage Examples

### Basic Usage

```python
from chatbot.services.conversation_memory_service import ConversationMemoryService

# Initialize service with hybrid strategy
memory_service = ConversationMemoryService(default_strategy='hybrid')

# Extract memory from user message
memories = memory_service.extract_memory_from_message(
    message=user_message,
    conversation=conversation,
    strategy='rag_context'  # Optional strategy override
)

# Get conversation context for RAG
context = memory_service.get_conversation_context(
    conversation=conversation,
    max_messages=10,
    strategy='rag_context'
)

# Process cross-learning
results = memory_service.process_cross_conversation_learning(
    user=user,
    strategy='cross_learning'
)
```

### Strategy-Specific Operations

#### Short-term Memory
```python
# Switch to short-term strategy
memory_service.set_strategy('short_term')

# Extract recent context
recent_context = memory_service.get_conversation_context(
    conversation=conversation,
    max_messages=5,
    strategy='short_term'
)

# Get short-term statistics
stats = memory_service.get_memory_stats(strategy='short_term')
```

#### Cross-learning Operations
```python
# Process corrections and feedback
learning_results = memory_service.process_cross_conversation_learning(
    user=user,
    strategy='cross_learning'
)

print(f"Processed {learning_results['corrections_processed']} corrections")
print(f"Processed {learning_results['feedback_processed']} feedback items")
```

#### RAG Context Enhancement
```python
# Get RAG-optimized context
rag_context = memory_service.get_conversation_context(
    conversation=conversation,
    strategy='rag_context'
)

# Get user context across conversations
user_context = memory_service.get_user_context(
    user=user,
    max_memories=20,
    strategy='rag_context'
)
```

### Memory Manager Direct Usage

```python
from chatbot.services.conversation_memory_service import ConversationMemoryManager

# Create strategy-specific manager
manager = ConversationMemoryManager(strategy='short_term')

# Get short-term context
context = manager.get_short_term_context(conversation)

# Create memory with strategy
memory = manager.create_memory(
    conversation=conversation,
    user=user,
    memory_type='context',
    content=message.content,
    priority='medium',
    confidence=0.8,
    relevance=0.7
)
```

## Database Schema

### ConversationMemory Model Fields

```python
class ConversationMemory(models.Model):
    # Strategy selection (NEW)
    memory_strategy = models.CharField(
        max_length=20,
        choices=MEMORY_STRATEGIES,
        default='hybrid'
    )
    
    # Recent messages storage (NEW)
    recent_messages = models.JSONField(
        default=list,
        help_text='Stores recent conversation messages'
    )
    
    # Enhanced fields
    rag_weight = models.FloatField(
        default=1.0,
        help_text='Weight for RAG context strategy'
    )
    
    # Existing fields...
    memory_type = models.CharField(max_length=20, choices=MEMORY_TYPES)
    content = models.TextField()
    context = models.JSONField(default=dict)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS)
    confidence_score = models.FloatField(default=0.7)
    relevance_score = models.FloatField(default=0.5)
    has_influenced_kb = models.BooleanField(default=False)
    # ... other fields
```

## API Reference

### ConversationMemoryService

#### Methods

- `__init__(default_strategy: str = 'hybrid')` - Initialize service
- `set_strategy(strategy: str)` - Change memory strategy
- `extract_memory_from_message(message, conversation, strategy=None)` - Extract memory from message
- `get_conversation_context(conversation, max_messages=10, strategy=None)` - Get conversation context
- `get_user_context(user, max_memories=20, strategy=None)` - Get user context
- `process_cross_conversation_learning(user=None, strategy=None)` - Process learning
- `get_memory_stats(strategy=None)` - Get memory statistics
- `cleanup_expired_memories()` - Clean up expired memories

### ConversationMemoryManager

#### Methods

- `__init__(strategy: str = 'hybrid')` - Initialize manager
- `create_memory(conversation, user, memory_type, content, ...)` - Create memory
- `get_short_term_context(conversation)` - Get short-term context
- `process_cross_learning(user=None)` - Process cross-learning
- `get_rag_context(conversation, user=None)` - Get RAG context

### ConversationMemory Model

#### Class Methods

- `get_active_memories(conversation=None, user=None, memory_type=None, strategy=None)` - Get active memories
- `get_short_term_context(conversation, max_messages=10)` - Get short-term context
- `get_cross_learning_insights(user=None)` - Get learning insights
- `get_rag_context_memories(conversation, user=None)` - Get RAG memories
- `cleanup_expired()` - Clean up expired memories

## Configuration

### Strategy Configuration

Each strategy has specific configuration parameters:

```python
strategy_configs = {
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
```

## Best Practices

### 1. Strategy Selection

- Use `'short_term'` for quick, context-aware responses
- Use `'cross_learning'` for knowledge base improvement
- Use `'rag_context'` for enhanced information retrieval
- Use `'hybrid'` for comprehensive coverage

### 2. Memory Management

- Regularly clean up expired memories
- Monitor memory statistics
- Adjust retention periods based on usage patterns
- Use appropriate priority levels

### 3. Performance Optimization

- Use strategy-specific queries for better performance
- Implement proper indexing on memory_strategy field
- Monitor memory growth and clean up regularly
- Use RAG weights for relevance scoring

### 4. Integration with RAG

```python
# Enhanced RAG integration
def enhanced_rag_query(query, conversation, user):
    # Get conversation-aware context
    context = memory_service.get_conversation_context(
        conversation=conversation,
        strategy='rag_context'
    )
    
    # Get user context
    user_context = memory_service.get_user_context(
        user=user,
        strategy='rag_context'
    )
    
    # Combine with RAG service
    return enhanced_rag_service.retrieve_relevant_knowledge(
        query=query,
        conversation=conversation,
        user=user
    )
```

## Troubleshooting

### Common Issues

1. **Memory Growth**: Use `cleanup_expired_memories()` regularly
2. **Performance**: Use strategy-specific queries
3. **Context Length**: Adjust `max_messages` parameter
4. **Strategy Conflicts**: Use hybrid strategy for balanced approach

### Debugging

```python
# Get memory statistics
stats = memory_service.get_memory_stats()
print(f"Current strategy: {stats['current_strategy']}")
print(f"Total memories: {stats['total_memories']}")
print(f"Strategy breakdown: {stats['strategy_breakdown']}")

# Check cleanup needed
if stats['cleanup_needed'] > 0:
    memory_service.cleanup_expired_memories()
```

## Migration Guide

### From Previous System

1. Run the migration: `python manage.py migrate chatbot`
2. Update service initialization
3. Add strategy parameters to existing calls
4. Test with hybrid strategy first
5. Gradually move to specific strategies

### Example Migration

```python
# Old usage
memory_service = ConversationMemoryService()
context = memory_service.get_conversation_context(conversation)

# New usage
memory_service = ConversationMemoryService(default_strategy='hybrid')
context = memory_service.get_conversation_context(
    conversation=conversation,
    strategy='rag_context'
)
```

---

This guide provides comprehensive documentation for the enhanced conversation memory system with strategic memory management capabilities. 