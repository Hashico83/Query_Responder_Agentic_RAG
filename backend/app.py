import os
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

import config
from prompt_library import (
    RAG_PROMPT_TEMPLATE,
    AGENT_TOOL_ROUTER_PROMPT,
    WEB_SYNTHESIS_PROMPT_TEMPLATE,
    RELEVANCE_GRADER_PROMPT,
    CLARIFICATION_PROMPT,
    FINETUNE_RESPONSE_PROMPT_TEMPLATE,
    REPHRASE_PROMPT # --- FIX: Import the new rephrase prompt ---
)

app = Flask(__name__)
CORS(app)

# --- Global RAG/Agent Components ---
vectorstore = None
llm = None
embedding_model = None
serper_search = None
rag_components_initialized = False
session_store = {}

rag_agent_flow = None


# --- LLM Initialization Helper Function ---
def _initialize_llm(provider: str):
    """Initializes the LLM based on the provider specified in config.py."""
    if not provider:
        raise ValueError("No LLM provider specified in config.py")

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Initializing LLM from provider: {provider}...", flush=True)

    match provider:
        case "ollama":
            return ChatOllama(
                base_url=config.OLLAMA_BASE_URL,
                model=config.OLLAMA_MODEL_NAME,
                temperature=0.0
            )
        case "openai":
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set in config.py")
            os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
            return ChatOpenAI(
                model_name=config.OPENAI_MODEL_NAME,
                temperature=0.0
            )
        case "gemini":
            if config.GEMINI_API_KEY == "Dummy to be updated" or not config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set in config.py")
            os.environ["GOOGLE_API_KEY"] = config.GEMINI_API_KEY
            return ChatGoogleGenerativeAI(
                model=config.GEMINI_MODEL_NAME,
                temperature=0.0
            )
        case "claude":
            if not config.CLAUDE_API_KEY:
                raise ValueError("CLAUDE_API_KEY not set in config.py")
            os.environ["ANTHROPIC_API_KEY"] = config.CLAUDE_API_KEY
            return ChatAnthropic(
                model_name=config.CLAUDE_MODEL_NAME,
                temperature=0.0
            )
        case _:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# --- TOOLS for the Agent ---
def retrieve_from_docs(query: str) -> tuple[str, list]:
    
    """
    Searches the db, filters chunks by a score threshold, then returns the combined content.
    """
    if not vectorstore:
        return "Error: Document database not initialized.", []

    try:
        # Step 1: Retrieve a broad set of initial chunks (k=8)
        initial_chunks = vectorstore.similarity_search_with_score(query, k=8)
        
        # --- NEW LOGIC: Filter out chunks with a distance score > 0.7 ---
        filtered_chunks = []
        for doc, score in initial_chunks:
            if score <= 0.7:
                filtered_chunks.append((doc, score))

        print(f"--- Retrieved {len(initial_chunks)} chunks, kept {len(filtered_chunks)} after filtering with score <= 0.7 ---", flush=True)

        # If no chunks meet the score threshold, return "not found"
        if not filtered_chunks:
            return "No relevant documents found that meet the quality threshold.", []
        
        # --- NEW: Print block to inspect the final chunks under consideration ---
        print("\n" + "="*50, flush=True)
        print(f"--- INSPECTING {len(filtered_chunks)} FINAL CHUNKS FOR CONTEXT ---", flush=True)
        for i, (chunk_document, chunk_score) in enumerate(filtered_chunks):
            print(f"\n--- FINAL CHUNK {i+1} ---", flush=True)
            print(f"DISTANCE SCORE: {chunk_score:.4f}", flush=True) # Formatted for readability
            print("CONTENT:", flush=True)
            print(chunk_document.page_content, flush=True)
        print("\n" + "="*50, flush=True)
        # --- End of new print block ---

        # --- FIX: Create a new list containing only the Document objects ---
        final_document_list = [doc for doc, score in filtered_chunks]

        # Step 3: Build the final context from the high-quality list of documents
        context_text = "\n\n---\n\n".join([doc.page_content for doc in final_document_list])
        sources = list(set([doc.metadata.get('source', 'N/A') for doc in final_document_list]))

        return context_text, sources
    except Exception as e:
        print(f"Error in retrieve_from_docs: {e}", flush=True)
        traceback.print_exc()
        return f"Error during local document retrieval: {e}", []

