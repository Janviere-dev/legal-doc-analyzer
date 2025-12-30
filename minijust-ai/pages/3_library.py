import streamlit as st
import os
import datetime
import shutil  # Library to move files 

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
    # Dispaly the files in a profesional Table
    # We will collect info like Name, Size, and Date
    file_details = []
    for file in files:
        path = os.path.join(data_folder, file)
        stats = os.stat(path)  # It asks the operating system for Metadata(status of the file)
        file_details.append({
            "File Name": file,
            "Size (MB)": round(stats.st_size / (1024 * 1024), 2),
            "Date Uploaded": datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M')
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
    st.success(f"Moved{file} to Trash")
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
    files = os.listdir(data_folder)
    if not files:
        st.info("No active files.")
    else:
        for i, files in enumerate(files):
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

    
    st.success(f"Total document managed: {len(files)}")
