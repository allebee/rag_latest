import streamlit as st
import os
from src.agent import Agent
from src.ingestion import ingest_data

st.set_page_config(page_title="AI консультант по госимуществу", layout="wide")

@st.cache_resource
def get_agent():
    return Agent()

def main():
    st.title("🏛️ AI Консультант по госимуществу")
    
    agent = get_agent()

    # Sidebar
    with st.sidebar:
        st.header("Управление")
        if st.button("Обновить Базу Знаний"):
            with st.spinner("Идет индексация документов..."):
                try:
                    ingest_data()
                    st.success("База знаний обновлена!")
                    # Clear cache to reload DB connection if needed
                    st.cache_resource.clear()
                except Exception as e:
                    st.error(f"Ошибка: {e}")
        
        st.markdown("---")
        st.markdown("**Категории:**")
        st.markdown("- Передача")
        st.markdown("- Дарение")
        st.markdown("- Списание")
        st.markdown("- Аренда")
        st.markdown("- Приватизация")
        st.markdown("- Эффективность управления")

        st.markdown("**Настройки поиска:**")
        use_hyde = st.checkbox("Гипотетический документ (HyDE)", value=False, help="Генерирует идеальный ответ для поиска, улучшает поиск при сложных запросах.")
        # Self-Correction is now always ON by default
        
    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "context" in message:
                with st.expander("Источники"):
                    for item in message["context"]:
                        st.markdown(f"**{item['metadata'].get('source')}**")
                        st.caption(item['metadata'].get('full_context', ''))
                        st.text(item['content'][:200] + "...")

    if prompt := st.chat_input("Задайте ваш вопрос по госимуществу..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Placeholder for streaming
            stream_container = st.empty()
            
            # Pass history excluding the current new message
            # Enable streaming mode
            result = agent.run(
                prompt, 
                history=st.session_state.messages[:-1],
                use_hyde=use_hyde,
                use_self_correction=True, # Always ON
                stream=True
            ) 
            
            response_generator = result["response"]
            context = result["context"]
            category = result["category"]
            
            # Use Streamlit's write_stream
            # Note: response_generator can be a string (if clarification) or a generator
            
            full_response = ""
            
            if isinstance(response_generator, str):
                full_response = response_generator
                st.markdown(f"**Категория:** {category}\n\n{full_response}")
            else:
                # Show category first
                st.markdown(f"**Категория:** {category}")
                
                # Stream the rest
                full_response = st.write_stream(response_generator)

            # Re-construct final text for history
            final_text_for_history = f"**Категория:** {category}\n\n{full_response}"

            with st.expander("Источники"):
                    for item in context:
                        st.markdown(f"**{item['metadata'].get('source')}**")
                        st.caption(item['metadata'].get('full_context', ''))
                        st.text(item['content'][:200] + "...")
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": final_text_for_history,
            "context": context
        })

if __name__ == "__main__":
    main()
