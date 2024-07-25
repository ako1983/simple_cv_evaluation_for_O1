# Evaluation Guide

## Objective

The goal is to evaluate CVs based on the O-1A visa qualification criteria using the provided FastAPI application and OpenAI's language model.

## Steps to Evaluate

1. **Run the FastAPI Application**:
    ```sh
    uvicorn app:app --reload --port 8002
    ```

2. **Send a CV for Evaluation**:
    - Use the `loader.py` script to send a CV file:
        ```sh
        python loader.py
        ```

3. **Check the Response**:
    - The loader script will print the evaluation response received from the FastAPI application.
    - The response will contain an evaluation of the CV based on the O-1A criteria, with a rating (low, medium, high) indicating the chance of qualification.

## Interpretation of Results

- **High**: Strong chance of meeting O-1A visa criteria.
- **Medium**: Moderate chance of meeting O-1A visa criteria; might require additional evidence.
- **Low**: Low chance of meeting O-1A visa criteria; significant improvements or additional evidence required.
