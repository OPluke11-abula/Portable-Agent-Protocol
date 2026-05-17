from agent_runtime.engine import AgentEngine
import json

def main():
    engine = AgentEngine(".agent/agent.md")
    print("Testing DAG Execution...")
    
    # We will simulate that the 'search_web' tool is in the router
    # Since search_web isn't implemented in the dummy router, let's inject a fake handler.
    engine.router.register_tool("search_web", lambda params: f"Found data for {params.get('query')}")

    inputs = {"topic": "AI Protocols"}
    result = engine.execute_workflow("research_and_report", inputs)
    
    print("\n--- Final Context ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Let's verify memory is populated
    mem_val = engine.memory.read("research_results")
    print(f"\n--- Memory 'research_results' ---")
    print(mem_val)

if __name__ == "__main__":
    main()
