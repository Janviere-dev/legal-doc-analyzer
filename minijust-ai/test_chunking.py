"""
Test script to analyze chunking results
Shows: total chunks, chunks per page, sample chunks with metadata
"""

from create_chunks import create_chunks_from_pdf
from collections import defaultdict
import json


def analyze_chunks(pdf_path: str, doc_type: str = 'auto'):
    """Analyze and display chunking results"""
    
    print(f"\n{'='*80}")
    print(f"ANALYZING: {pdf_path}")
    print(f"{'='*80}\n")
    
    # Create chunks
    chunks = create_chunks_from_pdf(pdf_path, doc_type)
    
    if not chunks:
        print("No chunks created!")
        return
    
    # Group chunks by page
    chunks_by_page = defaultdict(list)
    for chunk in chunks:
        page = chunk['metadata']['page']
        chunks_by_page[page].append(chunk)
    
    # Summary statistics
    print(f"\n📊 SUMMARY:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Total pages: {len(chunks_by_page)}")
    print(f"  Average chunks per page: {len(chunks) / len(chunks_by_page):.1f}")
    
    # Chunks per page breakdown
    print(f"\n📄 CHUNKS PER PAGE:")
    for page in sorted(chunks_by_page.keys()):
        page_chunks = chunks_by_page[page]
        print(f"  Page {page}: {len(page_chunks)} chunks")
    
    # Language distribution
    languages = defaultdict(int)
    for chunk in chunks:
        lang = chunk['metadata'].get('language', 'unknown')
        languages[lang] += 1
    
    print(f"\n🌍 LANGUAGE DISTRIBUTION:")
    for lang, count in sorted(languages.items()):
        percentage = (count / len(chunks)) * 100
        print(f"  {lang}: {count} chunks ({percentage:.1f}%)")
    
    # Article distribution (for legislation)
    if chunks[0]['metadata'].get('article_number'):
        articles_with_nums = [c for c in chunks if c['metadata'].get('article_number')]
        print(f"\n📜 ARTICLES DETECTED:")
        print(f"  Chunks with article numbers: {len(articles_with_nums)}")
        
        # Sample articles
        article_samples = {}
        for chunk in articles_with_nums[:10]:  # First 10
            art_num = chunk['metadata']['article_number']
            if art_num not in article_samples:
                article_samples[art_num] = chunk
        
        print(f"\n  Sample articles:")
        for art_num in sorted(article_samples.keys(), key=lambda x: int(x)):
            chunk = article_samples[art_num]
            text_preview = chunk['text'][:60].replace('\n', ' ')
            print(f"    Article {art_num}: {text_preview}...")
    
    # Sample chunks
    print(f"\n📝 SAMPLE CHUNKS (First 3):")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n  --- Chunk {i} ---")
        print(f"  Chunk ID: {chunk['chunk_id']}")
        print(f"  Metadata: {json.dumps(chunk['metadata'], indent=4)}")
        text_preview = chunk['text'][:150].replace('\n', ' ')
        print(f"  Text preview: {text_preview}...")
        print(f"  Full text length: {len(chunk['text'])} characters")
    
    print(f"\n{'='*80}\n")
    
    return chunks


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        doc_type = sys.argv[2] if len(sys.argv) > 2 else 'auto'
        analyze_chunks(pdf_path, doc_type)
    else:
        # Test with both sample documents
        print("\n🔍 Testing both documents...\n")
        
        analyze_chunks("data/MINISTERIAL INSTRUCTIONS No 001_07.01 OF 30_06_2025 RELATING TO THE SETTLING OF PERSONS (1).pdf", 'legislation')
        
        analyze_chunks("data/IKIGO CYIMISORO N'AMAHORO v. SUGIRA LTD.pdf", 'case_law')
