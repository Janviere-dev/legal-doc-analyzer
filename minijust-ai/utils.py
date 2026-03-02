"""
Simplified utils.py - Orchestrates standalone modules instead of duplicating logic
All heavy lifting is done by: parse_pdf.py, detect_column.py, detect_language.py, 
create_chunks.py, create_embeddings.py
This file just coordinates them for the chat interface.
"""

import os
from typing import Dict, Optional, List, Any

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Import ALL functionality from our well-implemented standalone modules
from create_chunks import create_chunks_from_pdf
from create_embeddings import get_embedding_model, create_vector_store

load_dotenv()

DOC_TYPES = ("Legislation", "Case Law", "Other")
VECTOR_STORE_PATH = "faiss_index"


def process_and_store_document(
    file_path: str,
    source_file_name: str,
    *,
    doc_type: str = "Legislation",
    extra_metadata: Optional[Dict[str, str]] = None,
    vector_store_path: str = VECTOR_STORE_PATH,
    chunk_size: int = 1500,
    chunk_overlap: int = 200,
) -> int:
    """
    Simplified ingestion pipeline using standalone modules.
    
    Pipeline:
    1. create_chunks_from_pdf() handles:
       - PDF parsing (parse_pdf.py)
       - Column detection (detect_column.py)
       - Language detection (detect_language.py)
       - Article detection and chunking (create_chunks.py)
    
    2. create_vector_store() from create_embeddings.py handles:
       - Embedding generation
       - FAISS vector store creation/update
    
    No logic duplication - just orchestration!
    """
    if doc_type not in DOC_TYPES:
        doc_type = "Other"

    extra_metadata = extra_metadata or {}

    # Use the sophisticated chunking from create_chunks.py
    # It handles everything: parsing, columns, language, articles, chunking
    doc_type_for_chunker = 'legislation' if doc_type == 'Legislation' else 'case_law'
    chunks = create_chunks_from_pdf(file_path, doc_type=doc_type_for_chunker)
    
    if not chunks:
        return 0

    # Enrich chunks with additional metadata before storing
    for chunk in chunks:
        chunk['metadata'].update({
            "source": extra_metadata.get("source", "amategeko.gov.rw"),
            "source_file": source_file_name,
            "doc_type": doc_type,
            **extra_metadata,
        })

    # Use create_embeddings.py to handle FAISS storage
    # This function handles loading existing index, adding new documents, and saving
    create_vector_store(chunks, save_path=vector_store_path)

    return len(chunks)


def load_vector_store(vector_store_path: str = VECTOR_STORE_PATH) -> Optional[FAISS]:
    """Load existing FAISS vector store"""
    if not os.path.exists(vector_store_path):
        return None
    
    try:
        embeddings = get_embedding_model()
        vector_store = FAISS.load_local(
            vector_store_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        return vector_store
    except Exception as e:
        print(f"Error loading vector store: {e}")
        return None


def search_documents(
    query: str,
    k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None,
    vector_store_path: str = VECTOR_STORE_PATH
) -> List[Document]:
    """
    Search documents in FAISS vector store
    
    Args:
        query: Search query text
        k: Number of results to return
        filter_dict: Optional metadata filters (e.g., {"doc_type": "Legislation"})
        vector_store_path: Path to FAISS index
    
    Returns:
        List of relevant Document objects with metadata
    """
    vector_store = load_vector_store(vector_store_path)
    if not vector_store:
        return []
    
    try:
        if filter_dict:
            # FAISS doesn't support metadata filtering natively.
            # We over-fetch and filter manually, increasing fetch size progressively
            # so selected-file searches still return results in large mixed indexes.
            def metadata_matches(doc: Document) -> bool:
                for key, value in filter_dict.items():
                    doc_value = doc.metadata.get(key)
                    if isinstance(value, (list, tuple, set)):
                        if doc_value not in value:
                            return False
                    else:
                        if doc_value != value:
                            return False
                return True

            total_docs = getattr(vector_store.index, "ntotal", k)
            initial_fetch = min(max(k * 10, 50), total_docs)
            fetch_k = max(initial_fetch, k)
            max_fetch = total_docs

            while True:
                results = vector_store.similarity_search(query, k=fetch_k)
                filtered = [doc for doc in results if metadata_matches(doc)]

                if len(filtered) >= k or fetch_k >= max_fetch:
                    return filtered[:k]

                # Increase retrieval window and try again
                fetch_k = min(fetch_k * 2, max_fetch)
        else:
            return vector_store.similarity_search(query, k=k)
    except Exception as e:
        print(f"Error searching documents: {e}")
        return []


def delete_document_from_store(
    source_file_name: str, 
    vector_store_path: str = VECTOR_STORE_PATH
) -> None:
    """
    Remove all chunks for a specific document from FAISS vector store
    
    Note: FAISS doesn't support direct deletion. This function:
    1. Loads the existing index
    2. Filters out documents matching source_file_name
    3. Recreates the index with remaining documents
    """
    vector_store = load_vector_store(vector_store_path)
    if not vector_store:
        return
    
    try:
        # Get all documents from the store
        all_docs = vector_store.docstore._dict.values()
        
        # Filter out documents from the specified file
        remaining_docs = [
            doc for doc in all_docs 
            if doc.metadata.get("source_file") != source_file_name
        ]
        
        if len(remaining_docs) == len(all_docs):
            print(f"No documents found with source_file: {source_file_name}")
            return
        
        # Recreate FAISS index with remaining documents
        if remaining_docs:
            embeddings = get_embedding_model()
            new_store = FAISS.from_documents(remaining_docs, embeddings)
            new_store.save_local(vector_store_path)
            print(f"Deleted {len(all_docs) - len(remaining_docs)} chunks from {source_file_name}")
        else:
            # All documents removed - delete the index
            import shutil
            if os.path.exists(vector_store_path):
                shutil.rmtree(vector_store_path)
            print(f"Vector store empty after deletion - removed index")
    
    except Exception as e:
        print(f"Error deleting document: {e}")