def check_exact_match(query: str) -> Optional[tuple[str, list]]:
    """
    Performs a simple keyword-based search for a near-exact match of the query.
    This is a fast check to bypass the LLM for simple Q&A.
    """
    if not vectorstore:
        return None
    try:
        
        # --- NEW LOGIC: Retrieve top 2 chunks ---
        docs_with_score = vectorstore.similarity_search_with_score(query, k=3)

        # --- CODE BLOCK FOR INSPECTING THE CHUNKS ---
        
        print("\n" + "="*50, flush=True)
        print(f"--- INSPECTING {len(docs_with_score)} RETRIEVED CHUNKS ---", flush=True)
        for i, (chunk_document, chunk_score) in enumerate(docs_with_score):
            print(f"\n--- CHUNK {i+1} ---", flush=True)
            print(f"DISTANCE SCORE: {chunk_score}", flush=True)
            print("CONTENT:", flush=True)
            print(chunk_document.page_content, flush=True)
        print("\n" + "="*50, flush=True)
        
        # --- END OF NEW CODE BLOCK ---
        
        
        # --- NEW LOGIC: Retrieve top 3 chunks ---
        docs_with_score = vectorstore.similarity_search_with_score(query, k=3)

        # --- NEW LOGIC: Loop through the chunks and check their scores individually ---
        for i, (doc, score) in enumerate(docs_with_score):
            print(f"--- Exact match check: Chunk {i+1} score is {score:.4f} ---", flush=True)
            # If any chunk has a score less than 0.5, trigger success and stop checking.
            if score < 0.7:
                print(f"--- Score is < 0.7. Triggering high-confidence RAG flow. ---", flush=True)
                # This function now acts only as a trigger.
                return "trigger_success", []
            
        # If the loop completes and no chunk met the condition, return None.
        return None
    except Exception as e:
        print(f"Error in check_exact_match: {e}", flush=True)
        traceback.print_exc()
        return None

def search_web(query: str) -> str:
    """
    Performs a web search using Google Serper API and returns a summary of the results.
    """
    if not serper_search:
        return "Error: Web search tool not initialized."
    try:
        search_results = serper_search.run(query)
        return search_results
    except Exception as e:
        print(f"Error in search_web: {e}", flush=True)
        traceback.print_exc()
        return f"Error performing web search: {e}"

def check_relevance(question: str, context: str) -> bool:
    """
    Uses the LLM to grade whether a retrieved context is relevant to the question.
    """
    if not llm:
        return False

    try:
        relevance_chain = RELEVANCE_GRADER_PROMPT | llm | StrOutputParser()
        grade = relevance_chain.invoke({"question": question, "context": context})
        is_relevant = grade.strip().lower().startswith("yes")
        return is_relevant
    except Exception as e:
        print(f"Error during relevance check: {e}", flush=True)
        traceback.print_exc()
        return False

def check_for_ambiguity(query: str) -> Optional[str]:
    """
    Uses the LLM to check if a query contains ambiguous pronouns or phrases.
    Returns a clarification question or 'clear'.
    """
    if not llm:
        return None
    try:
        ambiguity_chain = CLARIFICATION_PROMPT | llm | StrOutputParser()
        response = ambiguity_chain.invoke({"question": query})
        if response and response.strip().lower() == "clear":
            return "clear"
        elif response:
            return response
        return None
    except Exception as e:
        print(f"Error checking for ambiguity: {e}", flush=True)
        traceback.print_exc()
        return None
    
