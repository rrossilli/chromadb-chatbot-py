# ChromaDB Chatbot

_work in progress_

## Setup

Install chromadb and openai (in `requirements.txt` file)

## Usage

- Main chat client: `python chat.py`
- Take a look in your KB: `python chromadb_peek.py`
- Provide a document (experimental): `python source_file.py`

## Code Explanation

This Python script serves as the implementation of a chatbot that leverages the OpenAI's GPT-4 model. It additionally integrates the chatbot with a persistent knowledge base using the ChromaDB library. Here's an overview of how the different parts of the script function:

1. **Utility Functions**: The script starts with several utility functions to handle file operations and to interact with OpenAI's API. These include functions for saving and opening files, and a function to run the chatbot, managing retries in case of exceptions.
2. **Main Application**: The script's main operation is contained within a continuous loop (`while True:`), enabling continuous interaction with the user. This loop does the following:
   - **Instantiates the ChromaDB client** for persistent storage and knowledge base management.
   - **Initiates the chatbot** by loading OpenAI's API key and preparing a conversation list.
   - **Captures user input** and adds it to the conversation list. The input is also logged in a separate file for record-keeping.
   - **Searches the knowledge base** for relevant content based on the current conversation and updates the chatbot's default system message accordingly.
   - **Generates a response** from the chatbot based on the conversation so far, which includes the updated default system message and the user's input.
   - **Updates the user profile** based on the user's recent messages, using the chatbot's response as the updated profile.
   - **Updates the knowledge base** with the most recent conversation, either adding a new entry or updating an existing entry. If an existing entry becomes too long, it's split into two separate entries.

The script logs all interactions with the OpenAI API and updates to the knowledge base, providing a record of the chatbot's operations and aiding in debugging and optimization efforts. The use of the ChromaDB library allows for scalable storage and retrieval of the chatbot's knowledge base, accommodating a growing number of conversations and data points.