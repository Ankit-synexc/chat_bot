from typing import List, Dict, Any, Optional

def estimate_tokens(text: str) -> int:
    """Approximate token count (characters // 4)."""
    if not text:
        return 0
    return len(text) // 4

def build_system_prompt() -> str:
    """Build the system prompt for the RAG assistant."""
    return (
        "You are a helpful, conversational, and highly intelligent AI assistant. "
        "Your task is to answer the user's question naturally, using ONLY the provided context chunks. "
        "You MUST observe the following rules:\n"
        "1. Answer in a warm, human-like, and engaging tone. Avoid robotic phrases like 'According to the context' or 'Based on the provided document'. Just answer the question directly as if you know the information.\n"
        "2. Do NOT manually inject source file names or citations into your text (e.g., don't write '(Source: file.docx)'). The system handles citations separately in the UI.\n"
        "3. If the context is entirely insufficient to answer the question, politely and conversationally say that you don't have enough information in the uploaded documents to answer.\n"
        "4. Be concise but thorough."
    )

def build_rag_prompt(question: str, chunks: List[Dict[str, Any]], chat_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Format the retrieved chunks into a context block and append the question.
    Approximates token budget to keep the final prompt under ~3000 tokens.
    """
    history_text = ""
    if chat_history:
        history_parts = []
        for turn in chat_history:
            history_parts.append(f"User: {turn['question']}\nAssistant: {turn['answer']}")
        history_text = "--- Conversation History ---\n" + "\n\n".join(history_parts) + "\n----------------------------\n\n"

    context_parts = []
    current_tokens = 0
    max_tokens = 3000 - estimate_tokens(question) - estimate_tokens(history_text) - 500  # reserve tokens for system prompt and safety margin
    
    for i, chunk in enumerate(chunks):
        source = chunk.get("source_file", "Unknown source")
        page = chunk.get("page_number")
        page_str = f", Page: {page}" if page else ""
        text = chunk.get("text", "")
        
        chunk_str = f"--- Section {i+1} ---\nSource: {source}{page_str}\nContent: {text}\n"
        chunk_tokens = estimate_tokens(chunk_str)
        
        if current_tokens + chunk_tokens > max_tokens:
            break
            
        context_parts.append(chunk_str)
        current_tokens += chunk_tokens
        
    context_text = "\n".join(context_parts)
    if not context_text:
        context_text = "No relevant context found."
        
    prompt = (
        f"{history_text}"
        f"Context information is below.\n\n"
        f"{context_text}\n\n"
        f"Given the context information above, please answer the following question:\n"
        f"Question: {question}"
    )
    
    return prompt
