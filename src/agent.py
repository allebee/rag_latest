import os
import json
from openai import OpenAI
from src.database import get_db
from src.config import GROK_API_KEY, GROK_MODEL



from src.utils import get_compute_device

# X.AI setup
client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1",
)

CATEGORIES = [
    "Передача",
    "Дарение",
    "Списание",
    "Аренда",
    "Приватизация",
    "Эффективность управления (отчетность)"
]

SYSTEM_PROMPT = """Ты - эксперт-консультант по управлению государственным имуществом Республики Казахстан.
Твоя задача - давать точные, пошаговые инструкции на основе предоставленного контекста из НПА (Нормативно-правовых актов).

ДИРЕКТИВЫ ПО ФОРМАТУ ОТВЕТА:
1. Описывай процедуры подробно.
2. ВСЕГДА указывай:
   - Какие формальности требуется соблюсти.
   - Какие документы оформить (списком).
   - Куда подавать документы (веб-портал, орган и т.д.).

ОГРАНИЧЕНИЯ (GUARDRAILS):
1. Не выдумывай информацию. Если нет в контексте, так и скажи.
2. Всегда ссылайся на источники (Глава, Статья) в скобках.
3. ИЗБЕГАЙ упоминания "Национального Банка" и "Военного имущества/Военного времени", если пользователь ПРЯМО не спросил об этом. Это специфические исключения, которые путают пользователей. Оперируй общими правилами для госимущества.
"""

class Agent:
    def __init__(self):
        self.db = get_db()
        self.npa_collection = self.db.get_or_create_collection("npa_collection")
        self.instr_collection = self.db.get_or_create_collection("instructions_collection")
        # Initialize Re-ranker
        # Re-ranker disabled for performance
        # self.reranker = None

    def classify_intent(self, query):
        prompt = f"""
        Определи наиболее подходящую категорию запроса пользователя из следующего списка:
        {CATEGORIES}
        
        Запрос: {query}
        
        Инструкция:
        1. Выбери ОДНУ категорию, которая лучше всего описывает тематику запроса.
        2. Даже если запрос общий, попытайся отнести его к одной из конкретных тем.
        3. Верни ТОЛЬКО название категории.
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
            # Fallback if no match found - pick the first one or most broad? 
            # User wants "one more specific category". Let's default to "Передача" or "Приватизация" as they are common? 
            # Or better, just return one of them.
            return "Передача" # Default fallback
        except Exception as e:
            print(f"Classification error: {e}")
            return "Передача"

    def _format_results(self, chromadb_results):
        formatted = []
        if not chromadb_results['documents']:
            return []
            
        docs = chromadb_results['documents'][0]
        metas = chromadb_results['metadatas'][0]
        # Distances are optional, handle if missing
        dists = chromadb_results.get('distances', [None]*len(docs))
        if dists:
            dists = dists[0]
        else:
            dists = [1.0] * len(docs) # Default high distance
        
        for doc, meta, dist in zip(docs, metas, dists):
            formatted.append({
                "content": doc,
                "metadata": meta,
                "distance": dist
            })
        return formatted

    def generate_response(self, query, context_items, stream=False):
        if not context_items:
            if stream:
                yield "К сожалению, я не нашел информации по вашему запросу в базе знаний."
                return
            return "К сожалению, я не нашел информации по вашему запросу в базе знаний."
            
        context_parts = []
        for item in context_items:
            source = item['metadata'].get('source', 'Unknown')
            # Hierarchical context from ingestion (e.g., "Law > Chapter 2 > Article 5")
            hierarchy = item['metadata'].get('full_context', 'No context path')
            content = item['content']
            
            # Format: [Source: file.docx | Path: Chapter > Article]
            # Content: ...
            part = f"[[Источник: {source} | Структура: {hierarchy}]]\\nТекст: {content}"
            context_parts.append(part)
            
        context_str = "\\n\\n".join(context_parts)
        
        user_message = f"""
Ты аналитик по нормативно-правовым актам (НПА).
Твоя задача — ответить на вопрос, опираясь ИСКЛЮЧИТЕЛЬНО на предоставленный ниже контекст.

Вопрос: {query}

