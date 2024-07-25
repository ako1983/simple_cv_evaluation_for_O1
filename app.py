import asyncio
from typing import AsyncIterable

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CVRequest(BaseModel):
    cv_text: str


class EvaluationResponse(BaseModel):
    evaluation: str


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
            model="gpt-4", messages=messages, max_tokens=1500
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    evaluation = response.choices[0].message["content"].strip()
    return evaluation


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_cv_endpoint(cv_request: CVRequest):
    evaluation = await provide_cv(cv_request.cv_text)
    return {"evaluation": evaluation}
