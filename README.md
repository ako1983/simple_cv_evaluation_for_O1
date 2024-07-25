# CV Evaluation App

This project evaluates CVs for O-1A visa qualification using a FastAPI backend and OpenAI's language model.

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
    uvicorn app:app --reload --port 8002
    ```

4. Use the loader script to evaluate a CV:
    ```sh
    python loader.py
    ```

## Project Structure

- `app.py`: FastAPI application code.
- `loader.py`: Script to send CV files to the FastAPI endpoint for evaluation.
- `requirements.txt`: List of dependencies.
- `docs/`: Documentation for design choices and evaluation guide.
- `README.md`: Project overview and setup instructions.

## Documentation

See the `docs/` directory for detailed information on design choices and how to evaluate the output.
