import csv
import json
import os
import re

def clean_filename(text):
    """
    Extracts the filename from the 'Target NPA' column.
    Often the filename is on a new line or mixed with other text.
    We look for .docx extensions or take the last non-empty line.
    """
    if not text:
        return None
    
    # Try to find a docx filename
    match = re.search(r'[\w\-\.]+\.docx', text)
    if match:
        return match.group(0)
    
    # Fallback: take the last line which usually contains the ID/filename
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        return lines[-1]
    
    return None

def convert_csv_to_json(csv_path, json_path):
    print(f"Reading {csv_path}...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Skip the first line which is a custom header/title
        first_line = f.readline()
        print(f"Skipping header: {first_line.strip()}")
        
        reader = csv.DictReader(f)
        
        dataset = []
        for row in reader:
            # CSV Columns: Категория, Вопрос, Целевой НПА, Место в документе, Релевантный кусок НПА
            question = row.get('Вопрос')
            # 'Релевантный кусок НПА' might be missing or named differently depending on CSV parser strictness
            # Let's check keys just in case
            ground_truth = row.get('Релевантный кусок НПА')
            target_npa_raw = row.get('Целевой НПА')
            
            if not question:
                continue
                
            source_filename = clean_filename(target_npa_raw)
            
            item = {
                "question": question,
                "ground_truth": ground_truth,
                "source_metadata": {
                    "source": source_filename,
                    "target_npa_raw": target_npa_raw # Keep raw for debugging
                }
            }
            dataset.append(item)
            
    print(f"Converted {len(dataset)} items.")
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to {json_path}")

if __name__ == "__main__":
    base_path = os.getcwd()
    csv_file = os.path.join(base_path, "problems_evaluation_dataset.csv")
    json_file = os.path.join(base_path, "eval_dataset_converted.json")
    
    convert_csv_to_json(csv_file, json_file)
