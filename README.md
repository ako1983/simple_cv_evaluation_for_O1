# CV Evaluation App

This project evaluates CVs for O-1A visa qualification using a FastAPI backend and OpenAI's language model. It employs a Retrieval-Augmented Generation (RAG) system to enhance the evaluation process by leveraging relevant document context.

## Setup

1. Clone the repository:
    ```sh
    git clone <repo_url>
    cd my_cv_evaluation_app
    ```

2. Create a virtual environment and install dependencies:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. Run the FastAPI application:
    ```sh
    uvicorn app:app --reload --port 8000
    ```

4. Use the loader script to evaluate a CV:
    ```sh
    python loader.py
    ```

## Project Structure
app.py: FastAPI application code, including endpoints for creating the database, querying, and evaluating CVs.

create_database.py: Script for initializing and managing the Chroma vector store.

get_embedding_function.py: Defines the embedding function used for document processing.

loader.py: Script to send CV files to the FastAPI endpoint for evaluation.

query_data.py: Handles querying the Chroma database for relevant document context.

requirements.txt: List of dependencies required for the project.

README.md: Project overview, setup instructions, and usage guidelines.

## API Endpoints
/create_database
Description: Initializes or resets the Chroma vector store with documents from the data/ directory.

Method: POST
Parameters: reset (boolean, optional) - Resets the database if true.
Response: A message indicating the status of the database creation.

/query_database
Description: Retrieves relevant documents from the database based on a query.
Method: POST
Request Body:
query_text (string): The query to search for relevant documents.
Response:
response (string): Generated response from the model.
sources (list): List of document IDs used as context.

/evaluate
Description: Evaluates a CV for O-1A visa qualification using document context from the database.
Method: POST
Request Body:
cv_text (string): The CV content to be evaluated.
Response:
evaluation (string): The model's assessment of the CV's qualification.

## Documentation

See the `docs/` directory for detailed information on design choices and how to evaluate the output.

## Usage Examples
Creating the Database:
```sh
curl -X POST "http://127.0.0.1:8000/create_database?reset=true"
```

Querying the Database:
```sh
curl -X POST "http://127.0.0.1:8000/query_database" -H "Content-Type: application/json" -d '{"query_text": "specific question or keyword"}'
```

Evaluating a CV:

```sh
curl -X POST "http://127.0.0.1:8000/evaluate" -H "Content-Type: application/json" -d '{"cv_text": "CV content here"}'
```
