"""
View full chunk content to see actual article text
"""

from create_chunks import create_chunks_from_pdf
import json


def view_chunks(pdf_path: str, num_chunks: int = 5):
    """View full content of first N chunks"""
    
    print(f"\n{'='*80}")
    print(f"VIEWING CHUNKS FROM: {pdf_path}")
    print(f"{'='*80}\n")
    
    chunks = create_chunks_from_pdf(pdf_path)
    
    for i, chunk in enumerate(chunks[:num_chunks], 1):
        print(f"\n{'─'*80}")
        print(f"CHUNK {i}/{len(chunks)}")
        print(f"{'─'*80}")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"\nMetadata:")
        print(json.dumps(chunk['metadata'], indent=2))
        print(f"\n📄 FULL TEXT:")
        print(f"{'─'*80}")
        print(chunk['text'])
        print(f"{'─'*80}")
        print(f"Character count: {len(chunk['text'])}")
        print(f"Word count: {chunk['metadata']['word_count']}")
    
    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        num_chunks = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        view_chunks(pdf_path, num_chunks)
    else:
        # Default: show first 10 chunks from legislation
        view_chunks("data/MINISTERIAL INSTRUCTIONS No 001_07.01 OF 30_06_2025 RELATING TO THE SETTLING OF PERSONS (1).pdf", 10)
