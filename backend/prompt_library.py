# backend/prompt_library.py

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

# --- RAG Prompts (Existing) ---

# This prompt is used for the standard RAG chain.
# It's designed to be strict about using only the provided context.
RAG_SYSTEM_PROMPT = """
You are a helpful AI assistant. Use ONLY the following provided context to answer the user's question. If the context does not contain enough information to answer the question, clearly state that you don't have enough information from the provided context. Do NOT make up answers.
"""

# We can store the full prompt template here.
RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    ("human", "Context: {context}\n\nQuestion: {question}")
])

# --- Agentic Prompts (NEW) ---

# This prompt is for the agent's initial decision-making.
AGENT_TOOL_ROUTER_PROMPT = PromptTemplate.from_template(
    """
    You are an AI assistant who can answer questions using either a local document database or by searching the web.
    Carefully analyze the user's question.

    If the question is likely answerable from internal, historical, or specific company documents, use the 'retrieve_from_docs' tool.
    If the question requires current, real-time, broad, or external information that would not be in a private document database, use the 'search_web' tool.

    If the user asks for "news", "latest", "recent", or anything that implies real-time data, use 'search_web'.
    If the user asks about something specific to the documents you've ingested, use 'retrieve_from_docs'.

    Your response must ONLY be a JSON object with a single key 'tool_name' and its value being either 'retrieve_from_docs' or 'search_web'.
    Example: {{"tool_name": "retrieve_from_docs"}}

    Question: {input}
    """
)

# This prompt is used to synthesize an answer from web search results.
WEB_SYNTHESIS_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant tasked with summarizing web search results to answer a user's question.
    Synthesize the information from the provided search results to answer the question clearly and concisely.
    Cite the sources if appropriate. If the search results do not contain enough information to answer, state that.
    Do NOT make up information."""),
    ("human", "Question: {question}\n\nSearch Results: {search_results}")
])

# This prompt is used by a new agentic step to check if retrieved documents are relevant.
RELEVANCE_GRADER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a relevance grader. Your task is to determine if a given context is relevant to a user's question.
    The context is considered relevant ONLY if it contains specific information that can be used to directly and confidently answer the question.
    If the context contains keywords but no specific, factual information to form an answer, respond with 'no'.
    Do not be fooled by contexts that are from a similar general subject but do not contain the specific answer. For example, if the question is about 'Topic A' and the context is about 'Related Topic B', the context is not relevant. If the question asks about a specific entity and the context talks about a different entity (even if the topic is the same), the context is not relevant.

    Respond with 'yes' if the context is relevant, and 'no' if it is not.
    Your response must ONLY be a single word: 'yes' or 'no'."""),
    ("human", "Question: {question}\n\nContext: {context}")
])

# --- AMBIGUITY & CLARIFICATION PROMPTS ---

# Step 1: Detect ambiguity
CLARIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
You are an AI assistant that checks user questions for ambiguity before sending them to a search or knowledge system.

Your task:
1. Read the user question carefully.
2. Determine if the question is ambiguous — meaning it lacks a specific detail that is necessary to answer it accurately.
   Examples of ambiguity:
     - Missing entity: "your company", "our product", "their services" without a specific name.
     - Missing time period: "last quarter" without specifying exact months/year.
     - Missing location: "in our area" without specifying the place.
     - Unclear reference: "that system", "the report" without context.
3. If the question is clear (no missing details), respond exactly with:
    clear
4. If the question is ambiguous, respond ONLY with a short, friendly clarification question asking the user for the missing detail.
   Do NOT answer the original question.
   Do NOT output anything except the clarification question.

Example:
User question: "What are your sustainability initiatives?"
Your response: "Which company are you referring to in this question?"

User question: "What are InnovateSoft Solutions' key differentiators?"
Your response: clear
    """),
    ("human", "Question: {question}")
])

# --- FIX: Added a new prompt to intelligently rephrase the user's query after clarification ---
# Step 2: Rephrase with provided clarification
REPHRASE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
You are a query rephraser.
Your task is to rewrite the 'Original Question' by seamlessly integrating the user's 'Clarification Detail'.
The goal is to create a new, complete, and unambiguous question that can be answered on its own.
Output only the rewritten question and nothing else.

Example 1:
Original Question: What is India's population?
Clarification Detail: for the year 2023
Rewritten Question: What was India's population in the year 2023?

Example 2:
Original Question: What are your key differentiators?
Clarification Detail: InnovateSoft Solutions
Rewritten Question: What are InnovateSoft Solutions' key differentiators?
    """),
    ("human", "Original Question: {original_question}\nClarification Detail: {clarification_detail}")
])


# --- Prompt Template for rephrasing exact matches ---
FINETUNE_RESPONSE_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    """
You are a rephrasing assistant. Your task is to rewrite the 'Retrieved Content' to make it a direct and coherent answer to the 'User's Question'.
Strictly use only the information available in the 'Retrieved Content'.
Do not add any new facts, explanations, or information that is not present in the 'Retrieved Content'.
Maintain a helpful and direct tone.

User's Question: {question}

Retrieved Content: {response_context}

Rephrased Answer:
"""
])