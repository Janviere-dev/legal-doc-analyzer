import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
# from utils import get_document_text, get_text_chunks, get_vector_store

st.set_page_config(
    page_title = "Chat", 
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


load_dotenv()
client = Groq(api_key = os.getenv("GROQ_API_KEY"))

st.title("MINIJUST AI Assistant")

# The Dummy Database( this acts as our temporary storage for all past chats.)
if "chat_archive" not in st.session_state:
    st.session_state.chat_archive = [] # our dummy table

# Current session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar: History Vault 
with st.sidebar:
    st.header("Past Conversations")
    if not st.session_state.chat_archive:
        st.write("No saved chats yet.")
    else:
        for i, past_chat in enumerate(st.session_state.chat_archive):
            # show button for each saved chat
            if st.button(f"chat {i+1}: {past_chat['title']}", key= f"archive_{i}"):
                st.session_state.messages = past_chat["content"]

if st.button("➕ New chat", use_container_width=True):
    # save current chat to archive before clearing
    if st.session_state.messages:
        first_msg = st.session_state.messages[0]["content"][:20]
        st.session_state.chat_archive.append({
            "title": f"{first_msg}...",
            "content": st.session_state.messages
        })
        st.session_state.messages = []
        st.rerun()

# Chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What can I help you with?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model = "llama-3.3-70b-versatile",
                messages = [{"role": "user", "content": prompt}],
            )
            # context = " ".join(chunks[:3]) # For now, we take the first 3 chunks as a test
            # system_prompt = f"You are a legal assistant. Use this document context to answer: {context}"

            # response = client.chat.completions.create(
            #     model="llama-3.3-70b-versatile",
            #     messages=[
            #         {"role": "system", "content": system_prompt},
            #         {"role": "user", "content": prompt}
            #     ],
            # )
            full_response = response.choices[0].message.content
            st.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

# # selecting a specific document
# DATA_PATH = "data"

# if os.path.exists(DATA_PATH):
#     files = [ f for f in os.listdir(DATA_PATH) if f.endswith((".pdf", ".docx"))]
# else:
#     files = []
#     st.error("Data folder empty")
# # if files:
# #     selected_doc = st.selectbox("Select document:", files)
# #     file_path = os.path.join("data", selected_doc)
# # 2. Create a layout for the "Plus" button and the Chat
# # We use a popover to hide the file list until the "+" is clicked
# # with st.sidebar:
# #     st.title("📎 Attachments")
# #     if files:
# #         selected_file = st.selectbox("Attach a document to your next message:", ["None"] + files)
# #     else:
# #         st.info("No documents found in 'data' folder.")

# # # 3. Chat Input Area
# # if prompt := st.chat_input("Type your message..."):
    
# #     # Check if a document is attached
# #     context = ""
# #     if selected_file != "None":
# #         with st.status(f"Reading {selected_file}...", expanded=False):
# #             file_path = os.path.join(DATA_PATH, selected_file)
# #             raw_text = get_document_text(file_path)
# #             chunks = get_text_chunks(raw_text)
# #             vector_store = get_vector_store(chunks)
            
# #             # Find the parts of the doc related to the user's "few words"
# #             docs = vector_store.similarity_search(prompt, k=3)
# #             context = "\n".join([doc.page_content for doc in docs])

# #     # 4. Display user message
# #     st.session_state.messages.append({"role": "user", "content": prompt})
# #     with st.chat_message("user"):
# #         st.markdown(prompt)
# #         if selected_file != "None":
# #             st.caption(f"📎 Attached: {selected_file}")

# #     # 5. Generate AI Response with Context
# #     with st.chat_message("assistant"):
# #         # We tell the AI: Use the document context ONLY IF it exists
# #         system_instructions = "You are a legal assistant."
# #         if context:
# #             system_instructions += f"\n\nUse this document context to help answer:\n{context}"

# #         response = client.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[
# #                 {"role": "system", "content": system_instructions},
# #                 {"role": "user", "content": prompt}
# #             ]
# #         )
# #         # ... (rest of your response logic)

# # 1. THE "PLUS SIGN" POPOVER
# # We place this right above or beside the chat input
# col1, col2 = st.columns([0.1, 0.9])

# with col1:
#     with st.popover("➕"):
#         st.markdown("**Attach Document**")
#         files = [f for f in os.listdir("data") if f.endswith(('.pdf', '.docx'))]
#         selected_file = st.radio("Choose a file to analyze:", ["None"] + files)

# with col2:
#     prompt = st.chat_input("Ask a question or give instructions about the file...")

# # 2. THE LOGIC
# if prompt:
#     context = ""
#     if selected_file != "None":
#         # This is where the RAG magic happens
#         with st.spinner(f"Analyzing {selected_file}..."):
#             path = os.path.join("data", selected_file)
#             raw_text = get_document_text(path)
#             chunks = get_text_chunks(raw_text)
#             vs = get_vector_store(chunks)
            
#             # Find the most relevant parts of the doc
#             relevant_docs = vs.similarity_search(prompt, k=3)
#             context = "\n".join([d.page_content for d in relevant_docs])

#     # Extract the text
#     raw_text = get_document_text(file_path)
#     chunks = get_text_chunks(raw_text)

#     st.success(f"Successfully processed {len(chunks)} sections of the document.")