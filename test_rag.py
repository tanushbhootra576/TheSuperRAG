import sys
from graph import RAGGraph

def test_query(rag, query_text):
    print(f"\n{'='*50}\nTesting Query: '{query_text}'\n{'-'*50}")
    
    inputs = {
        "user_query": query_text,
        "current_search_query": query_text,
        "loop_count": 0,
        "logs": []
    }
    
    final_generation = ""
    current_active_query = query_text
    
    for output in rag.app.stream(inputs):
        for key, value in output.items():
            if key == "retrieve":
                print(f"🔍 [Retrieve Node] Searching DB for: '{current_active_query}'")
            elif key == "generate":
                print(f"🤖 [Generate Node] Analyzing context...")
                final_generation = value.get("generation", "")
            elif key == "rewrite_query":
                current_active_query = value.get('current_search_query', current_active_query)
                print(f"⚠️ [Self-Heal] Triggered! Information missing. Rewrote query to: '{current_active_query}'")
                
    if "information missing" in final_generation.lower():
         print("\n❌ Final Status: Failed to find an answer after multiple self-heal attempts.")
    else:
         print(f"\n✅ Final Answer:\n{final_generation}")

if __name__ == "__main__":
    print("Booting up TheSuperRAG...")
    try:
        rag = RAGGraph()
        
        # Test 1: Simple Retrieval
        test_query(rag, "What are the main topics discussed in these documents?")
        
        # Test 2: Specific Condition (This might trigger self-heal if the exact words are missing initially)
        test_query(rag, "What are the exact eligibility criteria based on income and age to qualify?")
        
        # Test 3: Completely Made-up Scenario (Should exhaust self-heal loops and stop)
        test_query(rag, "Does my health insurance cover emergency spaceship repairs on Mars?")
        
    except Exception as e:
        print(f"Test failed due to an exception: {e}")
