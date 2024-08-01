# app.py
## 1. Import Necessary Modules and Setup FastAPI

import os
import shutil
import asyncio
from typing import AsyncIterable
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai
from langchain_community.document_loaders import DirectoryLoader, UnstructuredHTMLLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Importing functions from the new scripts
from create_database import load_documents, split_text, add_to_chroma, clear_database
from query_database import query_rag
from get_embedding_function import get_embedding_function 

##############
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
##############

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#########################
# Constants for paths
CHROMA_PATH = "chroma"
DATA_PATH = "data/"

#########################
# This prompt template is used for general queries and document retrieval from the database.
PROMPT_TEMPLATE = """Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""
# In the /evaluate endpoint, a different prompt is used to specifically tailor the response
# towards evaluating a CV for O-1A visa qualification. It includes the context and the CV text
# to provide a comprehensive assessment.
#########################
## 2. Define Data Models

class CVRequest(BaseModel):
    cv_text: str

class EvaluationResponse(BaseModel):
    evaluation: str

class QueryRequest(BaseModel):
    query_text: str

class DatabaseResponse(BaseModel):
    message: str

class QueryResponse(BaseModel):
    response: str
    sources: list

#########################
## 3. Database Management Endpoint

@app.post("/create_database", response_model=DatabaseResponse)
async def create_database(reset: bool = False):
    try:
        if reset:
            clear_database()
        documents = load_documents()
        chunks = split_text(documents)
        add_to_chroma(chunks)
        return {"message": "Database created/updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating database: {e}")
    
#########################
## 4. Querying Database Endpoint

@app.post("/query_database", response_model=QueryResponse)
async def query_database(query_request: QueryRequest):
    try:
        response_text, sources = query_rag(query_request.query_text)
        return {"response": response_text, "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying database: {e}")
    

async def provide_cv(cv_text: str) -> str:
    prompt = f"Evaluate the following CV for O-1A visa qualification:\n\n{cv_text}\n\nList the things that meet the O-1A criteria and give a rating (low, medium, high) on the chance that this person is qualified for an O-1A immigration visa."
    messages = [
        {
            "role": "system",
            "content": "You are an assistant that helps evaluate CVs for O-1A visa qualification.",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        response = await openai.ChatCompletion.create(
            model="gpt-4o-mini", messages=messages, max_tokens=1500
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    evaluation = response.choices[0].message["content"].strip()
    return evaluation

#########################
## 5. Evaluation Endpoint
@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_cv_endpoint(cv_request: CVRequest):
    try:
        # Query the Chroma database for relevant documents
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function())
        results = db.similarity_search_with_score(cv_request.cv_text, k=3)
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in results])

        # Create a prompt with the context
        prompt = f"Using the following context, evaluate the CV for O-1A visa qualification:\n\n{context_text}\n\nCV Text:\n\n{cv_request.cv_text}\n\nList the relevant achievements and provide a likelihood rating (low, medium, high)."
        messages = [
            {"role": "system", "content": "You are an assistant that helps evaluate CVs for O-1A visa qualification."},
            {"role": "user", "content": prompt}
        ]

        # Get response from the model
        response = await openai.ChatCompletion.create(model="gpt-4o-mini", messages=messages, max_tokens=1500)
        evaluation = response.choices[0].message['content'].strip()

        return {"evaluation": evaluation}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


#########################
# Main function for serving the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)