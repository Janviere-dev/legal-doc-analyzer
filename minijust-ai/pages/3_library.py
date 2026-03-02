import streamlit as st
import os
import json
import datetime
import shutil  # Library to move files
from typing import Dict

from utils import delete_document_from_store 

st.set_page_config(
    page_title = "Library", 
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


st.title("📚 View All Uploaded Documents")
st.write("Browse and manage your indexed legal documents.")

# Info about chat integration
st.info("💡 **Tip**: Go to the **Chat** page to ask questions about these documents. You can select specific documents to search.")

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

# Backend Logic: Load from registry
data_folder = "data"
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

registry = load_registry()

if not registry:
    st.warning("📄 The library is currently empty. Go to the **Upload** page to add documents.")
else:
    # Display documents from registry in a professional table
    file_details = []
    for filename, info in registry.items():
        file_details.append({
            "📄 File Name": filename,
            "Type": info.get('doc_type', 'Unknown'),
            "Chunks": info.get('num_chunks', 0),
            "Jurisdiction": info.get('jurisdiction', 'N/A'),
            "Indexed": info.get('status', 'unknown'),
            "Date": info.get('upload_date', '')[:10],
        })
    
    # Show as a clean table
    st.table(file_details)
    
    st.divider()
    st.subheader("📊 Library Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Documents", len(registry))
    with col2:
        total_chunks = sum(info.get('num_chunks', 0) for info in registry.values())
        st.metric("Total Chunks", total_chunks)
    with col3:
        st.metric("Vector Store", "FAISS ✅")

trash_folder = "trash"

for folder in [data_folder, trash_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Function to move file to trash
def move_to_trash(file):
    old_path = os.path.join(data_folder, file)
    new_path = os.path.join(trash_folder, file)
    shutil.move(old_path, new_path)
    # Also delete from FAISS vector store
    try:
        delete_document_from_store(file)
        # Remove from registry
        registry = load_registry()
        if file in registry:
            del registry[file]
            save_registry(registry)
    except Exception as e:
        st.warning(f"File moved but vector store deletion had an issue: {str(e)}")
    st.success(f"✅ Moved {file} to Trash")
    st.rerun()

# function to restore trashed file
def restore_file(file):
    older_path = os.path.join(trash_folder, file)
    new_path = os.path.join(data_folder, file)
    shutil.move(older_path, new_path)
    st.success(f"✅ Restored {file} to Library")
    st.rerun()


# Tab view
tab1, tab2 = st.tabs(["📚 Active Library", "🗑️ Recycle Bin"])

with tab1:
    active_files = list(registry.keys())
    if not active_files:
        st.info("No active documents in the library.")
    else:
        st.write(f"**{len(active_files)} document(s) ready for search**")
        
        # Display each document with delete option
        for i, filename in enumerate(active_files):
            info = registry[filename]
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"📄 **{filename}**")
                st.caption(f"Type: {info['doc_type']} | Chunks: {info['num_chunks']} | {info['upload_date'][:10]}")
            
            with col2:
                if st.button("📋 Details", key=f"details_{filename}_{i}"):
                    with st.expander(f"Details for {filename}"):
                        st.json(info)
            
            with col3:
                if st.button("🗑️", key=f"active_del_{filename}_{i}"):
                    move_to_trash(filename)
    
    # Quick access to chat
    if active_files:
        st.divider()
        st.write("### 💬 Ready to Ask Questions?")
        st.write("Go to the **Chat** page to ask questions about your documents.")
        st.write("You can select specific documents to search or search across all documents.")


with tab2:
    trash_folder = "trash"
    if not os.path.exists(trash_folder):
        os.makedirs(trash_folder)
    
    trashed_files = os.listdir(trash_folder)
    if not trashed_files:
        st.info("🗑️ Recycle bin is empty.")
    else:
        st.write(f"**{len(trashed_files)} trashed file(s)**")
        
        for i, filename in enumerate(trashed_files):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"📄 {filename}")
            
            with col2:
                if st.button("🔄 Restore", key=f"trash_res_{filename}_{i}"):
                    restore_file(filename)

# Summary footer
st.divider()
total_active = len(registry)
st.success(f"✅ **Total documents managed: {total_active}**")