# --- NEW: Function to finalize bypassed responses ---
def finalize_exact_match_response(query: str, response_context: str) -> str:
    """
    Uses the LLM to rephrase a direct-hit response to make it more coherent
    and directly answer the user's query, without adding new info.
    """
    if not llm:
        print("Warning: LLM not initialized, returning raw content for exact match.", flush=True)
        return response_context

    try:
         # --- FIX: Added a print statement to inspect the chunk content ---
        print("\n" + "="*50, flush=True)
        print("--- CHUNK CONTENT BEING SENT FOR REPHRASING ---", flush=True)
        print(response_context, flush=True)
        print("="*50 + "\n", flush=True)
        # --- End of fix ---

        # Create a dictionary with the inputs for the prompt
        prompt_inputs = {
            "question": query,
            "response_context": response_context
        }

        rephrase_chain = FINETUNE_RESPONSE_PROMPT_TEMPLATE | llm | StrOutputParser()
        final_answer = rephrase_chain.invoke(prompt_inputs)
        return final_answer
    except Exception as e:
        print(f"Error during final rephrasing of exact match: {e}", flush=True)
        traceback.print_exc()
        # Fallback to returning the original content if rephrasing fails
        return response_context


# --- AGENT ORCHESTRATION ---
# def agent_decision_flow(input_query: str, session_id: str) -> tuple[str, str, list]:
    """
    Orchestrates the agent's decision-making and tool execution.
    This function handles multi-turn conversations and conditional logic.
    """
    try:
        print(f"\n{'='*50}\nAGENT THOUGHT PROCESS START\n{'='*50}", flush=True)

        session_state = session_store.get(session_id, {})
        last_agent_action = session_state.get('last_agent_action')
        last_query = session_state.get('last_query')

        # Multi-turn logic for web permission
        if last_agent_action == "awaiting_web_permission":
            if input_query.lower() in ["yes", "y", "sure", "ok"]:
                print(f"User affirmed web search. Executing web search...", flush=True)
                tool_output = search_web(last_query)
                final_prompt = WEB_SYNTHESIS_PROMPT_TEMPLATE
                final_input = {"question": last_query, "search_results": tool_output}
                source_label = "Agent + Web Search"
                session_store.pop(session_id, None)
                
                final_response_chain = final_prompt | llm | StrOutputParser()
                final_answer = final_response_chain.invoke(final_input)
                return final_answer, source_label, []
            else:
                session_store.pop(session_id, None)
                return "Understood. I will not perform a web search at this time.", "Agent Response", []

        # --- FIX: Re-architected the ambiguity and clarification flow ---
        # If the agent is waiting for clarification...
        if last_agent_action == "awaiting_clarification":
            print(f"--- User provided clarification: '{input_query}'. Rephrasing original query. ---", flush=True)
            # Use an LLM call to intelligently merge the original question and the new detail
            rephrase_chain = REPHRASE_PROMPT | llm | StrOutputParser()
            print(f"--- The last query is {last_query}")
            print(f"--- The input query is {input_query}")
            new_query = rephrase_chain.invoke({
                "original_question": last_query,
                "clarification_detail": input_query
            })
            print(f"--- Rephrased Query: {new_query} ---", flush=True)
            input_query = new_query # This updated query will now be used for the rest of the flow
            session_store.pop(session_id, None) # Clear the session state
        else:
            # For all other new queries, check for ambiguity first.
            ambiguity_check = check_for_ambiguity(input_query)
            if ambiguity_check and ambiguity_check != "clear":
                # The question is ambiguous, so ask the user for more information
                print(f"--- Query is ambiguous. Asking for clarification: '{ambiguity_check}' ---", flush=True)
                session_store[session_id] = {
                    'last_agent_action': 'awaiting_clarification',
                    'last_query': input_query, # Store the original ambiguous query
                }
                return ambiguity_check, "Agent (Clarification)", []

        # Main RAG flow starts here
        exact_match_response = check_exact_match(input_query)
        if exact_match_response:
            content, sources = exact_match_response
            print("--- Exact match found. Rephrasing response for coherence. ---", flush=True)
            # Call the new function to rephrase the content
            final_answer = finalize_exact_match_response(input_query, content)
            # --- FIX: Return the rephrased 'final_answer', not the raw 'content' ---
            return final_answer, "Agent (Exact Match Rephrased)", sources

        tool_output, sources = retrieve_from_docs(input_query)
        
        local_search_successful = False
        if "Error" not in tool_output and "No relevant documents" not in tool_output:
            if check_relevance(input_query, tool_output):
                local_search_successful = True
        
        if local_search_successful:
            final_prompt = RAG_PROMPT_TEMPLATE
            final_input = {"context": tool_output, "question": input_query}
            source_label = "Agent + Internal Docs"
            final_response_chain = final_prompt | llm | StrOutputParser()
            final_answer = final_response_chain.invoke(final_input)
            return final_answer, source_label, sources
        else:
            print(f"\n--- Fallback Triggered: Local docs insufficient, asking user for permission to search web ---", flush=True)
            
            session_store[session_id] = {
                'last_agent_action': 'awaiting_web_permission',
                'last_query': input_query
            }
            
            permission_question = "I couldn't find a good answer in the available documents. Would you like me to search the web for you? (yes/no)"
            return permission_question, "Agent (Multi-turn)", []

    except Exception as e:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR: An unhandled exception occurred in agent flow: {e}", flush=True)
        traceback.print_exc()
        return f"An internal agent error occurred: {e}", "System Error", []

