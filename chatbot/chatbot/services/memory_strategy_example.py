"""
Comprehensive example demonstrating the new conversation memory strategy features.

This example shows how to use:
1. Short-term conversation memory (recent 5-10 messages)
2. Cross-conversation learning (updates knowledge base)
3. RAG context-aware processing (enhances retrieval)
4. Hybrid strategy (combines all approaches)
"""

from django.contrib.auth.models import User
from chatbot.models import Conversation, Message
from chatbot.services.conversation_memory_service import (
    ConversationMemoryService, 
    ConversationMemoryManager
)
from chatbot.services.enhanced_rag_service import enhanced_rag_service


def demonstrate_memory_strategies():
    """Comprehensive demonstration of memory strategy features"""
    
    # Get a user and conversation (you would get these from your actual data)
    user = User.objects.first()
    conversation = Conversation.objects.filter(user=user).first()
    
    print("=== CONVERSATION MEMORY STRATEGY DEMONSTRATION ===\n")
    
    # 1. SHORT-TERM MEMORY STRATEGY
    print("1. SHORT-TERM MEMORY STRATEGY")
    print("-" * 40)
    
    # Initialize with short-term strategy
    short_term_service = ConversationMemoryService(default_strategy='short_term')
    
    # Create a sample message
    sample_message = Message.objects.create(
        conversation=conversation,
        content="I'm looking for information about engineering programs at APU",
        sender='user'
    )
    
    # Extract memories using short-term strategy
    memories = short_term_service.extract_memory_from_message(
        message=sample_message,
        conversation=conversation,
        strategy='short_term'
    )
    
    print(f"Extracted {len(memories)} short-term memories")
    for memory in memories:
        print(f"  - {memory.memory_type}: {memory.content[:50]}...")
    
    # Get short-term context
    short_term_context = short_term_service.get_conversation_context(
        conversation=conversation,
        max_messages=5,
        strategy='short_term'
    )
    
    print(f"\nShort-term context:\n{short_term_context[:200]}...\n")
    
    # 2. CROSS-CONVERSATION LEARNING STRATEGY
    print("2. CROSS-CONVERSATION LEARNING STRATEGY")
    print("-" * 40)
    
    # Initialize with cross-learning strategy
    learning_service = ConversationMemoryService(default_strategy='cross_learning')
    
    # Simulate a correction message
    correction_message = Message.objects.create(
        conversation=conversation,
        content="Actually, the fees for engineering programs are different. It should be RM45,000 per year.",
        sender='user'
    )
    
    # Extract correction memory
    correction_memories = learning_service.extract_memory_from_message(
        message=correction_message,
        conversation=conversation,
        strategy='cross_learning'
    )
    
    print(f"Extracted {len(correction_memories)} correction memories")
    for memory in correction_memories:
        print(f"  - {memory.memory_type}: {memory.content[:50]}...")
    
    # Process cross-conversation learning
    learning_results = learning_service.process_cross_conversation_learning(
        user=user,
        strategy='cross_learning'
    )
    
    print(f"\nCross-learning results:")
    print(f"  - Corrections processed: {learning_results.get('corrections_processed', 0)}")
    print(f"  - Feedback processed: {learning_results.get('feedback_processed', 0)}")
    print(f"  - Insights generated: {learning_results.get('insights_generated', 0)}")
    
    # 3. RAG CONTEXT-AWARE STRATEGY
    print("\n3. RAG CONTEXT-AWARE STRATEGY")
    print("-" * 40)
    
    # Initialize with RAG context strategy
    rag_service = ConversationMemoryService(default_strategy='rag_context')
    
    # Create a preference message
    preference_message = Message.objects.create(
        conversation=conversation,
        content="I prefer part-time study mode and would like programs in Kuala Lumpur",
        sender='user'
    )
    
    # Extract preference memory
    preference_memories = rag_service.extract_memory_from_message(
        message=preference_message,
        conversation=conversation,
        strategy='rag_context'
    )
    
    print(f"Extracted {len(preference_memories)} preference memories")
    for memory in preference_memories:
        print(f"  - {memory.memory_type}: {memory.content[:50]}...")
    
    # Get RAG-enhanced context
    rag_context = rag_service.get_conversation_context(
        conversation=conversation,
        strategy='rag_context'
    )
    
    print(f"\nRAG context:\n{rag_context[:200]}...\n")
    
    # Get user context across conversations
    user_context = rag_service.get_user_context(
        user=user,
        max_memories=10,
        strategy='rag_context'
    )
    
    print(f"User context:\n{user_context[:200]}...\n")
    
    # 4. HYBRID STRATEGY (COMBINES ALL)
    print("4. HYBRID STRATEGY (COMBINES ALL)")
    print("-" * 40)
    
    # Initialize with hybrid strategy
    hybrid_service = ConversationMemoryService(default_strategy='hybrid')
    
    # Create a comprehensive message
    comprehensive_message = Message.objects.create(
        conversation=conversation,
        content="Thanks for the information! I'm interested in the software engineering program. Can you tell me more about the curriculum?",
        sender='user'
    )
    
    # Extract memories using hybrid strategy
    hybrid_memories = hybrid_service.extract_memory_from_message(
        message=comprehensive_message,
        conversation=conversation,
        strategy='hybrid'
    )
    
    print(f"Extracted {len(hybrid_memories)} hybrid memories")
    for memory in hybrid_memories:
        print(f"  - {memory.memory_type} ({memory.memory_strategy}): {memory.content[:50]}...")
    
    # Get comprehensive context
    hybrid_context = hybrid_service.get_conversation_context(
        conversation=conversation,
        strategy='hybrid'
    )
    
    print(f"\nHybrid context:\n{hybrid_context[:200]}...\n")
    
    # 5. MEMORY MANAGER DIRECT USAGE
    print("5. MEMORY MANAGER DIRECT USAGE")
    print("-" * 40)
    
    # Create strategy-specific managers
    short_term_manager = ConversationMemoryManager(strategy='short_term')
    cross_learning_manager = ConversationMemoryManager(strategy='cross_learning')
    rag_manager = ConversationMemoryManager(strategy='rag_context')
    
    # Get short-term context
    short_context = short_term_manager.get_short_term_context(conversation)
    print(f"Short-term context messages: {len(short_context)}")
    
    # Get RAG context
    rag_context_text = rag_manager.get_rag_context(conversation, user)
    print(f"RAG context length: {len(rag_context_text)}")
    
    # Process cross-learning
    learning_results = cross_learning_manager.process_cross_learning(user)
    print(f"Cross-learning results: {learning_results}")
    
    # 6. INTEGRATION WITH ENHANCED RAG
    print("\n6. INTEGRATION WITH ENHANCED RAG")
    print("-" * 40)
    
    # Query using enhanced RAG with conversation context
    query = "What are the admission requirements for engineering programs?"
    
    # Get enhanced knowledge with conversation context
    knowledge_results = enhanced_rag_service.retrieve_relevant_knowledge(
        query=query,
        conversation=conversation,
        user=user
    )
    
    print(f"Enhanced RAG results: {len(knowledge_results)} entries")
    for i, result in enumerate(knowledge_results[:3]):
        entry = result['entry']
        score = result['relevance_score']
        strategy = result.get('strategy', 'unknown')
        print(f"  {i+1}. {entry.category} (Score: {score:.2f}, Strategy: {strategy})")
        print(f"     Q: {entry.question[:60]}...")
        print(f"     A: {entry.answer[:60]}...")
    
    # 7. MEMORY STATISTICS
    print("\n7. MEMORY STATISTICS")
    print("-" * 40)
    
    # Get statistics for different strategies
    strategies = ['short_term', 'cross_learning', 'rag_context', 'hybrid']
    
    for strategy in strategies:
        stats = hybrid_service.get_memory_stats(strategy=strategy)
        print(f"\n{strategy.title()} Strategy Stats:")
        print(f"  - Total memories: {stats.get('total_memories', 0)}")
        print(f"  - Active memories: {stats.get('active_memories', 0)}")
        print(f"  - Recent activity: {stats.get('recent_activity', 0)}")
        print(f"  - Cleanup needed: {stats.get('cleanup_needed', 0)}")
    
    # Overall statistics
    overall_stats = hybrid_service.get_memory_stats()
    print(f"\nOverall Statistics:")
    print(f"  - Current strategy: {overall_stats.get('current_strategy', 'unknown')}")
    print(f"  - Total memories: {overall_stats.get('total_memories', 0)}")
    print(f"  - Strategy breakdown: {overall_stats.get('strategy_breakdown', {})}")
    print(f"  - Cross-learning stats: {overall_stats.get('cross_learning_stats', {})}")
    
    # 8. CLEANUP AND MAINTENANCE
    print("\n8. CLEANUP AND MAINTENANCE")
    print("-" * 40)
    
    # Clean up expired memories
    cleanup_results = hybrid_service.cleanup_expired_memories()
    print(f"Cleanup results: {cleanup_results}")
    
    # Dynamic strategy switching
    print("\nDynamic Strategy Switching:")
    hybrid_service.set_strategy('short_term')
    print(f"Switched to: {hybrid_service.memory_manager.strategy}")
    
    hybrid_service.set_strategy('rag_context')
    print(f"Switched to: {hybrid_service.memory_manager.strategy}")
    
    hybrid_service.set_strategy('hybrid')
    print(f"Switched back to: {hybrid_service.memory_manager.strategy}")
    
    print("\n=== DEMONSTRATION COMPLETE ===")


