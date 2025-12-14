# 🏛️ AI Agent for Kazakhstan State Property

An intelligent RAG-based chatbot that acts as a consultant for Kazakhstan government property regulations. It uses **Grok (xAI)** for reasoning and **ChromaDB** for vector storage, with automatic hardware acceleration (MPS/CUDA).

## 🚀 Features
*   **Agentic RAG:** Re-writes queries, clarifies ambiguities, and retrieves multi-step legal context.
*   **Hybrid Retrieval:** Semantic search + Cross-Encoder Re-ranking (`BAAI/bge-reranker-v2-m3`).
*   **Hardware Aware:** Automatically selects **AMX/MPS** (Apple Silicon) or **CUDA** (NVIDIA RTX) or **CPU**.
*   **Sources:** Parses DOCX/PDF with structural hierarchy (Chapters, Articles).

## 🛠️ Installation

### 1. Clone & Setup
```bash
git clone <repo_url>
cd rag_latest

# Create Virtual Environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory:
```bash
# .env
GROK_API_KEY=your_key_here
GROK_MODEL=grok-beta
CHROMA_PATH=./chroma_db
EMBEDDING_MODEL=BAAI/bge-m3
```

### 3. Run Application
```bash
# Run the Streamlit App
./run_app.sh
```

## ⚡ Hardware Acceleration
The system automatically detects your hardware:
*   **Apple Silicon (Mac M1/M2/M3):** Uses **MPS** (Metal Performance Shaders).
*   **NVIDIA GPUs (RTX 3090/4090/5090):** Uses **CUDA**.
*   **Others:** Fallback to CPU.

To verify your device:
```bash
python check_hardware.py
```

## 📂 Structure
*   `src/agent.py`: Core logic (Router, Retrieval, Generation).
*   `src/ingestion.py`: Parsers for Legal Documents.
*   `src/utils.py`: Hardware detection utilities.
*   `app.py`: Streamlit Frontend.
*   `eval_dataset.json`: Synthetic evaluation data.