# --- AGENT ORCHESTRATION ---
def agent_decision_flow(input_query: str, session_id: str) -> tuple[str, str, list]:
    """
    Orchestrates the agent's decision-making and tool execution.
    This function handles multi-turn conversations and conditional logic.
    """
    try:
        print(f"\n{'='*50}\nAGENT THOUGHT PROCESS START\n{'='*50}", flush=True)

        session_state = session_store.get(session_id, {})
        last_agent_action = session_state.get('last_agent_action')
        last_query = session_state.get('last_query')

        # Multi-turn logic for web permission
        if last_agent_action == "awaiting_web_permission":
            if input_query.lower() in ["yes", "y", "sure", "ok"]:
                print(f"User affirmed web search. Executing web search...", flush=True)
                tool_output = search_web(last_query)
                final_prompt = WEB_SYNTHESIS_PROMPT_TEMPLATE
                final_input = {"question": last_query, "search_results": tool_output}
                source_label = "Agent + Web Search"
                session_store.pop(session_id, None)
                
                final_response_chain = final_prompt | llm | StrOutputParser()
                final_answer = final_response_chain.invoke(final_input)
                return final_answer, source_label, []
            else:
                session_store.pop(session_id, None)
                return "Understood. I will not perform a web search at this time.", "Agent Response", []

        # Re-architected the ambiguity and clarification flow
        if last_agent_action == "awaiting_clarification":
            print(f"--- User provided clarification: '{input_query}'. Rephrasing original query. ---", flush=True)
            rephrase_chain = REPHRASE_PROMPT | llm | StrOutputParser()
            new_query = rephrase_chain.invoke({
                "original_question": last_query,
                "clarification_detail": input_query
            })
            print(f"--- Rephrased Query: {new_query} ---", flush=True)
            input_query = new_query
            session_store.pop(session_id, None)
        else:
            ambiguity_check = check_for_ambiguity(input_query)
            if ambiguity_check and ambiguity_check != "clear":
                print(f"--- Query is ambiguous. Asking for clarification: '{ambiguity_check}' ---", flush=True)
                session_store[session_id] = {
                    'last_agent_action': 'awaiting_clarification',
                    'last_query': input_query,
                }
                return ambiguity_check, "Agent (Clarification)", []

        # --- NEW HYBRID LOGIC ---
        # First, check for a high-confidence trigger.
        exact_match_response = check_exact_match(input_query)
        if exact_match_response:
            # The trigger was successful. Now, gather a WIDER context to formulate a rich answer.
            print("--- High-confidence trigger found. Gathering broader context for a comprehensive answer. ---", flush=True)
            
            # 1. Retrieve the top 4 chunks using the main retrieval function.
            context_text, sources = retrieve_from_docs(input_query)
            
            # 2. Check if the retrieved context is valid.
            if "Error" in context_text or "No relevant documents" in context_text:
                 # Fallback if retrieval fails for some reason
                 return "I found a potential match but was unable to retrieve the full context.", "System Error", []

            # 3. Use the main RAG prompt to synthesize an answer from the multi-chunk context.
            final_prompt = RAG_PROMPT_TEMPLATE
            final_input = {"context": context_text, "question": input_query}
            source_label = "Agent (High-Confidence RAG)" # New label for this path
            
            final_response_chain = final_prompt | llm | StrOutputParser()
            final_answer = final_response_chain.invoke(final_input)
            
            return final_answer, source_label, sources

        # --- This is now the fallback path if the high-confidence trigger is NOT met ---
        print("--- No high-confidence trigger. Proceeding with standard RAG flow. ---", flush=True)
        tool_output, sources = retrieve_from_docs(input_query)
        
        local_search_successful = False
        if "Error" not in tool_output and "No relevant documents" not in tool_output:
            if check_relevance(input_query, tool_output):
                local_search_successful = True
        
        if local_search_successful:
            final_prompt = RAG_PROMPT_TEMPLATE
            final_input = {"context": tool_output, "question": input_query}
            source_label = "Agent + Internal Docs"
            final_response_chain = final_prompt | llm | StrOutputParser()
            final_answer = final_response_chain.invoke(final_input)
            return final_answer, source_label, sources
        else:
            print(f"\n--- Fallback Triggered: Local docs insufficient, asking user for permission to search web ---", flush=True)
            
            session_store[session_id] = {
                'last_agent_action': 'awaiting_web_permission',
                'last_query': input_query
            }
            
            permission_question = "I couldn't find a good answer in the available documents. Would you like me to search the web for you? (yes/no)"
            return permission_question, "Agent (Multi-turn)", []

    except Exception as e:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR: An unhandled exception occurred in agent flow: {e}", flush=True)
        traceback.print_exc()
        return f"An internal agent error occurred: {e}", "System Error", []

