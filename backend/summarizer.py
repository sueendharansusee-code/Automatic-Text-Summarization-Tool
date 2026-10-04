import re
import heapq
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# Ensure required NLTK resources are available
def initialize_nltk():
    resources = ['punkt', 'stopwords', 'punkt_tab']
    for resource in resources:
        try:
            nltk.data.find(f'tokenizers/{resource}') if 'punkt' in resource else nltk.data.find(f'corpora/{resource}')
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception as e:
                print(f"Warning downloading NLTK resource {resource}: {e}")

initialize_nltk()


def clean_text(text):
    """
    Cleans and normalizes whitespace in the text while preserving punctuation.
    """
    if not text:
        return ""
    # Normalize multiple whitespace, newlines, and non-standard spaces
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned


def get_target_sentence_count(total_sentences, length_level):
    """
    Determines the number of sentences to extract based on the selected length level.
    """
    if total_sentences <= 0:
        return 0
    if total_sentences <= 2:
        return total_sentences

    level_map = {
        'short': max(1, round(total_sentences * 0.20)),
        'medium': max(2, round(total_sentences * 0.35)),
        'detailed': max(3, round(total_sentences * 0.50))
    }

    target_count = level_map.get(length_level.lower(), level_map['medium'])
    # Ensure target_count doesn't exceed total sentences and is at least 1
    return max(1, min(target_count, total_sentences))


def summarize_text(raw_text, length_level='medium'):
    """
    Extractive text summarization algorithm based on sentence frequency scoring.
    
    Steps:
    1. Clean input text.
    2. Split into sentences using NLTK sentence tokenizer.
    3. Tokenize words, remove stopwords & non-alphanumeric tokens.
    4. Calculate normalized word frequency weights.
    5. Score sentences based on constituent word weights.
    6. Select top N sentences according to requested summary length (short/medium/detailed).
    7. Re-order selected sentences according to their original positions in the source text.
    8. Compute word count and compression statistics.
    """
    cleaned = clean_text(raw_text)
    if not cleaned:
        return {
            'error': 'Input text is empty or contains only whitespace.',
            'summary': '',
            'original_word_count': 0,
            'summary_word_count': 0,
            'compression_rate': 0,
            'original_sentence_count': 0,
            'summary_sentence_count': 0,
            'is_short_text': False
        }

    # Split into sentences
    try:
        sentences = sent_tokenize(cleaned)
    except Exception:
        # Fallback regex sentence tokenizer if NLTK tokenizer encounters an issue
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', cleaned) if s.strip()]

    if not sentences:
        sentences = [cleaned]

    original_word_count = len(cleaned.split())
    original_sentence_count = len(sentences)

    # Edge Case Handling (#14): Very short text (< 3 sentences or < 30 words)
    if original_sentence_count < 3 or original_word_count < 30:
        summary_text = cleaned
        summary_word_count = original_word_count
        return {
            'summary': summary_text,
            'original_word_count': original_word_count,
            'summary_word_count': summary_word_count,
            'compression_rate': 0.0,
            'original_sentence_count': original_sentence_count,
            'summary_sentence_count': original_sentence_count,
            'is_short_text': True,
            'message': 'Input text is very short; displaying complete text as summary.'
        }

    # Stopwords setup
    try:
        stop_words = set(stopwords.words('english'))
    except Exception:
        stop_words = set([
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
            "he", "him", "his", "himself", "she", "her", "hers", "it", "its", "they", "them", 
            "their", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", 
            "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", 
            "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", 
            "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", 
            "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", 
            "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once"
        ])

    # Calculate Word Frequency
    word_frequencies = {}
    for sentence in sentences:
        try:
            words = word_tokenize(sentence.lower())
        except Exception:
            words = re.findall(r'\b\w+\b', sentence.lower())

        for word in words:
            # Keep alphanumeric words not in stop_words
            if word.isalnum() and word not in stop_words:
                word_frequencies[word] = word_frequencies.get(word, 0) + 1

    # Check if we have any valid words for frequency calculation
    if not word_frequencies:
        # Fallback if text contains only stopwords or unusual characters
        target_count = get_target_sentence_count(original_sentence_count, length_level)
        selected_sentences = sentences[:target_count]
        summary_text = " ".join(selected_sentences)
        summary_word_count = len(summary_text.split())
        compression_rate = round((1 - (summary_word_count / original_word_count)) * 100, 2)
        return {
            'summary': summary_text,
            'original_word_count': original_word_count,
            'summary_word_count': summary_word_count,
            'compression_rate': max(0.0, compression_rate),
            'original_sentence_count': original_sentence_count,
            'summary_sentence_count': len(selected_sentences),
            'is_short_text': False
        }

    # Normalize word frequencies by maximum frequency
    max_frequency = max(word_frequencies.values())
    for word in word_frequencies:
        word_frequencies[word] = word_frequencies[word] / max_frequency

    # Score sentences based on normalized word frequencies
    sentence_scores = {}
    for idx, sentence in enumerate(sentences):
        try:
            words = word_tokenize(sentence.lower())
        except Exception:
            words = re.findall(r'\b\w+\b', sentence.lower())

        score = 0
        word_count_in_sentence = 0
        for word in words:
            if word in word_frequencies:
                score += word_frequencies[word]
                word_count_in_sentence += 1

        # Length normalization to avoid bias towards excessively long sentences
        if word_count_in_sentence > 0:
            sentence_scores[idx] = score / (word_count_in_sentence ** 0.5)
        else:
            sentence_scores[idx] = 0

    # Determine number of sentences for output summary
    target_count = get_target_sentence_count(original_sentence_count, length_level)

    # Select top scored sentence indices
    top_sentence_indices = heapq.nlargest(target_count, sentence_scores, key=sentence_scores.get)
    # Sort indices to maintain original narrative order
    top_sentence_indices.sort()

    selected_sentences = [sentences[i] for i in top_sentence_indices]
    summary_text = " ".join(selected_sentences)

    summary_word_count = len(summary_text.split())
    compression_rate = round((1 - (summary_word_count / original_word_count)) * 100, 2) if original_word_count > 0 else 0.0
    compression_rate = max(0.0, min(100.0, compression_rate))

    return {
        'summary': summary_text,
        'original_word_count': original_word_count,
        'summary_word_count': summary_word_count,
        'compression_rate': compression_rate,
        'original_sentence_count': original_sentence_count,
        'summary_sentence_count': len(selected_sentences),
        'is_short_text': False
    }
