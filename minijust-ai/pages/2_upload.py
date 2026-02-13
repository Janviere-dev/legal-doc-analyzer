import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils import process_and_store_document, delete_document_from_store
from pymilvus import MilvusClient

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


st.title("Document Ingestion")
st.write("Upload Document here")

# Basic ingestion metadata (used for filtering later)
doc_type = st.selectbox("Document type", options=["Legislation", "Case Law", "Other"], index=0)
jurisdiction = st.text_input("Jurisdiction (optional)", value="Rwanda")
# source_url = st.text_input("Source URL (optional)", value="https://www.amategeko.gov.rw/")

# UI-Frontent component
uploaded_file= st.file_uploader("Choose a PDF or DOCX file", type = ["pdf", "docx"])

if uploaded_file is not None:
    # Check if file already exists
    save_path = os.path.join("data", uploaded_file.name)
    file_exists = os.path.exists(save_path)
    
    if file_exists:
        st.warning(f"File {uploaded_file.name} already exists. Uploading will replace it and update the vector store.")
        # Delete old document from vector store
        try:
            delete_document_from_store(uploaded_file.name)
        except:
            pass
    
    # Save file
    with open(save_path,"wb") as f:
        f.write(uploaded_file.getbuffer()) 

    st.info(f"Processing {uploaded_file.name}...")
    
    # Process and store in Milvus
    try:
        with st.spinner("Extracting text, chunking, and creating embeddings..."):
            num_chunks = process_and_store_document(
                save_path,
                uploaded_file.name,
                doc_type=doc_type,
                extra_metadata={
                    "jurisdiction": jurisdiction.strip(),
                    # "source_url": source_url.strip(),
                },
            )
        
        st.success(f"File processed and stored in vector database successfully!")
        st.metric("Total chunks Created", num_chunks)
        st.info("✅ Document is now searchable in the chat interface!")
    except ConnectionError as e:
        st.error("❌ **Milvus Connection Error**")
        st.error(str(e))
        st.info("""
        **Quick Fix:**
        1. **Easiest option** - Use Milvus Lite:
           - Add to your `.env` file: `MILVUS_URI=./milvus_data.db`
           - Run: `pip install milvus`
           - Restart the app
        
        2. **Docker option** - Run Milvus server:
           ```bash
           docker run -d --name milvus-standalone -p 19530:19530 milvusdb/milvus:latest
           ```
           - Add to `.env`: `MILVUS_URI=http://localhost:19530`
        
        3. **Cloud option** - Use Zilliz Cloud:
           - Sign up at https://cloud.zilliz.com/
           - Set `MILVUS_URI` and `MILVUS_TOKEN` in `.env`
        """)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.info("💡 Make sure Milvus is running. Check the setup instructions in the README.")