"""
Create Embeddings for Legal Documents
Uses LangChain and HuggingFace to generate embeddings and store them in FAISS.
"""

import sys
import os
from typing import List, Dict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from create_chunks import create_chunks_from_pdf

# Constants
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_STORE_PATH = "faiss_index"

def get_embedding_model():
    """Initialize the embedding model"""
    print(f"Loading embedding model: {EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return embeddings

def create_vector_store(chunks: List[Dict], save_path: str = VECTOR_STORE_PATH):
    """
    Convert dictionary chunks to LangChain Documents and create FAISS index
    """
    if not chunks:
        print("No chunks to process.")
        return None

    # Convert chunks to LangChain Document objects
    documents = []
    print(f"Preparing {len(chunks)} documents for embedding...")
    
    for chunk in chunks:
        # Create a clean text representation for the embedding content
        # We might want to include the 'article_number' in the text if it exists to help with retrieval
        page_content = chunk['text']
        metadata = chunk['metadata']
        
        # Add the chunk_id to metadata so we can track it back
        metadata['chunk_id'] = chunk['chunk_id']
        
        doc = Document(
            page_content=page_content,
            metadata=metadata
        )
        documents.append(doc)

    # Initialize embeddings
    embeddings = get_embedding_model()

    if os.path.exists(save_path):
        try:
            print(f"Loading existing vector store from '{save_path}'...")
            vector_store = FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)
            print("Adding new documents to existing store...")
            vector_store.add_documents(documents)
        except Exception as e:
            print(f"Could not load existing index (Error: {e}). Creating new one.")
            vector_store = FAISS.from_documents(documents, embeddings)
    else:
        # Create Vector Store
        print("Creating new vector store...")
        vector_store = FAISS.from_documents(documents, embeddings)

    # Save to disk
    print(f"Saving vector store to '{save_path}'...")
    vector_store.save_local(save_path)
    print("Success! Vector store updated.")
    
    return vector_store
