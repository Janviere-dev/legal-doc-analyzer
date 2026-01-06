#  MINIJUST Legal Document Analyzer (AI Prototype)

This is a specialized RAG (Retrieval-Augmented Generation) application developed for the **Ministry of Justice**. It allows users to upload legal documents and engage in a context-aware chat to extract insights and legal citations.

##  Quick Start Instructions

Follow these steps to set up the environment and run the application on your local machine.

### 1. Prerequisites
* Ensure you have **Python 3.10 or higher** installed.
* You will need a **Groq API Key** (and/or Gemini API key) to power the LLM.

### 2. Installation
Open your terminal in the project folder and run:

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the environment
# On Windows: .venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install required libraries
pip install -r requirements.txt

To make sure your supervisor can run this without any "it's not working on my machine" headaches, your README.md needs to be professional, clear, and include a troubleshooting section.

Here is a complete, ready-to-use README and the corresponding requirements.txt.

1. The requirements.txt File
Create a file named requirements.txt in your root folder and paste this:

Plaintext

streamlit
langchain-huggingface
langchain-community
langchain-groq
sentence-transformers
pypdf2
python-docx
faiss-cpu
python-dotenv
2. The README.md File
Create a file named README.md in your root folder and paste the following content:

Markdown

# ⚖️ MINIJUST Legal Document Analyzer (AI Prototype)

This is a specialized RAG (Retrieval-Augmented Generation) application developed for the **Ministry of Justice**. It allows users to upload legal documents and engage in a context-aware chat to extract insights and legal citations.

##  Quick Start Instructions

Follow these steps to set up the environment and run the application on your local machine.

### 1. Prerequisites
* Ensure you have **Python 3.10 or higher** installed.
* You will need a **Groq API Key** (and/or Gemini API key) to power the LLM.

### 2. Installation
Open your terminal in the project folder and run:

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the environment
# On Windows: .venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install required libraries
pip install -r requirements.txt
### 3. Environment Setup
Create a file named .env in the root directory and add your credentials:
GROQ_API_KEY=your_key_here

### 4. Running the App
Launch the application with:

Bash

streamlit run app.py
### Troubleshooting (If you have issues)
"Module Not Found" Error: Ensure you have activated the virtual environment (source .venv/bin/activate) before running the app.

"Externally Managed Environment": This means you are trying to install libraries globally. Always ensure the .venv is active.

API Key Error: Double-check that your .env file is named correctly and contains the valid key.

Slow PDF Processing: The first time you upload a document, the system generates "embeddings." This may take a moment depending on the document size.
