import os
from langchain_ollama import ChatOllama

# If OLLAMA_BASE_URL is set (Docker), use it. 
# Otherwise, default to localhost (Local Debugging).
ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0,
    base_url=ollama_url
)