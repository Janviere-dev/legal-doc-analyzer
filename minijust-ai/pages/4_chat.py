import streamlit as st
import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from utils import load_vector_store, search_documents
from groq import Groq

load_dotenv()

st.set_page_config(
    page_title="Legal Chat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add branding to the sidebar
with st.sidebar:
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

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_files" not in st.session_state:
    st.session_state.selected_files = []

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_registry():
    """Load document registry"""
    registry_file = "data/document_registry.json"
    if os.path.exists(registry_file):
        with open(registry_file, 'r') as f:
            return json.load(f)
    return {}


def get_groq_client() -> Groq:
    """Initialize Groq client"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    return Groq(api_key=api_key)


def scout_phase(user_question: str, groq_client: Groq) -> str:
    """
    Phase 1: Use Groq to extract search terms and identify relevant legal categories
    """
    scout_prompt = f"""You are a legal research assistant for the Rwandan Justice System.

The user asked: "{user_question}"

Your task is to identify the most relevant search terms and legal categories to retrieve from a vector database.

Based on this question, identify:
1. Key legal concepts or topics (e.g., Land Law, Penal Code, Family Law, Contract Law, etc.)
2. Specific article numbers or legal references if mentioned
3. Important keywords in English, French, or Kinyarwanda

Return ONLY a concise list of search terms (2-5 terms maximum), separated by commas. Do not answer the question yet.

Example output format: "land ownership, Article 91, ubukode, property rights"

Search terms:"""

    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": scout_prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=200,
    )
    
    return response.choices[0].message.content.strip()


def retrieve_chunks(search_terms: str, selected_files: List[str] = None, top_k: int = 5) -> List[Dict]:
    """
    Phase 2: Retrieve relevant chunks from FAISS vector store
    """
    # Build metadata filter for selected files
    filter_dict = None
    if selected_files and len(selected_files) > 0:
        filter_dict = {"source_file": selected_files}

    # Search in FAISS using utils.search_documents
    # Filtering is handled inside search_documents with progressive over-fetching.
    documents = search_documents(search_terms, k=top_k, filter_dict=filter_dict)
    
    # Convert to chunk format
    chunks = []
    for doc in documents:
        chunks.append({
            "text": doc.page_content,
            "source_file": doc.metadata.get("source_file", "Unknown"),
            "doc_type": doc.metadata.get("doc_type", "Unknown"),
            "language": doc.metadata.get("language", "en"),
            "page": doc.metadata.get("page", 0),
            "article_number": doc.metadata.get("article_number", ""),
            "unit_header": doc.metadata.get("article_title", ""),
            "distance": 0.0,  # FAISS uses similarity, not distance in our abstraction
        })
    
    return chunks


def format_retrieved_data(chunks: List[Dict]) -> str:
    """Format chunks for inclusion in the prompt"""
    if not chunks:
        return "No relevant documents found in the database."
    
    formatted = "RETRIEVED LEGAL DOCUMENTS:\n\n"
    for i, chunk in enumerate(chunks, 1):
        formatted += f"--- Document {i} ---\n"
        formatted += f"Source: {chunk['source_file']}\n"
        formatted += f"Type: {chunk['doc_type']}\n"
        formatted += f"Language: {chunk['language']}\n"
        formatted += f"Page: {chunk['page']}\n"
        
        if chunk['article_number']:
            formatted += f"Article: {chunk['article_number']}\n"
        if chunk['unit_header']:
            formatted += f"Section: {chunk['unit_header']}\n"
        
        formatted += f"\nContent:\n{chunk['text']}\n\n"
    
    return formatted


def answer_phase(user_question: str, retrieved_data: str, groq_client: Groq) -> str:
    """
    Phase 3: Use Groq to answer the question based on retrieved chunks
    """
    system_prompt = """You are an expert legal assistant for the Rwandan Justice System. Your role is to provide DIRECT, CLEAR answers to legal questions using the provided document excerpts.

CRITICAL INSTRUCTIONS:

1. **ANSWER FIRST, DON'T JUST CITE**: 
   - DO NOT just tell the user "Article X says..." or "You can find this in..."
   - DIRECTLY answer their question by QUOTING and EXPLAINING the relevant legal text
   - Extract and present the ACTUAL content they need to know
   
2. **Use the Actual Legal Text**:
   - Quote the relevant parts of articles/laws DIRECTLY
   - Explain what those quotes mean in practical terms
   - If the law says "A person must do X, Y, Z", tell them: "You must do X, Y, and Z"
   
3. **Answer Structure** (MUST follow this order):
   
   [Give a clear, actionable answer in 2-3 sentences. State exactly what the law says about their question.]
   
   [Quote the relevant article/section directly from the documents. Use quotation marks for exact text.]
   
   [Explain what this means in plain language. Break down requirements, procedures, or implications.]
   
   [List the source documents: filename, article number, page number]

# 4. **Practical Example**:
#    ❌ BAD: "According to Article 4, you can find the criteria in the document..."
#    ✅ GOOD: "To settle persons in Rwanda, you must meet these criteria: (1) Be a Rwandan citizen or legally recognized refugee, (2) Have proper identification documents, (3) Demonstrate economic capability. This is stated in Article 4 which specifies..."

5. **Language**: Respond in the same language as the question. Preserve legal terminology accurately.

6. **If Information is Missing**: Say "Based on the documents I have access to, I don't have specific information about [topic]. However, what I can tell you is..." Then provide related information if available."""

    user_prompt = f"""{retrieved_data}

USER QUESTION:
{user_question}

Provide a complete answer with the actual legal content, not just references to where it can be found."""

    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=2000,
    )
    
    return response.choices[0].message.content.strip()


# ============================================================
# MAIN UI
# ============================================================

st.title("🏛️ Legal Document Chat")
st.write("Ask questions about your indexed Rwandan legal documents")

# Check if FAISS index exists
vector_store = load_vector_store()
if not vector_store:
    st.warning("⚠️ No documents indexed yet. Please upload documents in the **Upload** page first.")
    st.stop()

# File selection from library
st.sidebar.header("📚 Document Selection")

# Load registry to show indexed documents
registry = load_registry()
if registry:
    st.sidebar.write("Select specific documents to search (leave empty for all):")
    
    # Create checkboxes for each indexed file
    selected = []
    for filename, info in registry.items():
        label = f"{filename} ({info['doc_type']}, {info['num_chunks']} chunks)"
        if st.sidebar.checkbox(label, key=f"file_{filename}"):
            selected.append(filename)
    
    st.session_state.selected_files = selected
    
    if selected:
        st.sidebar.success(f"✅ {len(selected)} document(s) selected")
    else:
        st.sidebar.info("🔍 Searching all indexed documents")
else:
    st.sidebar.warning("No documents in registry. Upload documents in the **Upload** page.")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a legal question..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process the query
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyzing your question..."):
            try:
                # Initialize Groq client
                groq_client = get_groq_client()
                
                # Phase 1: Scout - Extract search terms
                with st.status("Processing your question...", expanded=True) as status:
                    st.write("🔎 Phase 1: Identifying relevant legal categories...")
                    search_terms = scout_phase(prompt, groq_client)
                    st.write(f"**Search terms identified**: {search_terms}")
                    
                    # Phase 2: Retrieve relevant chunks from FAISS
                    st.write("📚 Phase 2: Retrieving relevant documents from FAISS index...")
                    chunks = retrieve_chunks(
                        search_terms, 
                        st.session_state.selected_files,
                        top_k=5
                    )
                    st.write(f"**Retrieved**: {len(chunks)} document chunks")
                    
                    # Phase 3: Generate answer
                    st.write("💡 Phase 3: Generating answer with Groq LLM...")
                    retrieved_data = format_retrieved_data(chunks)
                    answer = answer_phase(prompt, retrieved_data, groq_client)
                    
                    status.update(label="✅ Analysis complete!", state="complete", expanded=False)
                
                # Display the answer
                st.markdown(answer)
                
                # Show sources in an expander
                if chunks:
                    with st.expander("📖 View Sources"):
                        for i, chunk in enumerate(chunks, 1):
                            st.markdown(f"**Source {i}**: {chunk['source_file']}")
                            st.markdown(f"- Type: {chunk['doc_type']}")
                            st.markdown(f"- Page: {chunk['page']}")
                            if chunk['article_number']:
                                st.markdown(f"- Article: {chunk['article_number']}")
                            st.markdown("---")
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except ValueError as e:
                error_msg = f"⚠️ Configuration Error: {str(e)}\n\nPlease add GROQ_API_KEY to your .env file."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Clear chat button in sidebar
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Settings in sidebar
with st.sidebar.expander("⚙️ Advanced Settings"):
    st.write("**Current Configuration:**")
    st.code(f"""
Vector Store: FAISS (./faiss_index/)
Embedding Model: {os.getenv('EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')}
LLM Model: llama-3.3-70b-versatile (Groq)
    """)
    
    # Show indexed documents summary
    if registry:
        st.write("**Indexed Documents:**")
        for filename, info in registry.items():
            st.write(f"- {filename}: {info['num_chunks']} chunks")