def initialize_rag_components():
    """Initializes all necessary RAG/Agent components."""
    global vectorstore, llm, embedding_model, serper_search, rag_agent_flow, rag_components_initialized

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Initializing RAG/Agent components...", flush=True)
    
    try:
        llm = _initialize_llm(config.ACTIVE_LLM_PROVIDER)
        if hasattr(llm, 'model_name'):
             llm_model_name = llm.model_name
        else:
            llm_model_name = config.OLLAMA_MODEL_NAME

        test_response = llm.invoke("Hello.")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - LLM '{llm_model_name}' connected. Test response: '{test_response.content[:50]}...'", flush=True)
    except Exception as e:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR: Could not initialize LLM from provider: {e}", flush=True)
        traceback.print_exc()
        return False
        
    try:
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': True}
        embedding_model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Embedding model '{config.EMBEDDING_MODEL_NAME}' loaded successfully.", flush=True)
    except Exception as e:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR: Could not load embedding model: {e}", flush=True)
        traceback.print_exc()
        return False

    try:
        if not os.path.exists(config.CHROMA_PERSIST_DIR):
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - WARNING: ChromaDB persistence directory not found: {config.CHROMA_PERSIST_DIR}. Please run the ingestion pipeline first.", flush=True)
            return False
        vectorstore = Chroma(
            persist_directory=config.CHROMA_PERSIST_DIR,
            embedding_function=embedding_model,
            collection_name=config.CHROMA_COLLECTION_NAME
        )
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ChromaDB collection '{config.CHROMA_COLLECTION_NAME}' loaded.", flush=True)
        if vectorstore._collection.count() == 0:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - WARNING: ChromaDB collection is empty. RAG will not find internal documents.", flush=True)
    except Exception as e:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR: Could not initialize ChromaDB: {e}", flush=True)
        traceback.print_exc()
        return False

    try:
        if not config.SERPER_API_KEY:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - WARNING: SERPER_API_KEY not set in config.py. Web search will be disabled.", flush=True)
            serper_search = None
        else:
            os.environ["SERPER_API_KEY"] = config.SERPER_API_KEY
            serper_search = GoogleSerperAPIWrapper()
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Serper API Wrapper initialized.", flush=True)
    except Exception as e:
        print(f"{datetime.now().strftime('%Y-%m-%d %M:%S')} - ERROR: Could not initialize Serper API Wrapper: {e}", flush=True)
        traceback.print_exc()
        return False

    global rag_agent_flow
    rag_agent_flow = agent_decision_flow
    
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Agent-driven RAG flow constructed successfully.", flush=True)
    rag_components_initialized = True
    return True


