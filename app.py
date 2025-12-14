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
            with st.spinner("Анализирую НПА..."):
                # Pass history excluding the current new message
                result = agent.run(prompt, history=st.session_state.messages[:-1]) 
                response = result["response"]
                context = result["context"]
                category = result["category"]
                
                final_response = f"**Категория:** {category}\n\n{response}"
                
                st.markdown(final_response)
                with st.expander("Источники"):
                     for item in context:
                        st.markdown(f"**{item['metadata'].get('source')}**")
                        st.caption(item['metadata'].get('full_context', ''))
                        st.text(item['content'][:200] + "...")
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": final_response,
            "context": context
        })

if __name__ == "__main__":
    main()
