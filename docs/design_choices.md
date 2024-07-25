# Design Choices

## Overview

This document explains the design choices made for the CV Evaluation App.

## FastAPI for Backend

FastAPI is chosen for its performance and ease of use. It allows asynchronous handling of requests, which is beneficial for our application as it interacts with the OpenAI API.

## OpenAI API

The OpenAI API is used to evaluate CVs based on the O-1A visa criteria. The prompt-based approach allows flexibility in the evaluation process.

## Non-Streaming API Call

For simplicity, the non-streaming API call (`openai.ChatCompletion.create`) is used. This is sufficient for our use case and avoids the complexity of handling streaming responses.

## Loader Script

A separate loader script (`loader.py`) is provided to send CV files to the FastAPI application for evaluation. This script reads the CV file, constructs the payload, and sends it to the `/evaluate` endpoint.

## Error Handling

Error handling is implemented in the `provide_cv` function to catch and return proper HTTP errors if the OpenAI API call fails.
