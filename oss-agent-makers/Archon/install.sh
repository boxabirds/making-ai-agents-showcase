#!/bin/bash

# Archon Installation Script - Package Form (Python)

# This script installs Archon using the local Python package method.
# It assumes Python 3.11+ is installed on the system.
# It uses a Python virtual environment and pip for dependency management.
# The script also includes instructions for running the client (Streamlit UI) and server (FastAPI graph service).

# ---------------------------
# Setup Python Virtual Environment and Install Dependencies
# ---------------------------
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

# ---------------------------
# Running the Server (Graph Service)
# ---------------------------
# The graph service is a FastAPI app that handles the agentic workflow.
# It runs on port 8100 by default.
# Run this command in a separate terminal or background process.
# Example:
# uvicorn graph_service:app --host 0.0.0.0 --port 8100

# ---------------------------
# Running the Client (Streamlit UI)
# ---------------------------
# The Streamlit UI provides the web interface for managing Archon.
# It runs on port 8501 by default.
streamlit run streamlit_ui.py

# ---------------------------
# Access the UI
# ---------------------------
# Open your browser and go to http://localhost:8501 to use Archon.

# ---------------------------
# Notes
# ---------------------------
# - You need a Supabase account for the vector database.
# - You need API keys for OpenAI/Anthropic/OpenRouter or Ollama for local LLMs.
# - Follow the guided setup process in the Streamlit UI for environment, database, documentation, and agent service setup.
# - For updates, pull the latest changes and reinstall dependencies as needed.

# End of script