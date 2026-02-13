# Quick Setup Guide

## Prerequisites

1. Python 3.8 or higher
2. Docker (for Milvus) OR Milvus Lite
3. Groq API key (free at https://console.groq.com/)

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The first time you run, the embedding model will be downloaded (~400MB). This may take a few minutes.

### 2. Set Up Milvus

#### Quick Start: Milvus Lite (Easiest for Development)

Milvus Lite runs in-process, no separate server needed:

```bash
pip install milvus
```

Then update your `.env` file:
```env
MILVUS_URI=./milvus_data
```

#### Production: Docker Milvus

```bash
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  -v $(pwd)/volumes/milvus:/var/lib/milvus \
  milvusdb/milvus:latest
```

### 3. Configure Environment

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
MILVUS_URI=http://localhost:19530
# MILVUS_TOKEN=  # Only needed for Zilliz Cloud
```

### 4. Run the Application

```bash
streamlit run app.py
```

Visit `http://localhost:8501`

## Testing the Setup

1. Go to **Upload** page
2. Upload a PDF or DOCX file
3. Check that you see "File processed and stored in vector database successfully!"
4. Go to **New Chat** page
5. Select the uploaded file from sidebar
6. Ask a question about the document
7. Verify you get a response with sources

## Troubleshooting

### "Connection refused" error for Milvus

- **Docker**: Check if container is running: `docker ps | grep milvus`
- **Milvus Lite**: Ensure `MILVUS_URI=./milvus_data` in `.env`
- **Cloud**: Verify `MILVUS_URI` and `MILVUS_TOKEN` are correct

### Embedding model download fails

- Check internet connection
- Try manually: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"`

### "Collection already exists" error

This is normal if you've run the app before. The collection will be reused.

### Import errors

Make sure all dependencies are installed:
```bash
pip install --upgrade -r requirements.txt
```

## Next Steps

1. Upload your legal documents
2. Start analyzing cases in the **New Chat** interface
3. Use the **Library** page to manage documents

