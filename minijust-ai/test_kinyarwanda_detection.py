"""
Test Kinyarwanda article detection patterns
"""

import re
from create_chunks import DocumentChunker

def test_kinyarwanda_patterns():
    """Test various Kinyarwanda article patterns"""
    
    # Create a dummy chunker instance just to access the method
    chunker = DocumentChunker("dummy.pdf")
    
    # Test cases with different Kinyarwanda article formats
    test_texts = [
        {
            'name': 'Ingingo ya mbere',
            'text': 'Ingingo ya mbere: Icyo aya mabwiriza agamije',
            'expected_articles': 1,
            'expected_number': '1'
        },
        {
            'name': 'Ingingo ya [number]',
            'text': '''
            Ingingo ya 5: Uburyo bwo gutuza
            Ingingo ya 12: Inshingano z'umuntu
            Ingingo ya 25: Ibigenderwaho
            ''',
            'expected_articles': 3,
            'expected_numbers': ['5', '12', '25']
        },
        {
            'name': 'Ingingo with Kinyarwanda number words',
            'text': '''
            Ingingo ya mbere: First article
            Ingingo ya kabiri: Second article
            Ingingo ya gatatu: Third article
            Ingingo ya kane: Fourth article
            Ingingo ya gatanu: Fifth article
            ''',
            'expected_articles': 5,
            'expected_numbers': ['1', '2', '3', '4', '5']
        },
        {
            'name': 'Mixed case Ingingo',
            'text': '''
            INGINGO YA 10: UPPERCASE
            Ingingo ya 11: Normal case
            ingingo ya 12: lowercase
            ''',
            'expected_articles': 3,
            'expected_numbers': ['10', '11', '12']
        },
        {
            'name': 'Complex document sample',
            'text': '''
            AMABWIRIZA YA MINISITIRI No 001/07.01
            
            UMUTWE WA MBERE: INGINGO RUSANGE
            
            Ingingo ya mbere: Icyo aya mabwiriza agamije
            Aya mabwiriza agena uburyo bwo gutuza abantu.
            
            Ingingo ya 2: Isobanura ry'amagambo
            Muri aya mabwiriza, amagambo akurikira afite ibisobanuro bikurikira:
            
            Ingingo ya gatatu: Abarebwa n'aya mabwiriza
            Aya mabwiriza arebana n'abantu bose.
            
            UMUTWE WA KABIRI: IBIKORESHO
            
            Ingingo ya 4: Ibigenderwaho mu gutoranya
            Abantu batuzwa batoranywa.
            ''',
            'expected_articles': 4,
            'expected_numbers': ['1', '2', '3', '4']
        }
    ]
    
    print("=" * 80)
    print("TESTING KINYARWANDA ARTICLE DETECTION")
    print("=" * 80)
    print()
    
    total_tests = len(test_texts)
    passed_tests = 0
    
    for i, test_case in enumerate(test_texts, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 60)
        
        # Detect articles
        articles = chunker._detect_articles(test_case['text'])
        
        # Check number of articles
        detected_count = len(articles)
        expected_count = test_case['expected_articles']
        
        print(f"  Expected articles: {expected_count}")
        print(f"  Detected articles: {detected_count}")
        
        # Display detected articles
        if articles:
            print(f"  Detected:")
            for article in articles:
                print(f"    - Article {article['number']}: '{article['matched_text']}' (pos: {article['start_pos']}, lang: {article['language']})")
        
        # Verify
        test_passed = True
        if detected_count != expected_count:
            print(f"  ❌ FAILED: Expected {expected_count} articles, got {detected_count}")
            test_passed = False
        elif 'expected_numbers' in test_case:
            detected_numbers = [a['number'] for a in articles]
            if detected_numbers != test_case['expected_numbers']:
                print(f"  ❌ FAILED: Expected numbers {test_case['expected_numbers']}, got {detected_numbers}")
                test_passed = False
            else:
                print(f"  ✅ PASSED")
                passed_tests += 1
        elif 'expected_number' in test_case and articles:
            if articles[0]['number'] != test_case['expected_number']:
                print(f"  ❌ FAILED: Expected number {test_case['expected_number']}, got {articles[0]['number']}")
                test_passed = False
            else:
                print(f"  ✅ PASSED")
                passed_tests += 1
        else:
            print(f"  ✅ PASSED")
            passed_tests += 1
        
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 80)
    
    return passed_tests == total_tests


if __name__ == '__main__':
    success = test_kinyarwanda_patterns()
    exit(0 if success else 1)
