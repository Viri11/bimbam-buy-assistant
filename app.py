import os
import time
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma

# Carga la API key desde el archivo .env (en local) o desde los "Secrets"/variables
# de entorno del servidor (cuando esté desplegado).
load_dotenv()

st.set_page_config(page_title="Asistente BimBam Buy", page_icon="🛍️")

DOCS_DIR = "docs"
DB_DIR = "chroma_db"


def get_api_key():
    """Busca la API key primero en variables de entorno (.env local)
    y si no la encuentra, en los 'Secrets' de Streamlit Cloud."""
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        return key
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        return None


@st.cache_resource(show_spinner="Cargando y procesando los documentos de políticas...")
def build_qa_chain():
    api_key = get_api_key()
    if not api_key:
        st.error(
            "No encontré la variable GOOGLE_API_KEY. "
            "Revisa tu archivo .env (en local) o los 'Secrets' configurados "
            "en Streamlit Community Cloud (en el servidor)."
        )
        st.stop()

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

    # Si ya existe una base vectorial guardada en disco, la reutilizamos en vez de
    # volver a procesar los PDFs (esto evita re-embeber todo cada vez que abres la app
    # y ayuda a no chocar con el límite gratuito de la API).
    if os.path.isdir(DB_DIR) and os.listdir(DB_DIR):
        vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    else:
        # 1. Cargar todos los PDFs que estén dentro de la carpeta docs/
        if not os.path.isdir(DOCS_DIR):
            st.error(f"No existe la carpeta '{DOCS_DIR}/'. Créala y coloca ahí tus PDFs.")
            st.stop()

        documents = []
        for filename in os.listdir(DOCS_DIR):
            if filename.lower().endswith(".pdf"):
                loader = PyPDFLoader(os.path.join(DOCS_DIR, filename))
                documents.extend(loader.load())

        if not documents:
            st.error(f"No encontré ningún PDF dentro de '{DOCS_DIR}/'. Agrega tus documentos ahí y recarga la app.")
            st.stop()

        # 2. Dividir los documentos en fragmentos pequeños (chunks) para poder buscarlos
        splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
        chunks = splitter.split_documents(documents)

        # 3. Convertir cada fragmento en un vector numérico (embedding) y guardarlo,
        # en lotes pequeños para no exceder el límite gratuito de la API (100 solicitudes/min).
        vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        batch_size = 20
        total_batches = (len(chunks) - 1) // batch_size + 1

        progress_bar = st.progress(0, text="Procesando documentos...")
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            while True:
                try:
                    vectorstore.add_documents(batch)
                    break
                except Exception as e:
                    if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                        st.info("Se alcanzó el límite gratuito de la API, esperando 60 segundos para continuar...")
                        time.sleep(60)
                    else:
                        raise
            current_batch = i // batch_size + 1
            progress_bar.progress(current_batch / total_batches, text=f"Procesando documentos... ({current_batch}/{total_batches})")
        progress_bar.empty()

    # 4. Modelo de lenguaje que genera las respuestas
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=api_key, temperature=0.2)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    return retriever, llm


def answer_question(retriever, llm, question):
    # 1. Buscar los fragmentos más relevantes para la pregunta
    relevant_docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in relevant_docs)

    # 2. Armar el prompt final con el contexto encontrado
    prompt_text = f"""Eres el asistente virtual oficial de BimBam Buy, un e-commerce multiplataforma
enfocado en la experiencia de compra digital ágil y segura.

Responde la pregunta del usuario ÚNICAMENTE con la información del contexto proporcionado,
que proviene de los documentos oficiales de políticas de la empresa.

Si la respuesta no está en el contexto, dilo claramente ("No cuento con esa información
en los documentos disponibles") y sugiere contactar a soporte. No inventes políticas
ni datos que no estén en el contexto.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""

    # 3. Pedirle al modelo que genere la respuesta
    response = llm.invoke(prompt_text)

    # El contenido puede venir como texto simple o como una lista de bloques
    # (algunas versiones de la API de Gemini devuelven bloques con metadatos extra).
    # Aquí nos quedamos solo con el texto real de la respuesta.
    raw_content = response.content
    if isinstance(raw_content, str):
        answer_text = raw_content
    else:
        answer_text = "".join(
            block.get("text", "")
            for block in raw_content
            if isinstance(block, dict) and block.get("type") == "text"
        )

    return answer_text, relevant_docs


# --- Interfaz de usuario ---

st.title("🛍️ Asistente Virtual — BimBam Buy")
st.caption("Pregúntame sobre políticas de reembolso, programa de afiliados, envíos y más.")

retriever, llm = build_qa_chain()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_question = st.chat_input("Escribe tu pregunta sobre las políticas de BimBam Buy...")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Buscando en los documentos..."):
            answer, source_docs = answer_question(retriever, llm, user_question)
            st.markdown(answer)

            with st.expander("📄 Fuentes consultadas"):
                for doc in source_docs:
                    source_name = os.path.basename(doc.metadata.get("source", "desconocido"))
                    page = doc.metadata.get("page", "N/A")
                    st.write(f"- **{source_name}**, página {page}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
