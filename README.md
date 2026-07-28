# 🛍️ Asistente Virtual de Políticas — BimBam Buy

Asistente virtual (chatbot con RAG) que permite a cualquier persona de la empresa **BimBam Buy**
(e-commerce multiplataforma enfocado en la experiencia de compra digital ágil y segura) consultar
en lenguaje natural las políticas internas de la empresa (reembolsos, programa de afiliados,
logística, soporte, etc.) a partir de documentos PDF oficiales.

## 🧠 Arquitectura

```
PDFs de políticas (docs/) 
      → se dividen en fragmentos (LangChain Text Splitter)
      → se convierten en vectores (Google Gemini Embeddings)
      → se guardan en una base vectorial (Chroma)
      → el usuario pregunta en la interfaz (Streamlit)
      → se buscan los fragmentos más relevantes
      → el modelo Gemini genera la respuesta usando solo esos fragmentos
```

**Tecnologías:** Python · LangChain · Google Gemini API · ChromaDB · Streamlit · Oracle Cloud Infrastructure (OCI)

## 📂 Estructura del proyecto

```
bimbam-buy-assistant/
├── app.py                # Aplicación principal (Streamlit + LangChain)
├── requirements.txt       # Librerías necesarias
├── .env.example           # Plantilla de variables de entorno
├── .gitignore
└── docs/                  # Coloca aquí tus PDFs de políticas
```

## ▶️ Cómo ejecutarlo en tu computadora

1. Clona este repositorio y entra a la carpeta:
   ```bash
   git clone <URL-de-tu-repo>
   cd bimbam-buy-assistant
   ```
2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # En Windows
   source venv/bin/activate     # En Mac/Linux
   pip install -r requirements.txt
   ```
3. Copia `.env.example` a `.env` y coloca tu API key de Gemini (obtenla gratis en
   [Google AI Studio](https://aistudio.google.com/app/apikey)):
   ```
   GOOGLE_API_KEY=tu_api_key_aqui
   ```
4. Coloca tus archivos PDF de políticas dentro de la carpeta `docs/`.
5. Ejecuta la app:
   ```bash
   streamlit run app.py
   ```
6. Se abrirá en tu navegador en `http://localhost:8501`.

## ☁️ Despliegue en Oracle Cloud Infrastructure (OCI)

Este proyecto se despliega en una **instancia Compute (VM) del Always Free Tier de OCI**,
donde se instala Python, se clona el repositorio y se ejecuta Streamlit exponiendo el puerto 8501.

> Instrucciones detalladas de despliegue en [`docs/DEPLOY_OCI.md`](docs/DEPLOY_OCI.md) *(agregar este archivo en la etapa de despliegue)*.

## 🎥 Demo en la nube

<!-- Reemplaza esta línea con tu captura de pantalla o video del agente corriendo en OCI -->
`[ Aquí va la imagen o video del asistente ejecutándose en OCI ]`

## ⚠️ Nota

Este proyecto fue desarrollado como práctica de un curso. Los documentos de políticas de
"BimBam Buy" son de carácter ilustrativo/ficticio.
