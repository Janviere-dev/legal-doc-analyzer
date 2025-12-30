import streamlit as st 

st.set_page_config(
    page_title = "Home", 
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


st.title(" Welcome to the MINIJUST Research portal")

st.markdown("""
This prototype is designed to transform how we handle legal data at the Ministry of Justice.
**Key Features of this System:**
* **Deep Research:** Powered by Groq & Llama3.
* **Vector Search:** Accurate retrieval using Milvus logic.
* **Secure Ingestion:** Document chunking for precise legal analysis.
""")

st.success(" Please navigate to 'upload' to start adding documents.")