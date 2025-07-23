import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot.settings')
django.setup()

from chatbot.services.enhanced_rag_service import enhanced_rag_service
from pprint import pprint

def test_rag_query(query, categories=None):
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"Categories: {categories if categories else 'All'}")
    print('='*80)
    
    results = enhanced_rag_service.retrieve_relevant_knowledge(query, categories)
    
    print(f"\nFound {len(results)} relevant entries:\n")
    
    for i, result in enumerate(results, 1):
        entry = result['entry']
        score = result['relevance_score']
        print(f"\n{i}. Relevance Score: {score:.3f}")
        print(f"Category: {entry.category}")
        print(f"Q: {entry.question}")
        print(f"A: {entry.answer}")
        print('-'*50)

# Test various queries
print("\nTesting Enhanced RAG System with New Dataset\n")

# Test 1: Program Information
test_rag_query("Tell me about the MSc Artificial Intelligence program")

# Test 2: Accommodation Options
test_rag_query("What accommodation options are available near APU?", ["Student Accommodation"])

# Test 3: Course Modules
test_rag_query("What modules are included in the Computer Science degree?", ["Curriculum and Modules"])

# Test 4: Study Modes and Duration
test_rag_query("How long does it take to complete a Bachelor's degree?", ["Programs and Courses"])

# Test 5: Mixed Query
test_rag_query("What are the fees and admission requirements for international students in 2025?", 
               ["Fees and Financial Aid", "Admissions"]) 