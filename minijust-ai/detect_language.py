"""
Simple language detection for PDF files.
Uses langid library which supports Kinyarwanda detection.
"""

import langid
from parse_pdf import parse_pdf_words
from collections import Counter

# Configure langid to include Kinyarwanda
langid.set_languages(['en', 'fr', 'rw'])

# Language name mapping
LANGUAGE_NAMES = {
    'en': 'English',
    'fr': 'French',
    'rw': 'Kinyarwanda',
    'unknown': 'Unknown'
}


def detect_language(page_data):
    """
    Detect all languages present in a page by analyzing text chunks.
    
    Args:
        page_data (dict): Page data with 'words' key containing word dictionaries
    
    Returns:
        list: List of detected language codes (e.g., ['en', 'fr', 'rw'])
    """
    if not page_data or 'words' not in page_data:
        return ['unknown']
    
    words = page_data['words']
    if not words:
        return ['unknown']
    
    # Extract all text
    all_text = ' '.join(word['text'] for word in words if 'text' in word)
    
    if len(all_text.strip()) < 10:
        return ['unknown']
    
    # Count language detections per chunk
    language_count = Counter()
    
    # Split into chunks of ~40 words
    word_list = all_text.split()
    chunk_size = 40
    
    if len(word_list) < chunk_size:
        # If page is small, analyze as single chunk
        try:
            lang, confidence = langid.classify(all_text)
            return [lang]
        except Exception:
            return ['unknown']
    
    # Analyze chunks
    for i in range(0, len(word_list), chunk_size):
        chunk = ' '.join(word_list[i:i + chunk_size])
        
        if len(chunk.strip()) < 10:
            continue
        
        try:
            lang, confidence = langid.classify(chunk)
            language_count[lang] += 1
        except Exception:
            continue
    
    # Get languages that appear in at least 15% of chunks
    total_chunks = len(language_count)
    if total_chunks == 0:
        return ['unknown']
    
    threshold = max(1, total_chunks * 0.15)  # At least 15% of chunks
    
    detected_languages = [
        lang for lang, count in language_count.items() 
        if count >= threshold
    ]
    
    return sorted(detected_languages) if detected_languages else ['unknown']


if __name__ == "__main__":
    import sys
    
    # Default test PDF path
    pdf_path = "data/MINISTERIAL INSTRUCTIONS No 001_07.01 OF 30_06_2025 RELATING TO THE SETTLING OF PERSONS (1).pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    print(f"Detecting languages in: {pdf_path}")
    print("=" * 80)
    
    # Parse PDF
    pages_data = parse_pdf_words(pdf_path)
    
    # Detect languages for each page
    for page_data in pages_data:
        page_num = page_data['page_num']
        languages = detect_language(page_data)
        
        # Format language names
        lang_names = [LANGUAGE_NAMES.get(lang, lang) for lang in languages]
        lang_display = ', '.join(lang_names)
        
        print(f"Page {page_num}: I detected {lang_display}")
    
    print("=" * 80)
    print("Language detection complete!")
