# import PyPDF2
# from docx import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS
# from langchain_huggingface import HuggingFaceEmbeddings 

# # Intialize embeddings
# embeddings = HuggingFaceEmbeddings(model_name = "all-MiniM-L6-v2")

# @st.cache_resource  # this make it fast
# def get_vector_store(text_chunks):

#     get_vector_store = FAISS.from_texts(text_chunks, embedding = embeddings)
#     return get_vector_store

# def get_document_text(file_path):
#     text = ""
#     extension = file_path.split(".")[-1].lower()
    
#     if extension == "pdf":
#         with open(file_path, "rb") as f:
#             reader = PyPDF2.PdfReader(f)
#             for page in reader.pages:
#                 content = page.extract_text()
#                 if content:
#                     text += content

#     elif extension == "docx":
#         doc = Document(file_path)
#         for para in doc.paragraphs:
#            text += para.text + "\n" 
    
#     return text

# def get_text_chunks(text):
#     # this splits the text into bite-sized pieces for the AI
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size = 1000,
#         chunk_overlap = 200,
#         length_function = len
#     )
#     return text_splitter.split_text(text)