def demonstrate_api_usage():
    """Demonstrate typical API usage patterns"""
    
    print("\n=== API USAGE PATTERNS ===\n")
    
    # Get sample data
    user = User.objects.first()
    conversation = Conversation.objects.filter(user=user).first()
    
    # 1. Quick setup for different use cases
    print("1. QUICK SETUP FOR DIFFERENT USE CASES")
    print("-" * 40)
    
    # For chat applications needing recent context
    chat_memory = ConversationMemoryService(default_strategy='short_term')
    print("✓ Chat application setup (short_term strategy)")
    
    # For knowledge base improvement
    learning_memory = ConversationMemoryService(default_strategy='cross_learning')
    print("✓ Learning system setup (cross_learning strategy)")
    
    # For RAG-enhanced responses
    rag_memory = ConversationMemoryService(default_strategy='rag_context')
    print("✓ RAG enhancement setup (rag_context strategy)")
    
    # For production deployment
    production_memory = ConversationMemoryService(default_strategy='hybrid')
    print("✓ Production deployment setup (hybrid strategy)")
    
    # 2. Common operations
    print("\n2. COMMON OPERATIONS")
    print("-" * 40)
    
    # Process a user message
    sample_message = Message.objects.create(
        conversation=conversation,
        content="I need information about computer science programs",
        sender='user'
    )
    
    # Extract memories
    memories = production_memory.extract_memory_from_message(
        message=sample_message,
        conversation=conversation
    )
    print(f"✓ Extracted {len(memories)} memories from user message")
    
    # Get conversation context
    context = production_memory.get_conversation_context(
        conversation=conversation,
        max_messages=10
    )
    print(f"✓ Retrieved conversation context ({len(context)} characters)")
    
    # Get user context
    user_context = production_memory.get_user_context(
        user=user,
        max_memories=15
    )
    print(f"✓ Retrieved user context ({len(user_context)} characters)")
    
    # Process learning
    learning_results = production_memory.process_cross_conversation_learning(user=user)
    print(f"✓ Processed cross-conversation learning: {learning_results}")
    
    # Get statistics
    stats = production_memory.get_memory_stats()
    print(f"✓ Memory statistics: {stats.get('total_memories', 0)} total memories")
    
    # 3. Strategy-specific operations
    print("\n3. STRATEGY-SPECIFIC OPERATIONS")
    print("-" * 40)
    
    # Short-term operations
    short_term_context = production_memory.get_conversation_context(
        conversation=conversation,
        strategy='short_term'
    )
    print(f"✓ Short-term context: {len(short_term_context)} characters")
    
    # RAG operations
    rag_context = production_memory.get_conversation_context(
        conversation=conversation,
        strategy='rag_context'
    )
    print(f"✓ RAG context: {len(rag_context)} characters")
    
    # Cross-learning operations
    learning_results = production_memory.process_cross_conversation_learning(
        user=user,
        strategy='cross_learning'
    )
    print(f"✓ Cross-learning results: {learning_results}")
    
    print("\n=== API DEMONSTRATION COMPLETE ===")


if __name__ == "__main__":
    # Run the demonstrations
    demonstrate_memory_strategies()
    demonstrate_api_usage()
    
    print("\n" + "="*60)
    print("CONVERSATION MEMORY STRATEGY SYSTEM")
    print("="*60)
    print("✓ Short-term memory: Recent conversation context (5-10 messages)")
    print("✓ Cross-learning: Knowledge base updates from interactions")
    print("✓ RAG context: Conversation-aware retrieval enhancement")
    print("✓ Hybrid strategy: Combines all approaches")
    print("✓ Dynamic strategy switching")
    print("✓ Comprehensive documentation")
    print("✓ Database migration included")
    print("✓ Enhanced RAG integration")
    print("="*60) 