# Quick Fix for Milvus Connection Error

## The Problem
You're seeing: `Fail connecting to server on localhost:19530`

This means Milvus server is not running or not configured.

## Solution: Use Milvus Lite (Easiest - Recommended)

Milvus Lite runs in-process, no separate server needed!

### Step 1: Install Milvus
```bash
pip install milvus
```

### Step 2: Update your .env file

Create or edit `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
MILVUS_URI=./milvus_data
```

**Important**: Change from `http://localhost:19530` to `./milvus_data`

### Step 3: Restart the app
```bash
streamlit run app.py
```

That's it! Milvus Lite will automatically create a local database in the `./milvus_data` folder.

---

## Alternative: Use Docker Milvus

If you prefer a separate Milvus server:

### Step 1: Run Milvus in Docker
```bash
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest
```

### Step 2: Update .env
```env
GROQ_API_KEY=your_groq_api_key_here
MILVUS_URI=http://localhost:19530
```

### Step 3: Verify it's running
```bash
docker ps | grep milvus
```

### Step 4: Restart the app

---

## Verify Your Setup

After fixing, test by:
1. Go to **Upload** page
2. Upload a PDF file
3. You should see: "File processed and stored in vector database successfully!"

If you still see errors, check:
- `.env` file exists and has correct values
- No typos in `MILVUS_URI`
- For Milvus Lite: `milvus` package is installed
- For Docker: Container is running (`docker ps`)

