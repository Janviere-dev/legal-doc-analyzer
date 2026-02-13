from parse_pdf import parse_pdf_words


def detect_column_boundaries(page_data, num_columns=3):
    
    words = page_data['words']
    page_width = page_data['width']
    
    if not words:
        # Fallback to equal division
        if num_columns == 3:
            return (page_width / 3, 2 * page_width / 3)
        return None
    
    # Step 1: Get center x-coordinate of each word
    word_centers = [(w['x0'] + w['x1']) / 2 for w in words]
    word_centers.sort()
    
    # Step 2: Find gaps between consecutive word positions
    gaps = []
    for i in range(len(word_centers) - 1):
        gap_size = word_centers[i + 1] - word_centers[i]
        gap_center = (word_centers[i] + word_centers[i + 1]) / 2
        gaps.append({
            'size': gap_size,
            'center': gap_center,
            'left': word_centers[i],
            'right': word_centers[i + 1]
        })
    
    # Step 3: Sort gaps by size (largest first)
    gaps.sort(key=lambda g: g['size'], reverse=True)
    
    # For 3 columns, we need 2 boundaries
    if num_columns == 3:
        # Filter gaps that are in the middle portion of the page
        # (not too close to edges - between 20% and 80% of page width)
        middle_gaps = [g for g in gaps if 0.2 * page_width < g['center'] < 0.8 * page_width]
        
        if len(middle_gaps) >= 2:
            # Take the 2 largest gaps in the middle section
            # Sort them left to right so boundary_1 < boundary_2
            selected_gaps = sorted(middle_gaps[:2], key=lambda g: g['center'])
            boundary_1 = selected_gaps[0]['center']
            boundary_2 = selected_gaps[1]['center']
        else:
            # Fallback to equal division if gaps aren't clear
            boundary_1 = page_width / 3
            boundary_2 = 2 * page_width / 3
        
        return (boundary_1, boundary_2)
    
    return None


def detect_columns(page_data):
    
    if not page_data['words']:
        return []
    
    page_width = page_data['width']
    page_height = page_data['height']
    words = page_data['words']
    
    # Detect column boundaries using gap analysis
    boundaries = detect_column_boundaries(page_data, num_columns=3)
    
    if not boundaries:
        # Fallback
        boundaries = (page_width / 3, 2 * page_width / 3)
    
    boundary_1, boundary_2 = boundaries
    
    # Define 3 columns with language assignments
    # Typically for Rwandan official documents: Kinyarwanda | English | French
    column_defs = [
        (0, boundary_1, 'rw', 'Kinyarwanda'),
        (boundary_1, boundary_2, 'en', 'English'),
        (boundary_2, page_width, 'fr', 'French')
    ]
    
    columns = []
    for i, (x0, x1, lang_code, lang_name) in enumerate(column_defs):
        # Find all words in this column
        words_in_column = []
        for word in words:
            word_center = (word['x0'] + word['x1']) / 2
            if x0 <= word_center < x1:
                words_in_column.append(word)
        
        # Get sample text (first 10 words)
        sample_text = ' '.join(w['text'] for w in words_in_column[:10])
        
        columns.append({
            'column_num': i,
            'x0': x0,
            'x1': x1,
            'width': x1 - x0,
            'bbox': (x0, 0, x1, page_height),
            'word_count': len(words_in_column),
            'language': lang_code,
            'language_name': lang_name,
            'sample_text': sample_text,
            'words': words_in_column  # Include actual words for further processing
        })
    
    return columns


def detect_columns_all_pages(pdf_path):
    
    # Step 1: Parse PDF to get words with coordinates for each page
    pages_data = parse_pdf_words(pdf_path)
    result = []
    
    for page_data in pages_data:
        columns = detect_columns(page_data)
        
        result.append({
            'page_num': page_data['page_num'],
            'width': page_data['width'],
            'height': page_data['height'],
            'num_columns': len(columns),
            'columns': columns
        })
    
    return result


def group_words_by_line(words, line_height_threshold=5):
    
    if not words:
        return []
    
    # Sort by vertical position (y0) - from top to bottom
    sorted_words = sorted(words, key=lambda w: w['y0'])
    
    lines = []
    current_line = [sorted_words[0]]
    
    for word in sorted_words[1:]:
        # Calculate average y-position of current line for more robust comparison
        avg_y = sum(w['y0'] for w in current_line) / len(current_line)
        
        if abs(word['y0'] - avg_y) <= line_height_threshold:
            # Same line - word is close enough to the average position
            current_line.append(word)
        else:
            # New line detected - finalize current line and start new one
            # Sort words left to right (by x0) for proper reading order
            lines.append(sorted(current_line, key=lambda w: w['x0']))
            current_line = [word]
    
    # Don't forget the last line
    if current_line:
        lines.append(sorted(current_line, key=lambda w: w['x0']))
    
    return lines

def reconstruct_text_reading_order(column, line_height_threshold=5, add_line_breaks=True):
   
    if 'words' not in column or not column['words']:
        return ""
    
    words = column['words']
    
    # Group words into lines
    lines = group_words_by_line(words, line_height_threshold)
    
    # Reconstruct text line by line
    text_lines = []
    for line in lines:
        # Join words in this line with spaces
        line_text = ' '.join(word['text'] for word in line)
        text_lines.append(line_text)
        print(text_lines)
    
    # Join lines
    if add_line_breaks:
        return '\n'.join(text_lines)
    else:
        return ' '.join(text_lines)
    

if __name__ == "__main__":
    # Test the column detection and text reconstruction
    import sys
    
    # Default test PDF path - update this to your actual PDF file
    pdf_path = "data/MINISTERIAL INSTRUCTIONS No 001_07.01 OF 30_06_2025 RELATING TO THE SETTLING OF PERSONS (1).pdf"  # Change this to your PDF file path
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    print(f"Analyzing PDF: {pdf_path}")
    print("=" * 80)
    
    # Detect columns in all pages
    result = detect_columns_all_pages(pdf_path)
    
    # Display results for each page
    for page_info in result:
        page_num = page_info['page_num']
        print(f"\n{'='*80}")
        print(f"PAGE {page_num}")
        print(f"{'='*80}")
        print(f"Page dimensions: {page_info['width']:.1f} x {page_info['height']:.1f}")
        print(f"Number of columns detected: {page_info['num_columns']}")
        
        # Display info and reconstructed text for each column
        for col in page_info['columns']:
            print(f"\n{'-'*80}")
            print(f"Column {col['column_num']} ({col['language_name']} - {col['language']})")
            print(f"Position: x={col['x0']:.1f} to {col['x1']:.1f}, width={col['width']:.1f}")
            print(f"Word count: {col['word_count']}")
            
            # Reconstruct text in reading order
            reconstructed_text = reconstruct_text_reading_order(col)
            
            print(f"\nReconstructed text:")
            print("-" * 40)
            print(reconstructed_text[:500])  # Print first 500 characters
            if len(reconstructed_text) > 500:
                print(f"\n... (showing first 500 of {len(reconstructed_text)} characters)")
            print("-" * 40)
    
    print(f"\n{'='*80}")
    print("Analysis complete!")
