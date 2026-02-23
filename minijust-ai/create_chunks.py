"""
Document Chunking System for Rwandan Legal Documents
Creates chunks with metadata: doc_id, language, page, column, article_number
Uses LangChain for intelligent text splitting
"""

import re
import hashlib
from typing import List, Dict
from parse_pdf import parse_pdf_words
from detect_column import detect_columns_all_pages, reconstruct_text_reading_order
from detect_language import detect_language
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Chunk legal documents with metadata"""
    
    def __init__(self, pdf_path: str, doc_type: str = 'auto'):
        self.pdf_path = pdf_path
        self.doc_type = doc_type
        self.doc_id = hashlib.md5(pdf_path.encode()).hexdigest()[:12]
        
        # Initialize LangChain text splitter with custom separators for Kinyarwanda legal documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n\nIngingo ya",     # Kinyarwanda article (primary)
                "\nIngingo ya",       # Kinyarwanda article (single newline)
                "\n\nUMUTWE",         # Kinyarwanda chapter
                "\n\nICYICIRO",       # Kinyarwanda section  
                "\n\nArticle",        # English/French article
                "\n\n",               # Double newline (paragraph)
                "\n",                 # Single newline
                ". ",                 # Sentence
                " ",                  # Word
                "",                   # Character
            ],
            chunk_size=1500,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
    
    def _detect_document_type(self, pages_data: List[Dict]) -> str:
        """Auto-detect legislation vs case law - prioritizing Kinyarwanda patterns"""
        pdf_document = pages_data[:min(3, len(pages_data))]
        article_count = 0
        case_indicators = 0
        
        for page_data in pdf_document:
            text = ' '.join(word['text'] for word in page_data['words'] if 'text' in word)
            
            # Count Kinyarwanda article patterns (primary)
            article_count += len(re.findall(r'Ingingo\s+ya\s+(\d+|mbere|kabiri|gatatu|kane|gatanu)', text, re.IGNORECASE))
            
            # Count English/French articles (secondary)
            article_count += len(re.findall(r'\bArticle\s+\d+', text, re.IGNORECASE))
            
            # Check for Kinyarwanda legislation indicators
            if re.search(r'(UMUTWE|ICYICIRO|Amabwiriza|Iteka)', text):
                article_count += 2
        
            # Check for case law indicators
            if re.search(r'\s+v\.\s+|\b(plaintiff|defendant|appellant|respondent)\b', text, re.IGNORECASE):
                case_indicators += 1
        
        return 'legislation' if article_count >= 3 else 'case_law' if case_indicators >= 2 else 'legislation'
    
    def _detect_articles(self, text: str) -> List[Dict]:
        """Detect articles - primarily focused on Kinyarwanda patterns"""
        articles = []
        
        for match in re.finditer(r'Ingingo\s+ya\s+mbere', text, re.IGNORECASE):
            articles.append({
                'number': '1',
                'start_pos': match.start(),
                'matched_text': match.group(0),
                'language': 'rw'
            })
        
        # Pattern 2: "Ingingo ya [number]" (e.g., Ingingo ya 2, Ingingo ya 15)
        for match in re.finditer(r'Ingingo\s+ya\s+(\d+)', text, re.IGNORECASE):
            # Skip if already captured
            if not any(abs(a['start_pos'] - match.start()) < 5 for a in articles):
                articles.append({
                    'number': match.group(1),
                    'start_pos': match.start(),
                    'matched_text': match.group(0),
                    'language': 'rw'
                })
        
        # Pattern 3: Kinyarwanda number words for articles 2-10
        kiny_numbers = {
            'kabiri': '2',
            'gatatu': '3', 
            'kane': '4',
            'gatanu': '5',
            'gatandatu': '6',
            'karindwi': '7',
            'umunani': '8',
            'icyenda': '9',
            'icumi': '10'
        }
        
        for kiny_word, number in kiny_numbers.items():
            pattern = rf'Ingingo\s+ya\s+{kiny_word}'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if not any(abs(a['start_pos'] - match.start()) < 5 for a in articles):
                    articles.append({
                        'number': number,
                        'start_pos': match.start(),
                        'matched_text': match.group(0),
                        'language': 'rw'
                    })
        
        return sorted(articles, key=lambda x: x['start_pos'])
    
    def _extract_article_content(self, text: str, articles: List[Dict]):
        """Extract content for each article"""
        for i, article in enumerate(articles):
            start = article['start_pos']
            end = articles[i + 1]['start_pos'] if i + 1 < len(articles) else len(text)
            article['content'] = text[start:end].strip()
            article['title'] = article['content'].split('\n')[1].strip() if '\n' in article['content'] else ''
    
    def _chunk_by_articles(self, pages_data: List[Dict]) -> List[Dict]:
        """Chunk legislation by articles within columns using LangChain"""
        chunks = []
        columns_all_pages = detect_columns_all_pages(self.pdf_path)
        
        for page_idx, page_data in enumerate(pages_data):
            page_num = page_data['page_num']
            page_columns = columns_all_pages[page_idx]['columns']
            
            for column in page_columns:
                column_text = reconstruct_text_reading_order(column)
                if not column_text.strip():
                    continue
                
                # Detect articles in the column
                articles = self._detect_articles(column_text)
                
                if not articles:
                    # No articles detected - use LangChain to split intelligently
                    text_chunks = self.text_splitter.split_text(column_text)
                    for idx, chunk_text in enumerate(text_chunks):
                        chunks.append({
                            'doc_id': self.doc_id,
                            'chunk_id': f"{self.doc_id}_p{page_num}_col{column['column_num']}_chunk{idx}",
                            'text': chunk_text,
                            'metadata': {
                                'doc_type': 'legislation',
                                'page': page_num,
                                'column': column['column_num'],
                                'language': column['language'],
                                'article_number': None,
                                'word_count': len(chunk_text.split())
                            }
                        })
                else:
                    # Articles detected - chunk each article separately
                    self._extract_article_content(column_text, articles)
                    for article in articles:
                        article_text = article['content']
                        
                        # If article is too long, use LangChain to split it
                        if len(article_text.split()) > 500:
                            sub_chunks = self.text_splitter.split_text(article_text)
                            for sub_idx, sub_chunk in enumerate(sub_chunks):
                                chunks.append({
                                    'doc_id': self.doc_id,
                                    'chunk_id': f"{self.doc_id}_p{page_num}_col{column['column_num']}_art{article['number']}_sub{sub_idx}",
                                    'text': sub_chunk,
                                    'metadata': {
                                        'doc_type': 'legislation',
                                        'page': page_num,
                                        'column': column['column_num'],
                                        'language': column['language'],
                                        'article_number': article['number'],
                                        'article_title': article.get('title', ''),
                                        'sub_chunk': sub_idx,
                                        'word_count': len(sub_chunk.split())
                                    }
                                })
                        else:
                            # Article is manageable size - keep as single chunk
                            chunks.append({
                                'doc_id': self.doc_id,
                                'chunk_id': f"{self.doc_id}_p{page_num}_col{column['column_num']}_art{article['number']}",
                                'text': article_text,
                                'metadata': {
                                    'doc_type': 'legislation',
                                    'page': page_num,
                                    'column': column['column_num'],
                                    'language': column['language'],
                                    'article_number': article['number'],
                                    'article_title': article.get('title', ''),
                                    'word_count': len(article_text.split())
                                }
                            })
        
        return chunks
    
    def _detect_sections(self, text: str) -> List[Dict]:
        """Detect sections in case law (I. FACTS, II. LAW, etc.)"""
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            # Roman numerals: "I. FACTS"
            if match := re.match(r'^([IVX]+)\.\s+(.+?)$', line):
                sections.append({'number': match.group(1), 'title': match.group(2).strip(), 'line_num': i})
            # Capitalized headers: "FACTS:"
            elif match := re.match(r'^([A-Z][A-Z\s]{2,}):?\s*$', line):
                if len(line) > 3:
                    sections.append({'number': None, 'title': match.group(1).strip(), 'line_num': i})
        
        return sections
    
    def _chunk_by_sections(self, pages_data: List[Dict]) -> List[Dict]:
        """Chunk case law by sections"""
        chunks = []
        full_text, page_line_map = [], []
        
        for page_data in pages_data:
            page_text = ' '.join(word['text'] for word in page_data['words'] if 'text' in word)
            for line in page_text.split('\n'):
                full_text.append(line)
                page_line_map.append(page_data['page_num'])
        
        full_text_str = '\n'.join(full_text)
        sections = self._detect_sections(full_text_str)
        
        if not sections:
            # Fallback to page-based chunks
            for page_data in pages_data:
                page_text = ' '.join(word['text'] for word in page_data['words'] if 'text' in word)
                lang = detect_language(page_data)[0] if detect_language(page_data) else 'unknown'
                chunks.append({
                    'doc_id': self.doc_id,
                    'chunk_id': f"{self.doc_id}_page{page_data['page_num']}",
                    'text': page_text,
                    'metadata': {
                        'doc_type': 'case_law',
                        'page': page_data['page_num'],
                        'language': lang,
                        'word_count': len(page_text.split())
                    }
                })
        else:
            # Section-based chunks
            full_text_lines = full_text_str.split('\n')
            for i, section in enumerate(sections):
                start = section['line_num']
                end = sections[i + 1]['line_num'] if i + 1 < len(sections) else len(full_text_lines)
                section_text = '\n'.join(full_text_lines[start:end]).strip()
                
                # Detect language
                try:
                    import langid
                    langid.set_languages(['en', 'fr', 'rw'])
                    lang = langid.classify(section_text)[0] if len(section_text) > 20 else 'unknown'
                except:
                    lang = 'unknown'
                
                chunks.append({
                    'doc_id': self.doc_id,
                    'chunk_id': f"{self.doc_id}_section{i}",
                    'text': section_text,
                    'metadata': {
                        'doc_type': 'case_law',
                        'page': page_line_map[start] if start < len(page_line_map) else 0,
                        'language': lang,
                        'section_title': section['title'],
                        'section_number': section.get('number'),
                        'word_count': len(section_text.split())
                    }
                })
        
        return chunks
    
    def create_chunks(self) -> List[Dict]:
        """Create chunks from PDF"""
        pages_data = parse_pdf_words(self.pdf_path)
        if not pages_data:
            return []
        
        if self.doc_type == 'auto':
            self.doc_type = self._detect_document_type(pages_data)
            print(f"Auto-detected: {self.doc_type}")
        
        chunks = self._chunk_by_articles(pages_data) if self.doc_type == 'legislation' else self._chunk_by_sections(pages_data)
        print(f"Created {len(chunks)} chunks")
        return chunks


def create_chunks_from_pdf(pdf_path: str, doc_type: str = 'auto') -> List[Dict]:
    """Create chunks from PDF - main entry point"""
    return DocumentChunker(pdf_path, doc_type).create_chunks()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        doc_type = sys.argv[2] if len(sys.argv) > 2 else 'auto'
        chunks = create_chunks_from_pdf(pdf_path, doc_type)
        print(f"\nTotal chunks: {len(chunks)}")
        
        if chunks:
            print("\n--- CONTENT PREVIEW ---")
            
            # 1. Show detected articles (Prioritized)
            article_chunks = [c for c in chunks if c['metadata'].get('article_number')]
            if article_chunks:
                print(f"\n>>> DETECTED KINYARWANDA ARTICLES (Found {len(article_chunks)}):")
                
                # Filter for Article 1 specifically to show the difference between TOC and Real Content
                art1_chunks = [c for c in article_chunks if c['metadata']['article_number'] == '1']
                if art1_chunks:
                    print(f"\n--- FOCUS: Article 1 (Found {len(art1_chunks)} occurrences) ---")
                    for i, chunk in enumerate(art1_chunks):
                        print(f"\n[Occurrence {i+1}] (Page {chunk['metadata']['page']}, Word Count: {chunk['metadata']['word_count']})")
                        print(f"ID: {chunk['chunk_id']}")
                        print(f"Text:\n{chunk['text']}")
                        print("-" * 60)
                
                # Show generic list
                print(f"\n--- OTHER EXAMPLES ---")
                for i, chunk in enumerate(article_chunks[5:8]):  # Show a few others
                     print(f"\n[Article {chunk['metadata']['article_number']}] (Page {chunk['metadata']['page']})")
                     print(f"Text Preview: {chunk['text'][:200]}..." if len(chunk['text']) > 200 else f"Text: {chunk['text']}")
                     print("-" * 60)

            else:
                print("\n>>> NO ARTICLES DETECTED (Check if document is legislation)")

            # 2. Show first few non-article chunks (Headers/Intro)
            intro_chunks = [c for c in chunks if not c['metadata'].get('article_number')][:3]
            if intro_chunks:
                print(f"\n>>> OTHER CHUNKS (Headers/Intro - Showing {len(intro_chunks)}):")
                for i, chunk in enumerate(intro_chunks):
                    print(f"\n[Chunk {i+1}] (ID: {chunk['chunk_id']})")
                    print(f"Text Preview: {chunk['text'][:300]}..." if len(chunk['text']) > 300 else f"Text: {chunk['text']}")
                    print("-" * 60)
    else:
        print("Usage: python create_chunks.py <pdf_path> [doc_type]")
