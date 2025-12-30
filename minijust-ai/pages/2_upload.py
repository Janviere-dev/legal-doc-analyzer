import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

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

# UI-Frontent component
uploaded_file= st.file_uploader("Choose a PDF or DOCX file", type = ["pdf", "docx"])

if uploaded_file is not None:
    # Save file
    save_path = os.path.join("data", uploaded_file.name)
    with open(save_path,"wb") as f:
        f.write(uploaded_file.getbuffer()) 

    st.info(f"Processing {uploaded_file.name}...")

    # Choose right loader based on file extension
    if uploaded_file.name.endswith(".pdf"):
        loader = PyPDFLoader(save_path)
    elif uploaded_file.name.endswith(".docx"):
        loader = Docx2txtLoader(save_path)

    # Load and Chunk
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(pages)

    st.success("File processed successfully!")
    st.metric("Total chunks Created", len(chunks))