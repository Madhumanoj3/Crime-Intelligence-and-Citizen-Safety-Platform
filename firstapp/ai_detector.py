"""
AI Duplicate Detection Engine using TF-IDF and Cosine Similarity.
Calculates text similarity between new and existing complaints.
"""

import re
import math
from collections import Counter

# Standard English stopwords
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and',
    'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below',
    'between', 'both', 'but', 'by', 'can', 'did', 'do', 'does', 'doing', 'down',
    'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have',
    'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his',
    'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me',
    'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off', 'on',
    'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
    'same', 'she', 'should', 'so', 'some', 'such', 'than', 'that', 'the', 'their',
    'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this',
    'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we',
    'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with',
    'you', 'your', 'yours', 'yourself', 'yourselves'
}


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words without stopwords."""
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())
    return [w for w in words if w not in STOPWORDS]


def _compute_tf(tokens: list[str]) -> dict[str, float]:
    """Compute term frequency (TF) for a single document."""
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    return {word: count / total for word, count in counts.items()}


def _compute_cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse TF-IDF vectors."""
    common_words = set(vec1.keys()).intersection(vec2.keys())
    if not common_words:
        return 0.0

    dot_product = sum(vec1[w] * vec2[w] for w in common_words)
    norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot_product / (norm1 * norm2)


def check_duplicate_complaint(new_title: str, new_desc: str, new_category: str,
                              existing_complaints: list, threshold: float = 0.50):
    """
    Compares a new complaint against a list of existing complaint objects/dicts.

    Returns:
        dict: {
            'is_duplicate': bool,
            'similarity_score': float (0.0 to 1.0),
            'similarity_pct': float (0.0 to 100.0),
            'matched_complaint_id': str or None,
            'matched_title': str or None,
            'reason': str
        }
    """
    new_combined = f"{new_category} {new_title} {new_desc}".strip()
    new_tokens = _tokenize(new_combined)
    if not new_tokens or not existing_complaints:
        return {
            'is_duplicate': False,
            'similarity_score': 0.0,
            'similarity_pct': 0.0,
            'matched_complaint_id': None,
            'matched_title': None,
            'reason': "Unique complaint"
        }

    # Build corpus
    corpus_docs = [new_tokens]
    complaint_records = []

    for c in existing_complaints:
        c_id = getattr(c, 'complaint_id', None) or (c.get('complaint_id') if isinstance(c, dict) else None)
        c_title = getattr(c, 'title', None) or (c.get('title', '') if isinstance(c, dict) else '')
        c_desc = getattr(c, 'description', None) or (c.get('description', '') if isinstance(c, dict) else '')
        c_cat = getattr(c, 'category', None) or (c.get('category', '') if isinstance(c, dict) else '')

        text = f"{c_cat} {c_title} {c_desc}".strip()
        tokens = _tokenize(text)
        corpus_docs.append(tokens)
        complaint_records.append({
            'id': c_id,
            'title': c_title,
            'tokens': tokens
        })

    # Compute IDF across all documents
    total_docs = len(corpus_docs)
    df_counts = Counter()
    for doc in corpus_docs:
        df_counts.update(set(doc))

    idf = {word: math.log((1 + total_docs) / (1 + count)) + 1.0 for word, count in df_counts.items()}

    # Compute TF-IDF for new complaint
    new_tf = _compute_tf(new_tokens)
    new_tfidf = {w: tf_val * idf.get(w, 1.0) for w, tf_val in new_tf.items()}

    best_score = 0.0
    best_match = None

    for rec in complaint_records:
        rec_tf = _compute_tf(rec['tokens'])
        rec_tfidf = {w: tf_val * idf.get(w, 1.0) for w, tf_val in rec_tf.items()}

        sim = _compute_cosine_similarity(new_tfidf, rec_tfidf)
        if sim > best_score:
            best_score = sim
            best_match = rec

    if best_match and best_score >= threshold:
        pct = round(best_score * 100, 1)
        return {
            'is_duplicate': True,
            'similarity_score': round(best_score, 3),
            'similarity_pct': pct,
            'matched_complaint_id': best_match['id'],
            'matched_title': best_match['title'],
            'reason': f"High similarity ({pct}%) with complaint {best_match['id']}: '{best_match['title']}'"
        }

    return {
        'is_duplicate': False,
        'similarity_score': round(best_score, 3),
        'similarity_pct': round(best_score * 100, 1),
        'matched_complaint_id': best_match['id'] if best_match else None,
        'matched_title': best_match['title'] if best_match else None,
        'reason': "Unique complaint"
    }
