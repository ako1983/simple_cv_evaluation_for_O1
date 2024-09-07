# from langchain_community.embeddings.ollama import OllamaEmbeddings
# or any other llm
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings

def get_embedding_function():
    embeddings = OpenAIEmbeddings()
    # embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings
