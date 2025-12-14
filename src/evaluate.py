import json
import time
from openai import OpenAI
from src.agent import Agent
from src.config import GROK_API_KEY, GROK_MODEL

client = OpenAI(api_key=GROK_API_KEY, base_url="https://api.x.ai/v1")

def evaluate_response(question, agent_answer, ground_truth):
    prompt = f"""
    You are an impartial judge evaluating an AI assistant's answer.
    
    Question: {question}
    
    Ground Truth Answer: {ground_truth}
    
    Agent Answer: {agent_answer}
    
    Rate the Agent Answer on a scale of 1 to 5 based on how well it matches the Ground Truth in terms of factual correctness.
    1 = Completely wrong
    5 = Completely correct and accurate
    
    Also provide a brief explanation.
    
    Format: JSON with keys "score" (int) and "explanation" (string).
    """
    
    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"Error evaluating: {e}")
        return {"score": 0, "explanation": "Error"}

def main():
    print("Loading dataset...")
    with open("eval_dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    agent = Agent()
    results = []
    
    total_score = 0
    retrieval_hits = 0
    
    print(f"Starting evaluation of {len(dataset)} items...")
    
    for item in dataset:
        q = item["question"]
        gt = item["ground_truth"]
        source_meta = item["source_metadata"]
        
        print(f"\nProcessing: {q}")
        start_time = time.time()
        
        # Run Agent
        agent_result = agent.run(q)
        agent_answer = agent_result["response"]
        retrieved_context = agent_result["context"]
        duration = time.time() - start_time
        
        # 1. Check Retrieval (Hit Rate) - Simple strict check on source filename
        # Ideally we check if the exact chunk was retrieved, but checking source file is a good proxy for category/file retrieval
        hit = False
        target_source = source_meta.get("source")
        for ctx in retrieved_context:
            if ctx['metadata'].get('source') == target_source:
                hit = True
                break
        
        if hit:
            retrieval_hits += 1
            
        # 2. Check Correctness (LLM Judge)
        eval_res = evaluate_response(q, agent_answer, gt)
        score = eval_res["score"]
        total_score += score
        
        results.append({
            "question": q,
            "ground_truth": gt,
            "agent_answer": agent_answer,
            "retrieval_hit": hit,
            "correctness_score": score,
            "explanation": eval_res["explanation"],
            "latency": duration
        })
        print(f"Score: {score}/5 | Hit: {hit}")

    # Calculate Aggregates
    avg_score = total_score / len(dataset) if dataset else 0
    hit_rate = retrieval_hits / len(dataset) if dataset else 0
    
    report = f"""# RAG Evaluation Report

**Total Samples:** {len(dataset)}
**Average Correctness Score (1-5):** {avg_score:.2f}
**Retrieval Hit Rate:** {hit_rate:.2%}\n\n"""

    for r in results:
        report += f"## Q: {r['question']}\n"
        report += f"- **Score:** {r['correctness_score']}/5\n"
        report += f"- **Retrieval Hit:** {r['retrieval_hit']}\n"
        report += f"- **Explanation:** {r['explanation']}\n"
        report += f"- **Latency:** {r['latency']:.2f}s\n"
        report += "---\n"
        
    with open("evaluation_report.md", "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\nEvaluation Complete. Avg Score: {avg_score:.2f}, Hit Rate: {hit_rate:.2%}")

if __name__ == "__main__":
    main()
