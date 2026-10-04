import os
import sys

# Ensure backend root path is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.summarizer import summarize_text, clean_text
from backend.database import (
    init_db, save_summary, get_all_summaries,
    get_summary_by_id, delete_summary, clear_all_summaries
)

def test_nlp_summarizer():
    print("--- Running NLP Summarizer Verification Tests ---")

    # Test Case 1: Standard Article Text
    sample_text = (
        "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to intelligence displayed by animals including humans. "
        "AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals. "
        "The term artificial intelligence had previously been used to describe machines that mimic and display human cognitive skills that associated with the human mind, such as learning and problem solving. "
        "As machines become increasingly capable, tasks considered to require intelligence are often removed from the definition of AI, a phenomenon known as the AI effect. "
        "For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology. "
        "Modern AI capabilities include autonomous vehicles, medical diagnosis, creating art, proving mathematical theorems, playing games, search engines, and targeted online advertising."
    )

    for length in ['short', 'medium', 'detailed']:
        res = summarize_text(sample_text, length_level=length)
        print(f"\n[Length Level: {length.upper()}]")
        print(f"Original Words: {res['original_word_count']} | Summary Words: {res['summary_word_count']}")
        print(f"Compression Rate: {res['compression_rate']}%")
        print(f"Sentences Ratio: {res['original_sentence_count']} -> {res['summary_sentence_count']}")
        print(f"Summary Output:\n{res['summary']}\n")
        assert res['summary_word_count'] > 0
        assert res['summary_sentence_count'] <= res['original_sentence_count']

    # Test Case 2: Short Text Edge Case (#14)
    short_text = "This is a single short sentence."
    res_short = summarize_text(short_text, length_level='medium')
    print("[Short Text Edge Case]")
    print(f"is_short_text: {res_short['is_short_text']}")
    print(f"Summary: {res_short['summary']}")
    assert res_short['is_short_text'] == True
    assert res_short['summary'] == short_text

    # Test Case 3: Empty Text Handling
    res_empty = summarize_text("", length_level='medium')
    assert 'error' in res_empty
    print("[Empty Text Test Passed]")

    print("\n--- All Summarizer Verification Tests Passed! ---\n")


def test_database():
    print("--- Running SQLite Database Verification Tests ---")
    test_db = os.path.join(BASE_DIR, 'data', 'test_summaries.db')
    if os.path.exists(test_db):
        os.remove(test_db)

    # Test saving record
    id1 = save_summary("Orig text 1", "Sum text 1", "medium", 100, 40, 60.0, db_path=test_db)
    id2 = save_summary("Orig text 2", "Sum text 2", "short", 200, 50, 75.0, db_path=test_db)

    all_recs = get_all_summaries(db_path=test_db)
    print(f"Saved records count: {len(all_recs)}")
    assert len(all_recs) == 2

    item = get_summary_by_id(id1, db_path=test_db)
    assert item['original_text'] == "Orig text 1"
    print(f"Fetched Item #{id1}: {item['summary_text']}")

    del_ok = delete_summary(id1, db_path=test_db)
    assert del_ok == True
    assert len(get_all_summaries(db_path=test_db)) == 1

    cleared = clear_all_summaries(db_path=test_db)
    assert cleared == 1
    assert len(get_all_summaries(db_path=test_db)) == 0

    if os.path.exists(test_db):
        os.remove(test_db)

    print("\n--- All Database Verification Tests Passed! ---\n")


if __name__ == '__main__':
    test_nlp_summarizer()
    test_database()
