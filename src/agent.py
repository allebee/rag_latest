import os
import json
from openai import OpenAI
from src.database import get_db
from src.config import GROK_API_KEY, GROK_MODEL

from sentence_transformers import CrossEncoder

from src.utils import get_compute_device

# X.AI setup
client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1",
)

CATEGORIES = [
    "Общий",
    "Передача",
    "Дарение",
    "Списание",
    "Аренда",
    "Приватизация",
    "Эффективность управления (отчетность)"
]

SYSTEM_PROMPT = """Ты - эксперт-консультант по управлению государственным имуществом Республики Казахстан.
Твоя задача - давать точные, пошаговые инструкции на основе предоставленного контекста из НПА (Нормативно-правовых актов).
Не выдумывай информацию. Если в контексте нет ответа, так и скажи.
Всегда ссылайся на источники (Глава, Статья) из контекста.
"""

class Agent:
    def __init__(self):
        self.db = get_db()
        self.npa_collection = self.db.get_or_create_collection("npa_collection")
        self.instr_collection = self.db.get_or_create_collection("instructions_collection")
        # Initialize Re-ranker
        print("Loading Re-ranker model...")
        device = get_compute_device()
        print(f"Re-ranker initialized on: {device.upper()}")
        
        try:
            self.reranker = CrossEncoder('BAAI/bge-reranker-v2-m3', device=device)
            print("Re-ranker loaded.")
        except Exception as e:
            if device == "cuda":
                print(f"Failed to load Re-ranker on CUDA: {e}")
                print("Retrying with CPU...")
                device = "cpu"
                self.reranker = CrossEncoder('BAAI/bge-reranker-v2-m3', device=device)
                print("Re-ranker loaded on CPU.")
            else:
                raise e

    def classify_intent(self, query):
        prompt = f"""
        Определи категорию запроса пользователя из следующего списка:
        {CATEGORIES}
        
        Запрос: {query}
        
        Верни только название категории. Если не уверен, верни "Общий".
        """
        
        try:
            response = client.chat.completions.create(
                model=GROK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            category = response.choices[0].message.content.strip()
            # Fuzzy match or simple check
            for cat in CATEGORIES:
                if cat in category:
                    return cat
            return "Общий"
        except Exception as e:
            print(f"Classification error: {e}")
            return "Общий"

    def retrieve(self, query, category):
        # 1. Broad Retrieval (Get more candidates)
        initial_k = 20 # Retrieve top 20 candidates per source
        candidates = []
        
        # Search Specific Category
        if category != "Общий":
            res_cat = self.npa_collection.query(
                query_texts=[query],
                n_results=initial_k,
                where={"category": category}
            )
            candidates.extend(self._format_results(res_cat))
            
            res_instr = self.instr_collection.query(
                query_texts=[query],
                n_results=initial_k,
                where={"category": category}
            )
            candidates.extend(self._format_results(res_instr))
            
        # Search General
        res_gen = self.npa_collection.query(
            query_texts=[query],
            n_results=initial_k,
            where={"category": "Общий"}
        )
        candidates.extend(self._format_results(res_gen))
        
        # Deduplicate candidates based on content
        unique_candidates = {c['content']: c for c in candidates}.values()
        candidates = list(unique_candidates)

        if not candidates:
            return []

        # 2. Re-ranking
        # Create pairs: [ [query, doc1], [query, doc2], ... ]
        pairs = [[query, doc['content']] for doc in candidates]
        
        scores = self.reranker.predict(pairs)
        
        # Combine docs with scores
        scored_docs = []
        for doc, score in zip(candidates, scores):
            doc['score'] = score
            scored_docs.append(doc)
            
        # Sort by score descending
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        
        # Return Top K
        top_k = 5
        return scored_docs[:top_k]

    def _format_results(self, chromadb_results):
        formatted = []
        if not chromadb_results['documents']:
            return []
            
        docs = chromadb_results['documents'][0]
        metas = chromadb_results['metadatas'][0]
        
        for doc, meta in zip(docs, metas):
            formatted.append({
                "content": doc,
                "metadata": meta
            })
        return formatted

    def generate_response(self, query, context_items):
        if not context_items:
            return "К сожалению, я не нашел информации по вашему запросу в базе знаний."
            
        context_str = "\n\n".join([f"Источник: {item['metadata'].get('source')} (Контекст: {item['metadata'].get('full_context', '')})\nТекст: {item['content']}" for item in context_items])
        
        user_message = f"""
        Вопрос пользователя: {query}
        
        Используй следующую информацию для ответа:
        {context_str}
        
        Составь подробный пошаговый план действий если это применимо.
        Обязательно указывай ссылки на статьи и пункты НПА.
        """
        
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content

    def check_need_clarification(self, query, history):
        # Format history
        history_str = ""
        for msg in history[-5:]: # Last 5 messages
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_str += f"{role}: {msg['content']}\n"
            
        prompt = f"""
        Ты - умный маршрутизатор диалога для юридического ассистента по Госимуществу РК.
        
        ВАЖНО: По умолчанию всегда считай, что речь идет о ГОСУДАРСТВЕННОМ имуществе (не частном). Не переспрашивай это.
        
        Твоя задача:
        1. Проанализировать последний запрос пользователя с учетом истории диалога.
        2. Если запрос СЛИШКОМ размытый (например просто "автомобиль" или "как продать?"), и контекст непонятен -> Сформулируй уточняющий вопрос.
        3. Если запрос понятен (или стал понятен из контекста) -> Переформулируй его в полной, самодостаточной форме для поиска.
        
        История диалога:
        {history_str}
        
        Последний запрос: {query}
        
        Верни ответ в формате JSON:
        {{
            "needs_clarification": true/false,
            "clarification_question": "Текст вопроса если true, иначе null",
            "rewritten_query": "Полный поисковый запрос если false, иначе null"
        }}
        
        
        Примеры:
        - User: "списание" -> needs_clarification: true, "Уточните, какое имущество вы хотите списать?"
        - User: "как его продать?" (History: "речь про автомобиль") -> needs_clarification: false, rewritten_query: "как продать служебный автомобиль государственного учреждения"
        """
        
        try:
            response = client.chat.completions.create(
                model=GROK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            # Clean up json if needed
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            return json.loads(content)
        except Exception as e:
            print(f"Router error: {e}")
            # Fallback to assuming it's a clear query
            return {"needs_clarification": False, "rewritten_query": query}

    def run(self, query, history=[]):
        # 1. Router Check
        router_result = self.check_need_clarification(query, history)
        
        if router_result.get("needs_clarification"):
            return {
                "response": router_result["clarification_question"],
                "category": "Уточнение",
                "context": []
            }
            
        # Use the rewritten query for search
        search_query = router_result.get("rewritten_query") or query
        print(f"Processing Query: {search_query}")
        
        category = self.classify_intent(search_query)
        print(f"Classified as: {category}")
        
        context = self.retrieve(search_query, category)
        response = self.generate_response(search_query, context)
        
        return {
            "response": response,
            "category": category,
            "context": context
        }
