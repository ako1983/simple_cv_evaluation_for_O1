# from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings



def get_embedding_function():
    embeddings = OpenAIEmbeddings()
    # embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings
