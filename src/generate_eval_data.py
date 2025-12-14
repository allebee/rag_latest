import json
import random
from openai import OpenAI
from src.database import get_db
from src.config import GROK_API_KEY, GROK_MODEL

client = OpenAI(api_key=GROK_API_KEY, base_url="https://api.x.ai/v1")

def generate_qa_pair(chunk_text, metadata):
    prompt = f"""
    You are an expert in creating evaluation datasets for Kazakhstan government regulations.
    Based ONLY on the following text, generate a specific question and the correct answer IN RUSSIAN.

    CRITICAL RULES:
    1. Ignore administrative metadata (signatures, copyright, dates, document numbers, authors).
    2. Focus ONLY on legal rules, rights, obligations, procedures, and definitions.
    3. If the text is just a header, a list of deleted items, or lacks substantial legal content, return specific JSON: {{"question": null, "answer": null}}.
    
    Context:
    "{chunk_text}"
    Source: {metadata.get('source')} - {metadata.get('full_context')}
    
    Format your response as a valid JSON object with keys "question" and "answer". 
    Do not add markdown formatting.
    """
    
    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        
        data = json.loads(content)
        if not data.get("question"): # Filter out nulls
            return None
        return data
    except Exception as e:
        print(f"Error generating QA: {e}")
        return None

def main():
    db = get_db()
    npa_col = db.get_or_create_collection("npa_collection")
    
    # Get all documents (limit to a manageable number for this demo)
    results = npa_col.get(limit=200) # Increased limit to find better chunks
    
    ids = results['ids']
    documents = results['documents']
    metadatas = results['metadatas']
    
    if not ids:
        print("No documents found in DB. Run ingestion first.")
        return

    # Filter for meaningful chunks (len > 300) - Stricter filter
    indices = [i for i, doc in enumerate(documents) if len(doc) > 300]
    
    # Sample 20 random chunks
    sample_indices = random.sample(indices, min(20, len(indices)))
    
    dataset = []
    
    print(f"Generating evaluation dataset from {len(sample_indices)} chunks (filtered from {len(indices)})...")
    
    for i in sample_indices:
        text = documents[i]
        meta = metadatas[i]
        
        qa = generate_qa_pair(text, meta)
        if qa:
            dataset.append({
                "question": qa["question"],
                "ground_truth": qa["answer"],
                "source_chunk": text,
                "source_metadata": meta
            })
            print(f"Generated Q: {qa['question']}")

    with open("eval_dataset.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(dataset)} items to eval_dataset.json")

if __name__ == "__main__":
    main()
