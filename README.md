# 🏛️ AI Agent for Kazakhstan State Property

> **Status:** Production Ready 🟢  
> **LLM:** Grok (xAI)  
> **Docs:** [Full Documentation](./DOCUMENTATION.md)

An intelligent, **Agentic RAG** system acting as a virtual legal consultant for the Committee of State Property. It uses advanced reasoning patterns to interpret laws, clarify user intent, and provide strictly cited answers.

## 🚀 Key Features
*   **Active Agent:** Doesn't just search; it *thinks*, *clarifies*, and *corrects* itself.
*   **Self-Correction:** Every answer is "audited" by a second LLM pass to ensure zero hallucinations.
*   **HyDE (Hypothetical Document Embeddings):** Maps vague user queries to precise legal terminology.
*   **Hardware Optimized:** Runs on **Mac (MPS)**, **NVIDIA (CUDA)**, or **CPU** automatically.

## ⚡ Quick Start

### 1. Install
```bash
git clone https://github.com/allebee/rag_latest.git
cd rag_latest
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
Create `.env`:
```bash
GROK_API_KEY=your_key
```

### 3. Ingest Data
Build the local vector database from your documents:
```bash
python -m src.ingestion
```

### 4. Run
```bash
./run_app.sh
```
Open **http://localhost:8501** in your browser.

## 📚 Documentation
For deep technical details on the architecture, Self-Correction logic, and HyDE implementation, please read the **[Detailed Documentation](./DOCUMENTATION.md)**.
