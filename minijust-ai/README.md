# MINIJUST AI - Legal Document Analyzer

An AI-powered legal document analysis system designed to help judges, prosecutors, and lawyers in Rwanda analyze legal cases efficiently using advanced RAG (Retrieval-Augmented Generation) technology.

## Features

- 📄 **Document Upload & Processing**: Upload PDF and DOCX legal documents
- 🔍 **Vector Search**: Fast semantic search using Milvus with HNSW indexing
- 💬 **ChatGPT-like Interface**: Modern chat interface for legal case analysis
- 📚 **RAG System**: Retrieval-Augmented Generation for accurate legal references
- 🌍 **Multilingual Support**: Works with French, English, and Kinyarwanda legal documents
- 📊 **Document Library**: Manage and organize uploaded legal documents

## Technology Stack

- **Frontend**: Streamlit
- **LLM**: Groq (Llama 3.3 70B)
- **Vector Database**: Milvus with HNSW indexing
- **Embeddings**: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- **Document Processing**: LangChain

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Milvus

#### Option A: Using Docker (Recommended)

```bash
# Pull Milvus standalone image
docker pull milvusdb/milvus:latest

# Run Milvus
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  -v $(pwd)/volumes/milvus:/var/lib/milvus \
  milvusdb/milvus:latest
```

#### Option B: Using Milvus Lite (For Development)

```bash
pip install milvus
```

Then Milvus will run in-process (no separate server needed).

#### Option C: Using Zilliz Cloud (Cloud Milvus)

1. Sign up at [Zilliz Cloud](https://cloud.zilliz.com/)
2. Create a cluster
3. Get your connection URI and API key
4. Set environment variables (see below)

### 3. Environment Variables

Create a `.env` file in the project root:

```env
# Groq API Key (get from https://console.groq.com/)
GROQ_API_KEY=your_groq_api_key_here

# Milvus Configuration (Optional - defaults to localhost)
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=your_milvus_token_here  # Only needed for cloud Milvus
```

### 4. Run the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage Guide

### 1. Upload Documents

- Navigate to the **Upload** page
- Upload PDF or DOCX legal documents
- Documents are automatically processed, chunked, and stored in Milvus

### 2. Use the New Chat Interface

- Navigate to **New Chat** page (ChatGPT-like interface)
- Select documents from the sidebar to analyze
- Or upload new documents directly from the chat interface
- Ask questions about legal cases, articles, or precedents
- The system will retrieve relevant information and provide analysis

### 3. Use the Old Chat Interface

- Navigate to **Chat** page (original interface)
- Select a document from the dropdown
- Ask questions about the selected document

### 4. Manage Documents

- Navigate to **Library** page
- View all uploaded documents
- Delete or restore documents
- Documents deleted from library are also removed from vector store

## Project Structure

```
minijust-ai/
├── app.py                 # Main Streamlit app
├── pages/
│   ├── 1_home.py         # Home page
│   ├── 2_upload.py       # Document upload page
│   ├── 3_library.py      # Document library management
│   ├── 4_chat.py         # Original chat interface
│   └── 5_new_chat.py     # New ChatGPT-like interface
├── utils.py              # Utility functions (Milvus, embeddings, etc.)
├── data/                 # Uploaded documents storage
├── trash/                # Deleted documents
├── assets/               # Images and static files
└── requirements.txt      # Python dependencies
```

## Key Features Explained

### HNSW Indexing

The system uses Hierarchical Navigable Small World (HNSW) indexing for fast similarity search in Milvus. This is optimized for legal document retrieval with:
- **M=16**: Number of connections per node
- **efConstruction=200**: Index construction parameter
- **ef=64**: Search parameter for query time

### Embedding Model

Uses `paraphrase-multilingual-MiniLM-L12-v2` which:
- Supports 50+ languages including French, English, and Kinyarwanda
- Provides 384-dimensional embeddings
- Optimized for semantic similarity tasks

### RAG Pipeline

1. **Document Ingestion**: Documents are chunked (1000 chars, 200 overlap)
2. **Embedding**: Each chunk is embedded using the multilingual model
3. **Storage**: Embeddings stored in Milvus with metadata
4. **Retrieval**: Query embedded and similar chunks retrieved
5. **Generation**: LLM generates response using retrieved context

## Troubleshooting

### Milvus Connection Issues

If you see connection errors:
1. Ensure Milvus is running: `docker ps | grep milvus`
2. Check MILVUS_URI in `.env` file
3. For cloud Milvus, verify MILVUS_TOKEN is correct

### Embedding Model Download

On first run, the embedding model will be downloaded (~400MB). Ensure you have:
- Stable internet connection
- Sufficient disk space
- Proper permissions

### Memory Issues

If you encounter memory issues:
- Reduce chunk size in `utils.py` (currently 1000)
- Process fewer documents at once
- Use Milvus Lite for smaller datasets

## Contributing

This is a prototype system for the Rwanda Ministry of Justice. For improvements or issues, please contact the development team.

## License

© 2026 MINIJUST AI | A Year of Remarkable Change

