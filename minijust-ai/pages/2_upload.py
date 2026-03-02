import streamlit as st
import os
import json
import hashlib
from datetime import datetime
from utils import process_and_store_document, delete_document_from_store

st.set_page_config(
    page_title = "Upload", 
    layout = "wide",
    initial_sidebar_state = "expanded"
)

# Add branding to the sidebar (the look)
with st.sidebar:
    # check if the logo exist, otherwise show text
    try:
        st.logo("assets/minijust.png", icon_image="assets/minijust.png", size="large")
    except:
        st.title("MINIJUST")

    footer = """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: transparent;
        color: gray;
        text-align: center;
        padding: 10px;
        font-size: 12px;
    }
    </style>
    <div class="footer">
        <p>© 2026 MINIJUST AI | A Year of Remarkable Change</p>
    </div>
"""
st.markdown(footer, unsafe_allow_html=True)


st.title("📤 Document Ingestion")
st.write("Upload legal documents to process and index them for intelligent search and chat.")

# Load document registry
REGISTRY_FILE = "data/document_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_registry(registry):
    os.makedirs("data", exist_ok=True)
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f, indent=2)

def get_doc_id(filepath):
    """Generate unique document ID from filepath"""
    return hashlib.md5(filepath.encode()).hexdigest()[:12]

# Basic ingestion metadata (used for filtering later)
doc_type = st.selectbox("Document type", options=["Legislation", "Case Law", "Other"], index=0)
jurisdiction = st.text_input("Jurisdiction (optional)", value="Rwanda")
source_url = st.text_input("Source URL (optional)", value="https://www.amategeko.gov.rw/")

# UI-Frontend component
uploaded_file = st.file_uploader("Choose a PDF or DOCX file", type=["pdf", "docx"])

if uploaded_file is not None:
    # Check if file already exists
    save_path = os.path.join("data", uploaded_file.name)
    doc_id = get_doc_id(save_path)
    registry = load_registry()
    file_exists = os.path.exists(save_path)
    
    if file_exists:
        st.warning(f"⚠️ File {uploaded_file.name} already exists. Re-uploading will replace it and update the index.")
        # Delete old document from vector store
        try:
            delete_document_from_store(uploaded_file.name)
            st.info("🗑️ Removed old version from index")
        except Exception as e:
            st.warning(f"Could not remove old version: {e}")
    
    # Save file
    os.makedirs("data", exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info(f"📄 Processing {uploaded_file.name}...")
    
    # Process and store in FAISS
    try:
        with st.status("Processing document...", expanded=True) as status:
            st.write("📄 Step 1: Parsing PDF with PyMuPDF...")
            st.write("🔍 Step 2: Detecting columns (multi-column layout support)...")
            st.write("🌐 Step 3: Detecting language (English, French, Kinyarwanda)...")
            st.write("📜 Step 4: Detecting articles (Ingingo ya...)...")
            st.write("✂️ Step 5: Creating intelligent chunks with metadata...")
            st.write("🧠 Step 6: Generating multilingual embeddings...")
            st.write("💾 Step 7: Storing in FAISS vector database...")
            
            num_chunks = process_and_store_document(
                save_path,
                uploaded_file.name,
                doc_type=doc_type,
                extra_metadata={
                    "doc_id": doc_id,
                    "jurisdiction": jurisdiction.strip(),
                    "source_url": source_url.strip(),
                    "upload_date": datetime.now().isoformat(),
                },
            )
            
            status.update(label="✅ Processing complete!", state="complete", expanded=False)
        
        # Update registry with document metadata
        registry[uploaded_file.name] = {
            "doc_id": doc_id,
            "filename": uploaded_file.name,
            "filepath": save_path,
            "doc_type": doc_type,
            "jurisdiction": jurisdiction.strip(),
            "source_url": source_url.strip(),
            "num_chunks": num_chunks,
            "upload_date": datetime.now().isoformat(),
            "status": "indexed"
        }
        save_registry(registry)
        
        st.success(f"✅ File processed and indexed successfully!")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Chunks Created", num_chunks)
        with col2:
            st.metric("Document ID", doc_id)
        
        st.info("🎯 Document is now searchable in the **Chat** page!")
        
        # Show what was detected
        with st.expander("📊 Processing Pipeline Details"):
            st.write("**✅ Automated Pipeline Completed:**")
            st.write("✓ PDF parsing with PyMuPDF (parse_pdf.py)")
            st.write("✓ Multi-column detection - up to 3 columns (detect_column.py)")
            st.write("✓ Language detection - Kinyarwanda/English/French (detect_language.py)")
            st.write("✓ Article detection - 'Ingingo ya...' patterns (detect_article.py)")
            st.write("✓ Article-level chunking for legislation (create_chunks.py)")
            st.write("✓ Intelligent chunking with context overlap (LangChain)")
            st.write("✓ Multilingual embeddings - sentence-transformers (create_embeddings.py)")
            st.write("✓ Metadata preserved - page, column, article numbers, language")
            st.write(f"✓ {num_chunks} searchable chunks indexed in FAISS")
            st.write(f"✓ Document registered with ID: {doc_id}")
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.error("**Debug Info:**")
        st.code(str(e))
        st.info("""
        **Troubleshooting:**
        1. Make sure all dependencies are installed: `pip install -r requirements.txt`
        2. Check that the PDF is not corrupted
        3. Ensure the `faiss_index` directory has write permissions
        4. For large PDFs, processing may take a few minutes
        """)

# Show existing documents
st.divider()
st.subheader("📚 Indexed Documents")

registry = load_registry()
if registry:
    for filename, info in registry.items():
        with st.expander(f"📄 {filename}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Type:** {info['doc_type']}")
                st.write(f"**Jurisdiction:** {info['jurisdiction']}")
                st.write(f"**Chunks:** {info['num_chunks']}")
            with col2:
                st.write(f"**Document ID:** {info['doc_id']}")
                st.write(f"**Upload Date:** {info['upload_date'][:10]}")
                st.write(f"**Status:** {info['status']}")
            
            if st.button(f"🗑️ Delete {filename}", key=f"del_{filename}"):
                try:
                    delete_document_from_store(filename)
                    if os.path.exists(info['filepath']):
                        os.remove(info['filepath'])
                    del registry[filename]
                    save_registry(registry)
                    st.success(f"Deleted {filename}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting: {e}")
else:
    st.info("No documents indexed yet. Upload your first document above!")