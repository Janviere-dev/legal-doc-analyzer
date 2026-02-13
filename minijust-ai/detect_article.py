"""
Article detection for legal documents.
Detects articles using pattern matching for multilingual legal documents.
Supports English (Article), French (Article), and Kinyarwanda (Ingingo).
"""

import re
from parse_pdf import parse_pdf_words
from collections import defaultdict


def detect_articles(text):
  
    articles = []
    
    # Patterns for article headers (multilingual)
    patterns = [
        # English: "Article 1", "Article One", "ARTICLE 1"
        r'(?:Article|ARTICLE|Art\.?)\s+(\d+|[IVX]+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)',
        
        # French: "Article 1", "Article premier"
        r'(?:Article|ARTICLE)\s+(\d+|premier|première)',
        
        # Kinyarwanda: "Ingingo ya mbere", "Ingingo ya 2"
        r'Ingingo\s+ya\s+(\d+|mbere|kabiri|gatatu|kane|gatanu)',
        
        # Simple numbered format: "1.", "2.", "3." at line start
        r'^(\d+)\.\s',
    ]
    
    combined_pattern = '|'.join(f'({p})' for p in patterns)
    
    for match in re.finditer(combined_pattern, text, re.MULTILINE | re.IGNORECASE):
        # Extract the article number from whichever group matched
        article_num = None
        for group in match.groups():
            if group and not group.startswith(('Article', 'ARTICLE', 'Art', 'Ingingo')):
                article_num = group
                break
        
        if article_num:
            articles.append({
                'number': article_num,
                'start_pos': match.start(),
                'matched_text': match.group(0)
            })
    
    # Extract content for each article
    for i, article in enumerate(articles):
        start = article['start_pos']
        # Content goes until the next article or end of document
        end = articles[i + 1]['start_pos'] if i + 1 < len(articles) else len(text)
        
        article['content'] = text[start:end].strip()
        
        # Try to extract title (first line after article number)
        lines = article['content'].split('\n')
        if len(lines) > 1:
            article['title'] = lines[1].strip()
        else:
            article['title'] = ''
    
    return articles


def detect_articles_from_pdf(pdf_path):
  
    pages_data = parse_pdf_words(pdf_path)
    
    result = defaultdict(list)
    
    for page_data in pages_data:
        page_num = page_data['page_num']
        words = page_data['words']
        
        # Extract text from page
        page_text = ' '.join(word['text'] for word in words if 'text' in word)
        
        # Detect articles on this page
        articles = detect_articles(page_text)
        
        if articles:
            result[page_num] = articles
    
    return dict(result)


if __name__ == "__main__":
    import sys
    
    pdf_path = "data/MINISTERIAL INSTRUCTIONS No 001_07.01 OF 30_06_2025 RELATING TO THE SETTLING OF PERSONS (1).pdf"  # Change this to your PDF file path

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    print(f"Analyzing PDF: {pdf_path}")
    
    print("Testing article detection:")
    print("=" * 80)
    
    pdf_articles = detect_articles_from_pdf(pdf_path)
    
    for page_num, Ingingo in pdf_articles.items():
        print(f"\n{'='*60}")
        print(f"PAGE {page_num}: Found {len(Ingingo)} article(s)")
        print('='*60)
        
        for article in Ingingo:
            print(f"\nArticle {article['number']}:")
            print(f"  Matched: {article['matched_text']}")
            print(f"  Title: {article['title']}")
            print(f"  Content length: {len(article['content'])} characters")
            print(f"  Content preview: {article['content'][:500]}...")
    
    print("\n" + "=" * 80)
    print("Analysis complete!") 
    