import os
import sys
from flask import Flask, render_template, request, jsonify

# Add backend directory to sys.path if needed
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.summarizer import summarize_text
from backend.database import (
    init_db,
    save_summary,
    get_all_summaries,
    get_summary_by_id,
    delete_summary,
    clear_all_summaries
)

template_dir = os.path.join(BASE_DIR, 'templates')
static_dir = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Initialize SQLite Database on startup
init_db()


@app.route('/')
def index():
    """Renders the main dashboard page."""
    return render_template('index.html')


@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    """
    API endpoint to process input text and generate extractive summary.
    Saves successful non-empty summaries to SQLite database history.
    """
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    length_level = data.get('length', 'medium')

    if not text:
        return jsonify({
            'success': False,
            'error': 'Please provide text to summarize.'
        }), 400

    result = summarize_text(text, length_level=length_level)

    if 'error' in result:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 400

    # Save to database if summary was produced
    history_id = None
    if result['summary']:
        try:
            history_id = save_summary(
                original_text=text,
                summary_text=result['summary'],
                length_setting=length_level,
                original_word_count=result['original_word_count'],
                summary_word_count=result['summary_word_count'],
                compression_rate=result['compression_rate']
            )
        except Exception as db_err:
            print(f"Error saving to database: {db_err}")

    return jsonify({
        'success': True,
        'history_id': history_id,
        'summary': result['summary'],
        'original_word_count': result['original_word_count'],
        'summary_word_count': result['summary_word_count'],
        'compression_rate': result['compression_rate'],
        'original_sentence_count': result['original_sentence_count'],
        'summary_sentence_count': result['summary_sentence_count'],
        'is_short_text': result.get('is_short_text', False),
        'message': result.get('message', '')
    })


@app.route('/api/history', methods=['GET'])
def api_get_history():
    """Endpoint to retrieve summary history."""
    try:
        history = get_all_summaries()
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history/<int:summary_id>', methods=['GET'])
def api_get_history_item(summary_id):
    """Endpoint to fetch details of a specific history item."""
    item = get_summary_by_id(summary_id)
    if not item:
        return jsonify({'success': False, 'error': 'Summary not found'}), 404
    return jsonify({'success': True, 'item': item})


@app.route('/api/history/<int:summary_id>', methods=['DELETE'])
def api_delete_history_item(summary_id):
    """Endpoint to delete a specific history item."""
    success = delete_summary(summary_id)
    if success:
        return jsonify({'success': True, 'message': 'Summary deleted successfully'})
    return jsonify({'success': False, 'error': 'Item not found'}), 404


@app.route('/api/history', methods=['DELETE'])
def api_clear_history():
    """Endpoint to clear all history records."""
    count = clear_all_summaries()
    return jsonify({'success': True, 'message': f'Cleared {count} records.'})


@app.route('/api/sample', methods=['GET'])
def api_sample_text():
    """Returns sample academic/article text for quick testing and demonstration."""
    sample_text = (
        "Natural Language Processing (NLP) is a interdisciplinary subfield of computer science, "
        "artificial intelligence, and linguistics. It is primarily concerned with giving computers "
        "the ability to process and analyze large amounts of natural language data. The ultimate "
        "objective of NLP is to read, decipher, understand, and make sense of the human languages "
        "in a manner that is valuable. Most NLP techniques rely on machine learning to derive "
        "meaning from human languages.\n\n"
        "Text summarization is one of the most vital and challenging applications in NLP. "
        "It involves condensing a long text document into a succinct summary that preserves key "
        "information and overall meaning. There are two general approaches to automatic text "
        "summarization: extractive summarization and abstractive summarization. Extractive summarization "
        "works by identifying and extracting important sentences, clauses, or passages from the source document "
        "without altering the original wording. In contrast, abstractive summarization aims to build an internal "
        "semantic representation and generate new sentences that paraphrase the core concepts of the original text.\n\n"
        "Extractive summarization techniques rely heavily on Statistical and Heuristic methods. Frequency-based "
        "algorithms compute word significance based on Term Frequency (TF) after removing non-informative words "
        "known as stopwords. Sentences containing a high density of high-frequency words receive higher relevance scores. "
        "By ordering sentences by their calculated weights and selecting the top percentile, the system yields a concise, "
        "highly representative summary. This approach is computationally efficient, deterministic, and effective for "
        "academic papers, news articles, and legal documents."
    )
    return jsonify({'success': True, 'sample_text': sample_text})


if __name__ == '__main__':
    print("Starting Automatic Text Summarization Tool Flask App...")
    print("Open your web browser at: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
