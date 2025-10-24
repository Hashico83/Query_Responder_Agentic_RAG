🧠 **Query Responder — Agentic RAG System**

A modular, production-ready framework for agent-driven document intelligence.

🚀 **Overview**

Query Responder is an Agentic Retrieval-Augmented Generation (RAG) system built end-to-end — combining a React + Vite frontend, a Flask backend, and a ChromaDB vector store with HuggingFace embeddings and local or remote LLM integration (Ollama, OpenAI, Claude, or Gemini).

This was creaeted as part of a vibe coding challenge. While the choice was to use a complete no code platform as per the coding challenge, I took the less troden path of using chat assists to develop the code while defining the functionality of the components myself. This helped me to be in better control.

Simply put, its an ecosystem of agents, utilizing a RAG mechanism to find the response of a query posted by the user. If the agents reason that the response it is not satisfactory, it enquires the user whether the information can be obtained from the internet and if yes, gathers the same using SerperDev.

🧩 Core Components
Folder Description
frontend/-- React + Vite app for the chat UI. Displays conversation history, user input, and model responses with source attributions.

backend/-- Flask API implementing the complete agentic RAG orchestration logic (LLM + retrieval + synthesis).

Endpoints:
• POST /api/query — full RAG + agent pipeline
• POST /api/feedback — collects user feedback
• GET /health — service health check
ingestion-pipeline/ Scripts to process and embed your documents into ChromaDB. Handles chunking, metadata tagging, and vector persistence.
reference-docs/ Folder for your internal knowledge base (PDFs, DOCX, HTML, TXT, etc).
ingestion-pipeline/chroma_db_data/ Local persisted ChromaDB vector store.

🧠 Agentic RAG Flow — How It Works
1️⃣ Ingest Knowledge

Place documents in reference-docs/.

Run ingestion-pipeline/ingest_docs.py.

Reads supported formats (PDF, DOCX, HTML, TXT, etc.)

Splits documents into overlapping chunks

Generates embeddings via HuggingFace

Persists embeddings + metadata in ChromaDB

2️⃣ Receive a Query

The frontend sends the user query to POST /api/query.

The backend logs and processes it via the agent decision flow.

3️⃣ Agentic Orchestration (Backend Intelligence)

The backend implements a multi-stage reasoning agent orchestrated in app.py:

**Stage Description**

_Planner / Decision Layer_ Determines whether the query is clear, ambiguous, or requires clarification. Handles multi-turn context and permission for web search.
_Retriever_ Performs semantic search on ChromaDB (vector similarity) to fetch top-k relevant document chunks.
_Relevance Grader_ Uses the LLM to evaluate whether the retrieved context is sufficiently related to the question.
_Synthesizer_ Builds a contextual prompt and calls the configured LLM (Ollama / OpenAI / Claude / Gemini) to generate a grounded answer.

_Verifier_ Optionally cross-checks synthesized answer with retrieved context to detect contradictions or low confidence.
_Rephraser / Finetuner_ Refines the final response using FINETUNE_RESPONSE_PROMPT_TEMPLATE for coherence and tone consistency.
4️⃣ Response Construction

The agent returns a structured JSON payload:

{
"query": "user question",
"response": "generated answer",
"source": "Agent + Internal Docs",
"sources": [
{ "filename": "policy.pdf", "score": 0.91, "snippet": "..." }
]
}

The frontend displays the result with citations and conversation history.

🧠 Supported LLM Providers

The backend dynamically loads the LLM based on configuration in config.py:

Provider Backend Class Example Models
Ollama ChatOllama Mistral, Llama3, Phi3, etc.
OpenAI ChatOpenAI gpt-4o, gpt-4o-mini
Claude ChatAnthropic Claude-3.5-Sonnet, Claude-3.5-Haiku
Gemini ChatGoogleGenerativeAI gemini-1.5-pro, gemini-flash

All providers can be toggled via config.ACTIVE_LLM_PROVIDER.

⚙️ **Tech Stack**

_Frontend_ - React + Vite + Tailwind
_Backend_- Flask + LangChain
_Vector DB_ ChromaDB
_Embeddings_ HuggingFace (sentence-transformers)
LLM Integration Ollama / OpenAI / Claude / Gemini
_Search Tool (Optional)_ Google Serper API for web augmentation
✅ What’s Implemented

🔹 Full agentic decision flow (planner → retriever → synthesizer → verifier → rephraser)

🔹 LLM integration through LangChain abstraction (multi-provider support)

🔹 Multi-turn conversation memory via lightweight session store

🔹 Confidence and relevance checks

🔹 Web search fallback via Serper API

🔹 Feedback loop (/api/feedback) to record user satisfaction

🔹 Frontend integration with full async query/response flow

🚦 **Quick Start**
Prerequisites

Python 3.8+

Node.js 16+

pip and npm

(Optional) API keys for OpenAI / Anthropic / Google / Serper

Run Locally

# 1. Install backend dependencies

cd backend
pip install -r requirements.txt

# 2. Start the backend

python app.py

# 3. Install and run frontend

cd ../frontend
npm install
npm run dev

Default ports:

Frontend → http://localhost:5173

Backend → http://localhost:5001

🧭 Recommended Configuration (config.py)
ACTIVE_LLM_PROVIDER = "ollama" # or "openai", "claude", "gemini"
OLLAMA_MODEL_NAME = "mistral"
CHROMA_PERSIST_DIR = "./ingestion-pipeline/chroma_db_data"
CHROMA_COLLECTION_NAME = "local_docs"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SERPER_API_KEY = "your-serper-key"