КОНТЕКСТ:
{context_str}

ИНСТРУКЦИЯ ПО ОФОРМЛЕНИЮ ОТВЕТА (СТРОГО):

1. **Структура ответа:**
   - **Заголовок:** Краткая суть ответа.
   - **Основная часть:** Четкое разъяснение одним маркированным списком.

2. **Правила цитирования (ВАЖНО):**
   - НЕ делай отдельный раздел "Обоснование" или "Источники".
   - Указывай ссылку на пункт/статью СРАЗУ в конце предложения в скобках.
   - Пример: "...передается по постановлению акимата (п. 10 Правил)." или "...в срок до 30 дней (ст. 15 Закона)."
   - НЕ пиши "Согласно тексту..." в начале. Пиши суть, а источник в скобки.

3. **Стиль:**
   - Официально-деловой, нейтральный.
   - Без вступлений и заключений.

3. **Ограничения:**
   - ЕСЛИ В КОНТЕКСТЕ НЕТ ОТВЕТА: Напиши "В предоставленных нормативных актах информация по данному вопросу отсутствует."
   - НЕ ДОДУМЫВАЙ: Не используй "общие знания". Только текст из блока КОНТЕКСТ.
   - НЕ упоминай названия файлов (source), используй только смысловые ссылки на пункты/статьи.
