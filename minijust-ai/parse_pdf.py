"""
Parse PDF → words with coordinates per page.
"""
import fitz  # PyMuPDF


def parse_pdf_words(pdf_path):
   
    doc = fitz.open(pdf_path)
    pages_data = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        words = page.get_text("words")
        
        page_data = {
            'page_num': page_num,
            'width': page.rect.width,
            'height': page.rect.height,
            'words': [
                {
                    'text': w[4],
                    'x0': w[0],
                    'y0': w[1],
                    'x1': w[2],
                    'y1': w[3],
                    'bbox': (w[0], w[1], w[2], w[3])
                }
                for w in words
            ]
        }
        pages_data.append(page_data)
    
    doc.close()
    return pages_data