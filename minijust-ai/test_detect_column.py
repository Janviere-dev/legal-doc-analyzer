"""
Test script for column detection - can be run independently
"""
import os
import sys



def test_all_pdfs_in_data():
    """
    Test all PDF files in the data directory.
    """
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    if not os.path.exists(data_dir):
        print(f"Data directory not found: {data_dir}")
        return
    
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in data directory")
        return
    
    print(f"\nFound {len(pdf_files)} PDF file(s):")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    
    # Let user choose a file
    print("\nEnter the number of the file you want to test (or press Enter for file #1): ")
    try:
        user_input = input().strip()
        if user_input:
            choice = int(user_input)
            if choice < 1 or choice > len(pdf_files):
                print(f"Invalid choice. Using file #1")
                choice = 1
        else:
            choice = 1
    except ValueError:
        print("Invalid input. Using file #1")
        choice = 1
    
    # Get the chosen file
    chosen_file = pdf_files[choice - 1]
    chosen_path = os.path.join(data_dir, chosen_file)
    
    print(f"\n{'='*80}")
    print(f"You selected: {chosen_file}")
    print(f"{'='*80}\n")
    
    # Parse the PDF and get word coordinates
    from parse_pdf import parse_pdf_words
    
    print("Parsing PDF and extracting word coordinates...")
    pages_data = parse_pdf_words(chosen_path)
    
    print(f"\n✓ Successfully parsed {len(pages_data)} page(s)\n")
    
    # Display word coordinates for first page (or first few words)
    for page_idx, page_data in enumerate(pages_data[:2]):  # Show first 2 pages
        print(f"Page {page_data['page_num'] + 1}:")
        print(f"  Dimensions: {page_data['width']:.2f} x {page_data['height']:.2f}")
        print(f"  Total words: {len(page_data['words'])}")
        
        # Show first 10 words with coordinates
        print(f"\n  First 10 words with coordinates:")
        print(f"  {'Word':<20} {'X0':<8} {'Y0':<8} {'X1':<8} {'Y1':<8}")
        print(f"  {'-'*60}")
        
        for word in page_data['words'][:10]:
            text = word['text'][:18]  # Truncate long words
            x0 = word['x0']
            y0 = word['y0']
            x1 = word['x1']
            y1 = word['y1']
            print(f"  {text:<20} {x0:<8.2f} {y0:<8.2f} {x1:<8.2f} {y1:<8.2f}")
        
        print()
    
    return pages_data


def test_column_detection_simple(pdf_path):
    """
    Simple test that doesn't require polyglot - just tests the basic structure.
    """
    from parse_pdf import parse_pdf_words
    
    print(f"\n{'='*80}")
    print(f"Testing Column Detection (Simple Version)")
    print(f"File: {pdf_path}")
    print(f"{'='*80}\n")
    
    try:
        # Step 1: Parse PDF
        print("Step 1: Parsing PDF...")
        pages_data = parse_pdf_words(pdf_path)
        print(f"✓ Parsed {len(pages_data)} page(s)\n")
        
        # Step 2: Analyze each page
        for page_data in pages_data[:3]:  # Show first 3 pages
            page_num = page_data['page_num']
            width = page_data['width']
            height = page_data['height']
            words = page_data['words']
            
            print(f"Page {page_num + 1}:")
            print(f"  Dimensions: {width:.2f} x {height:.2f}")
            print(f"  Total Words: {len(words)}")
            
            if words:
                # Analyze x-position distribution
                x_positions = [(w['x0'] + w['x1']) / 2 for w in words]
                x_positions.sort()
                
                # Simple column detection: divide into thirds
                third_1 = width / 3
                third_2 = 2 * width / 3
                
                # Count words in each third
                col1_words = sum(1 for x in x_positions if x < third_1)
                col2_words = sum(1 for x in x_positions if third_1 <= x < third_2)
                col3_words = sum(1 for x in x_positions if x >= third_2)
                
                print(f"  Word Distribution (simple thirds):")
                print(f"    Column 1 (0 → {third_1:.1f}): {col1_words} words")
                print(f"    Column 2 ({third_1:.1f} → {third_2:.1f}): {col2_words} words")
                print(f"    Column 3 ({third_2:.1f} → {width:.1f}): {col3_words} words")
                
                # Show first few words from each column
                print(f"\n  Sample words from each section:")
                col1_samples = [w['text'] for w in words if (w['x0'] + w['x1'])/2 < third_1][:5]
                col2_samples = [w['text'] for w in words if third_1 <= (w['x0'] + w['x1'])/2 < third_2][:5]
                col3_samples = [w['text'] for w in words if (w['x0'] + w['x1'])/2 >= third_2][:5]
                
                if col1_samples:
                    print(f"    Column 1: {' '.join(col1_samples)}")
                if col2_samples:
                    print(f"    Column 2: {' '.join(col2_samples)}")
                if col3_samples:
                    print(f"    Column 3: {' '.join(col3_samples)}")
            
            print()
        
        if len(pages_data) > 3:
            print(f"... and {len(pages_data) - 3} more page(s)\n")
        
        print("✓ Test completed successfully!\n")
        return pages_data
        
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=" * 80)
    print("COLUMN DETECTION TEST SUITE")
    print("=" * 80)
    
    # Check if a specific file was provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if os.path.exists(pdf_path):
            print(f"\nTesting file: {pdf_path}")
            test_column_detection_simple(pdf_path)
        else:
            print(f"\nFile not found: {pdf_path}")
    else:
        # Test all PDFs in data directory with file selection
        test_all_pdfs_in_data()

