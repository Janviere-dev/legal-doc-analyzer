import streamlit as st
import os
import datetime
import shutil  # Library to move files
from typing import Dict

from pymilvus import MilvusClient
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


st.title("View All Uploaded Document")
st.write("List of current files available in our system:")

# Backend Logic: Scan the "data" folder
data_folder = "data"
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

files = os.listdir(data_folder)
if len(files) == 0:
    st.warning("The library is currently empty. Go to the 'Upload' to add documents.")
else:
    # Optionally inspect Milvus to see which files are indexed in the vector DB
    indexed_status: Dict[str, str] = {}
    try:
        uri = os.getenv("MILVUS_URI", "./milvus_data.db")
        token = os.getenv("MILVUS_TOKEN")
        client = MilvusClient(uri=uri, token=token) if token else MilvusClient(uri=uri)
        collection_name = "legal_docs"

        if client.has_collection(collection_name):
            for f in files:
                try:
                    res = client.query(
                        collection_name=collection_name,
                        filter=f'source_file == "{f}"',
                        output_fields=["id"],
                        limit=1,
                    )
                    indexed_status[f] = "Yes" if res else "No"
                except Exception:
                    indexed_status[f] = "Unknown"
        else:
            indexed_status = {f: "No collection" for f in files}
    except Exception:
        indexed_status = {f: "DB unavailable" for f in files}

    # Display the files in a professional table
    # We collect info like Name, Size, Date and whether they are indexed
    file_details = []
    for file in files:
        path = os.path.join(data_folder, file)
        stats = os.stat(path)  # It asks the operating system for Metadata(status of the file)
        file_details.append({
            "File Name": file,
            "Size (MB)": round(stats.st_size / (1024 * 1024), 2),
            "Date Uploaded": datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M'),
            "Indexed (Vector DB)": indexed_status.get(file, "Unknown"),
        })

    # Show as a clean table 
    st.table(file_details)

trash_folder = "trash"

for folder in [data_folder, trash_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Function to move file to trash
def move_to_trash(file):
    old_path = os.path.join(data_folder, file)
    new_path = os.path.join(trash_folder, file)
    shutil.move(old_path, new_path)
    # Also delete from Milvus vector store
    try:
        delete_document_from_store(file)
    except Exception as e:
        st.warning(f"File moved but vector store deletion had an issue: {str(e)}")
    st.success(f"Moved {file} to Trash")
    st.rerun()

# function to restore trashed file

def restore_file(file):
    older_path = os.path.join(trash_folder, file)
    new_path = os.path.join(data_folder, file)
    shutil.move(older_path,new_path)
    st.success(f"Restored {file} to Libary")
    st.rerun()


# Tab view

tab1, tab2 = st.tabs(["Active Library", "Recycle Bin"])

with tab1:
    active_files = os.listdir(data_folder)
    if not active_files:
        st.info("No active files.")
    else:
        for i, file in enumerate(active_files):
            col = st.columns([4, 1])
            col[0].text(file)
            if col[1].button("🗑️", key= f"active_del_{file}_{i}"):
                move_to_trash(file)


with tab2:
    trashed_files = os.listdir(trash_folder)
    if not trashed_files:
        st.info("Trash is empty.")
    else:
        for i, file in enumerate(trashed_files):
            col = st.columns([4, 1])
            col[0].text(file)
            if col[1].button("🔄", key = f"trash_res_{file}_{i}"):
                restore_file(file)

    
    st.success(f"Total document managed: {len(active_files)}")
