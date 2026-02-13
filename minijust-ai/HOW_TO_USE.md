# How to Use MINIJUST AI Chat

## The Problem You're Experiencing

If the AI says "I don't see any uploaded documents", it means:
1. Documents aren't uploaded/processed yet, OR
2. Documents are uploaded but not indexed in the vector database, OR
3. Documents aren't selected in the chat interface

## Step-by-Step Guide

### Step 1: Upload and Process Documents

1. Go to the **Upload** page
2. Click "Choose a PDF or DOCX file"
3. Select your legal document
4. **Wait for the success message**: "File processed and stored in vector database successfully!"
5. You should see: "Total chunks Created: X" (where X is a number)

**Important**: If you see an error about Milvus connection, follow the QUICK_FIX.md guide first.

### Step 2: Use the Chat Interface

1. Go to the **New Chat** page
2. In the sidebar, you'll see:
   - **Attached Files** section showing all uploaded documents
   - Files with ✅ are indexed and ready
   - Files with ⚠️ need to be re-uploaded

### Step 3: Select Documents (Optional but Recommended)

1. In the sidebar under "Attached Files"
2. Use the dropdown to select which documents to analyze
3. You'll see: "📄 X file(s) attached"
4. Selected files will be used for your questions

**Note**: If you don't select any files, ALL indexed documents will be searched automatically.

### Step 4: Ask Questions

1. Type your question in the chat input
2. The system will:
   - Search your documents for relevant content
   - Show which documents are being searched
   - Provide answers with source citations

## Understanding the Status Indicators

### In the Sidebar:
- ✅ **Green checkmark**: Document is indexed and ready
- ⚠️ **Warning icon**: Document exists but isn't indexed (needs re-upload)

### In the Main Chat:
- 📎 **Active Documents**: Documents you've selected
- 📚 **Auto-search mode**: All documents will be searched
- ⚠️ **Warning**: Documents found but not indexed

## Common Issues and Solutions

### Issue: "I don't see any uploaded documents"

**Solution**:
1. Check if files are in the `data/` folder
2. Go to Upload page and re-upload the files
3. Make sure you see "File processed successfully" message
4. Go back to New Chat and check the sidebar

### Issue: "No relevant content found"

**Possible causes**:
1. Documents aren't indexed - Re-upload them
2. Question doesn't match document content - Try rephrasing
3. Milvus connection issue - Check QUICK_FIX.md

### Issue: Files show ⚠️ (not indexed)

**Solution**:
1. Go to Upload page
2. Re-upload the file
3. Wait for "File processed successfully" message
4. Return to New Chat - it should show ✅

## Best Practices

1. **Always check the Upload page first** - Make sure documents are processed
2. **Select specific files** - For focused analysis on particular cases
3. **Use clear questions** - Ask specific questions about articles, cases, or legal concepts
4. **Check sources** - Click "📚 Sources" to see which documents were used

## Example Workflow

1. Upload case document: "IKIGO CYIMISORO N'AMAHORO v. SUGIRA LTD.pdf"
2. Wait for processing confirmation
3. Go to New Chat
4. Select the uploaded file from sidebar
5. Ask: "What are the main legal issues in this case?"
6. Review the answer and sources

## Need Help?

- Check QUICK_FIX.md for Milvus connection issues
- Check SETUP.md for installation help
- Make sure your `.env` file is configured correctly


