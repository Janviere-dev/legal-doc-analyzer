"""
Analyze Kinyarwanda article detection in PDF
Shows statistics on detected articles
"""

from create_chunks import DocumentChunker
import sys


def analyze_kinyarwanda_articles(pdf_path):
    """Analyze and display Kinyarwanda article detection results"""
    
    print("=" * 80)
    print(f"ANALYZING KINYARWANDA ARTICLES IN:")
    print(f"{pdf_path}")
    print("=" * 80)
    print()
    
    # Create chunks
    chunker = DocumentChunker(pdf_path, doc_type='legislation')
    chunks = chunker.create_chunks()
    
    # Analyze chunks
    total_chunks = len(chunks)
    kinyarwanda_articles = []
    english_articles = []
    french_articles = []
    non_article_chunks = []
    
    for chunk in chunks:
        metadata = chunk['metadata']
        article_num = metadata.get('article_number')
        lang = metadata.get('language')
        
        if article_num:
            # Extract article info
            article_info = {
                'number': article_num,
                'page': metadata.get('page'),
                'column': metadata.get('column'),
                'title': metadata.get('article_title', ''),
                'word_count': metadata.get('word_count', 0),
                'chunk_id': chunk['chunk_id']
            }
            
            if lang == 'rw':
                kinyarwanda_articles.append(article_info)
            elif lang == 'en':
                english_articles.append(article_info)
            elif lang == 'fr':
                french_articles.append(article_info)
        else:
            non_article_chunks.append(chunk)
    
    # Display statistics
    print(f"📊 STATISTICS")
    print("-" * 80)
    print(f"Total chunks created: {total_chunks}")
    print(f"  - Kinyarwanda articles: {len(kinyarwanda_articles)} 🎯")
    print(f"  - English articles: {len(english_articles)}")
    print(f"  - French articles: {len(french_articles)}")
    print(f"  - Non-article chunks: {len(non_article_chunks)}")
    print()
    
    # Display Kinyarwanda articles
    if kinyarwanda_articles:
        print(f"📝 KINYARWANDA ARTICLES DETECTED ({len(kinyarwanda_articles)} articles)")
        print("-" * 80)
        
        # Group by article number
        article_groups = {}
        for article in kinyarwanda_articles:
            num = article['number']
            if num not in article_groups:
                article_groups[num] = []
            article_groups[num].append(article)
        
        # Sort by article number
        sorted_articles = sorted(article_groups.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999)
        
        for article_num, article_list in sorted_articles:
            if len(article_list) == 1:
                article = article_list[0]
                print(f"  Ingingo ya {article_num:>3}  |  Page {article['page']}  |  Col {article['column']}  |  {article['word_count']} words")
                if article['title']:
                    print(f"                    Title: {article['title'][:60]}")
            else:
                # Multiple chunks for same article (split article)
                print(f"  Ingingo ya {article_num:>3}  |  Split into {len(article_list)} chunks:")
                for i, article in enumerate(article_list):
                    print(f"                    Chunk {i+1}: Page {article['page']}, Col {article['column']}, {article['word_count']} words")
        
        print()
    
    # Display English/French articles (if any)
    if english_articles:
        print(f"📄 ENGLISH ARTICLES ({len(english_articles)} articles)")
        print("-" * 80)
        for article in english_articles[:10]:  # Show first 10
            print(f"  Article {article['number']:>3}  |  Page {article['page']}  |  {article['word_count']} words")
        if len(english_articles) > 10:
            print(f"  ... and {len(english_articles) - 10} more")
        print()
    
    if french_articles:
        print(f"📄 FRENCH ARTICLES ({len(french_articles)} articles)")
        print("-" * 80)
        for article in french_articles[:10]:  # Show first 10
            print(f"  Article {article['number']:>3}  |  Page {article['page']}  |  {article['word_count']} words")
        if len(french_articles) > 10:
            print(f"  ... and {len(french_articles) - 10} more")
        print()
    
    # Coverage analysis
    print(f"📈 COVERAGE ANALYSIS")
    print("-" * 80)
    kiny_coverage = (len(kinyarwanda_articles) / total_chunks * 100) if total_chunks > 0 else 0
    print(f"Kinyarwanda article coverage: {kiny_coverage:.1f}% of all chunks")
    
    if kinyarwanda_articles:
        # Find gaps in article numbering
        article_numbers = sorted([int(a['number']) for a in kinyarwanda_articles if a['number'].isdigit()])
        if article_numbers:
            print(f"Article range: Ingingo ya {article_numbers[0]} to Ingingo ya {article_numbers[-1]}")
            
            # Check for gaps
            expected_range = set(range(article_numbers[0], article_numbers[-1] + 1))
            actual_numbers = set(article_numbers)
            missing = sorted(expected_range - actual_numbers)
            
            if missing:
                print(f"⚠️  Missing articles: {missing}")
            else:
                print(f"✅ Complete sequence - no gaps detected")
    
    print()
    print("=" * 80)
    
    return chunks


if __name__ == '__main__':
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "data/MINISTERIAL INSTRUCTIONS No 001_07.01 OF 30_06_2025 RELATING TO THE SETTLING OF PERSONS (1).pdf"
    
    chunks = analyze_kinyarwanda_articles(pdf_path)
