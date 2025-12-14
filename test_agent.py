from src.agent import Agent

def test():
    print("Initializing Agent...")
    agent = Agent()
    
    query = "Как передать имущество из республиканской собственности в коммунальную?"
    print(f"Query: {query}")
    
    result = agent.run(query)
    
    print("\n--- RESPONSE ---")
    print(result["response"])
    print("\n--- SOURCES ---")
    for item in result["context"]:
        print(f"- {item['metadata'].get('source')}: {item['metadata'].get('full_context')}")

if __name__ == "__main__":
    test()