"""

        
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            stream=stream
        )
        
        if stream:
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            return response.choices[0].message.content

    def check_need_clarification(self, query, history):
        # Format history
        history_str = ""
        for msg in history[-5:]: # Last 5 messages
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_str += f"{role}: {msg['content']}\\n"
            
        prompt = f"""
        Ты - умный маршрутизатор диалога для юридического ассистента по Госимуществу РК.
        
        ВАЖНО: По умолчанию всегда считай, что речь идет о ГОСУДАРСТВЕННОМ имуществе (не частном). Не переспрашивай это.
        
        Твоя задача:
        1. Проанализировать последний запрос пользователя с учетом истории диалога.
        2. Проверить КРИТЕРИИ ДОСТАТОЧНОСТИ информации (Miro Rules):
           - Если тема "ПЕРЕДАЧА": Нужно знать уровни отправителя и получателя (Республиканский, Областной, Районный, Сельский). Минимум одна сторона должна быть коммунальной. Если непонятно кто кому передает -> needs_clarification: true.
           - Если тема "СПИСАНИЕ" или "ВЫБЫТИЕ": Нужно знать ТИП имущества (Недвижимость, Биологические активы, или Основные средства/Машины). Если просто "как списать имущество?" -> needs_clarification: true.
           - Если тема "АРЕНДА": Нужно знать ТИП (Общий случай, Неиспользуемое госимущество, или Водохозяйственные сооружения).
        
        3. Если критерии НЕ соблюдены -> Сформулируй уточняющий вопрос (clarification_question).
        4. Если критерии соблюдены ИЛИ вопрос общий (о наличии ставок, правил) -> needs_clarification: false.
        5. Если пользователь спрашивает о НАЛИЧИИ правил, ставок, процедур (например "есть ли ставки?", "как списать?"), НЕ нужно уточнять детали. Считай это поисковым запросом.
        6. Создай self-contained поисковый запрос (rewritten_query).
        
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

    def generate_hyde_doc(self, query):
        prompt = f"""
        Ты - эксперт по госимуществу РК.
        Напиши ГИПОТЕТИЧЕСКИЙ (вымышленный), но юридически правдоподобный ответ на вопрос:
        "{query}"
        
        Не пытайся ответить точно, просто используй правильную терминологию, названия процедур и структуру, которую ты ожидаешь увидеть в реальном документе.
        Ответ должен быть на русском языке.
        """
        try:
            response = client.chat.completions.create(
                model=GROK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7 
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"HyDE error: {e}")
            return query

    def self_correct(self, query, response, context_items):
        context_str = "\\n".join([item['content'] for item in context_items])
        
        prompt = f"""
        Ты - строгий критик (Auditor). Твоя задача проверить ответ ассистента на соответствие контексту.
        
        Вопрос: {query}
        
        Контекст:
        {context_str[:15000]}
        
        Ответ ассистента:
        {response}
        
        Задание:
        1. Проверь, не содержит ли ответ галлюцинаций (фактов, которых нет в контексте).
        2. Если ответ верный и подтверждается контекстом -> верни только слово "OK" (без кавычек и пояснений).
        3. Если есть ошибки или выдумки -> верни ИСПРАВЛЕННУЮ версию ответа. НЕ ПИШИ "Анализ" или "Исправленная версия". Просто верни готовый текст ответа так, как он должен выглядеть для пользователя.
        """
        
        try:
            res = client.chat.completions.create(
                model=GROK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = res.choices[0].message.content
            if "OK" in content[:10]:
                return response # Return original if OK
            else:
                print("Self-Correction Triggered: Rewriting response.")
                return content # Return corrected version
        except Exception as e:
            print(f"Self-correction error: {e}")
            return response

    def retrieve(self, query, category, use_hyde=False):
        search_text = query
        if use_hyde:
            print("Generating HyDE document...")
            hyde_doc = self.generate_hyde_doc(query)
            print(f"HyDE Doc: {hyde_doc[:100]}...")
            search_text = hyde_doc

        # 1. Broad Retrieval (Get more candidates)
        initial_k = 150
        candidates = []
        
        # Search Specific Category
        if category != "Общий":
            res_cat = self.npa_collection.query(
                query_texts=[search_text],
                n_results=initial_k,
                where={"category": category}
            )
            candidates.extend(self._format_results(res_cat))
            
            res_instr = self.instr_collection.query(
                query_texts=[search_text],
                n_results=initial_k,
                where={"category": category}
            )
            candidates.extend(self._format_results(res_instr))
            
        # Search Global Fallback (catch-all for misclassified docs or cross-category info)
        # This is critical because some docs might be in specific folders but relevant to other queries.
        res_global = self.npa_collection.query(
            query_texts=[search_text],
            n_results=initial_k,
            # No 'where' clause -> search everything
        )
        candidates.extend(self._format_results(res_global))
        
        # Deduplicate candidates
        # Deduplicate candidates (preserve best distance)
        unique_candidates = {}
        for c in candidates:
            # If doc already exists, keep the one with lower distance (if available)
            if c['content'] not in unique_candidates:
                unique_candidates[c['content']] = c
            else:
                if c['distance'] and unique_candidates[c['content']]['distance']:
                    if c['distance'] < unique_candidates[c['content']]['distance']:
                         unique_candidates[c['content']] = c
        
        candidates = list(unique_candidates.values())
        
        # SORT by distance (Ascending: Lower is better for L2/Euclidean)
        candidates.sort(key=lambda x: x.get('distance', 1.0) or 1.0)

        if not candidates:
            return []

        # 2. Re-ranking
        # Return Top K without re-ranking
        return candidates[:5]

    def run(self, query, history=[], use_hyde=False, use_self_correction=True, stream=False):
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
        
        # 2. Retrieval (with optional HyDE)
        context = self.retrieve(search_query, category, use_hyde=use_hyde)
        
        # 3. Generation & Self-Correction Logic
        # If Self-Correction is ON, we cannot stream the initial generation to the user,
        # because we need to validate it first.
        if use_self_correction and context:
            print("Self-Correction Enabled: Buffering initial response...")
            # Generate FULL response (no stream)
            initial_response_gen = self.generate_response(search_query, context, stream=True)
            initial_response = "".join([chunk for chunk in initial_response_gen])
            
            print("Running Self-Correction...")
            final_response = self.self_correct(search_query, initial_response, context)
            
            # If the user wants a stream, we fake-stream the final corrected response
            if stream:
                def fake_stream(text):
                    # Yield words or small chunks
                    words = text.split(' ')
                    for word in words:
                        yield word + " "
                
                return {
                    "response": fake_stream(final_response),
                    "category": category,
                    "context": context
                }
            else:
                return {
                    "response": final_response,
                    "category": category,
                    "context": context
                }
        else:
            # Normal streaming (or not)
            response = self.generate_response(search_query, context, stream=stream)
            
            return {
                "response": response,
                "category": category,
                "context": context
            }