# --- Flask Routes ---
@app.route('/api/query', methods=['POST'])
def handle_query():
    """Handles incoming user queries by performing RAG."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query field in request body'}), 400
        user_query = data['query']
        session_id = request.remote_addr # Using IP for session, consider a more robust method for production
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Received query: '{user_query}' for session: {session_id}", flush=True)

        if not rag_components_initialized or not rag_agent_flow:
            return jsonify({
                "response": "Backend not fully initialized. Check server logs.",
                "query": user_query,
                "source": "System Error",
                "sources": []
            }), 500

        llm_response, source_label, sources = rag_agent_flow(user_query, session_id)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Final generated response for '{user_query}': '{llm_response[:100]}...' (Source: {source_label})", flush=True)

        return jsonify({
            'response': llm_response.strip(),
            'query': user_query,
            'source': source_label,
            'sources': sources
        }), 200

    except Exception as e:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR: An unexpected error occurred: {e}", flush=True)
        traceback.print_exc()
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'query': request.get_json().get('query', 'N/A'),
            'source': 'System Error',
            'sources': []
        }), 500

@app.route('/api/feedback', methods=['POST'])
def handle_feedback():
    """Handles feedback from the user and stores it in a JSON file."""
    try:
        data = request.get_json()
        if not data or 'query' not in data or 'response' not in data or 'liked' not in data:
            return jsonify({'error': 'Missing fields in feedback data'}), 400

        feedback_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': "dummy_user_id",
            'query': data['query'],
            'response': data['response'],
            'liked': data['liked']
        }

        feedback_file_path = "feedback_history.json"
        
        if os.path.exists(feedback_file_path):
            with open(feedback_file_path, 'r') as f:
                history = json.load(f)
        else:
            history = []

        history.append(feedback_data)
        
        with open(feedback_file_path, 'w') as f:
            json.dump(history, f, indent=4)

        return jsonify({'message': 'Feedback received successfully'}), 200
    
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while saving feedback: {e}", flush=True)
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the Flask application."""
    status = 'healthy'
    message = 'Query Responder RAG API is running.'
    if not rag_components_initialized:
        status = 'degraded'
        message = 'RAG/Agent components not initialized. Check backend logs for details.'
    return jsonify({
        'status': status,
        'service': 'Query Responder RAG API',
        'message': message,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'Welcome to the Query Responder RAG API (Agentic Phase 1)',
        'endpoints': {
            'POST /api/query': 'Submit a query and receive an agent-driven RAG/Web response',
            'GET /health': 'Health check endpoint',
            'GET /': 'API information'
        },
        'status': 'RAG/Agent components ' + ('initialized' if rag_components_initialized else 'NOT initialized')
    }), 200

if __name__ == '__main__':
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting Query Responder RAG API...", flush=True)
    initialize_rag_components()
    app.run(host='0.0.0.0', port=5001, debug=True)