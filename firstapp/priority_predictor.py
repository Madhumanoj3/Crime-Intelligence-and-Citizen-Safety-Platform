"""
AI Complaint Priority Prediction (decision support only).

A supervised model (TF-IDF text features + Logistic Regression) trained by
ml/train_priority_model.py predicts Low / Medium / High priority for a new
complaint. The prediction is a recommendation for the Station In-Charge
Inspector; it never assigns officers or approves/rejects a complaint.

This module has no Django imports, so the training script can reuse the same
feature preparation (prepare_record / build_features) as the live app.
"""
import os
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'ml', 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'priority_model.joblib')
VECTORIZER_PATH = os.path.join(MODELS_DIR, 'tfidf_vectorizer.joblib')

PRIORITY_LABELS = ['Low', 'Medium', 'High']

# Categories offered on the citizen complaint form (after .title()).
CATEGORIES = ['Theft', 'Cybercrime', 'Fraud', 'Harassment', 'Accident', 'Assault', 'Vandalism', 'Other']
# Location.location_type values in the database, plus a fallback.
LOCATION_TYPES = ['Area', 'Village', 'Town', 'Landmark', 'City Center', 'Unknown']
TIME_BUCKETS = ['Night', 'Morning', 'Afternoon', 'Evening']
MAX_PREVIOUS_REPORTS = 5  # counts above this are capped


def time_bucket(time_str):
    """Map 'HH:MM' to Night (22-05), Morning (06-11), Afternoon (12-16) or Evening (17-21)."""
    try:
        hour = int(str(time_str).strip().split(':')[0])
    except (ValueError, IndexError):
        return 'Afternoon'
    if hour >= 22 or hour < 6:
        return 'Night'
    if hour < 12:
        return 'Morning'
    if hour < 17:
        return 'Afternoon'
    return 'Evening'


def prepare_record(title, description, category, location_type, incident_time, previous_reports):
    """Normalise raw complaint information into the model's input fields."""
    category = (category or 'Other').strip().title()
    if category not in CATEGORIES:
        category = 'Other'
    location_type = (location_type or 'Unknown').strip()
    if location_type not in LOCATION_TYPES:
        location_type = 'Unknown'
    try:
        previous_reports = max(0, int(previous_reports or 0))
    except (TypeError, ValueError):
        previous_reports = 0
    return {
        'text': f"{title or ''}. {description or ''}".strip(),
        'category': category,
        'location_type': location_type,
        'time_bucket': time_bucket(incident_time),
        'previous_reports': previous_reports,
    }


def build_features(records, vectorizer, encoder):
    """Stack TF-IDF text features, one-hot structured features and scaled report count."""
    import numpy as np
    from scipy.sparse import csr_matrix, hstack

    text = vectorizer.transform([r['text'] for r in records])
    cats = encoder.transform([[r['category'], r['location_type'], r['time_bucket']] for r in records])
    prev = np.array([[min(r['previous_reports'], MAX_PREVIOUS_REPORTS) / MAX_PREVIOUS_REPORTS]
                     for r in records])
    return hstack([text, cats, csr_matrix(prev)]).tocsr()


_cache = {}
_lock = threading.Lock()


def _load():
    """Load (and cache) the model bundle and vectorizer; reload if the files change."""
    import joblib

    stamp = (os.path.getmtime(MODEL_PATH), os.path.getmtime(VECTORIZER_PATH))
    with _lock:
        if _cache.get('stamp') != stamp:
            _cache['bundle'] = joblib.load(MODEL_PATH)
            _cache['vectorizer'] = joblib.load(VECTORIZER_PATH)
            _cache['stamp'] = stamp
        return _cache['bundle'], _cache['vectorizer']


def predict_priority(title, description, category, location_type='Unknown',
                     incident_time='', previous_reports=0):
    """
    Predict complaint priority. Never raises: if the model is missing or fails,
    returns priority '' so the complaint is still saved normally.

    Returns: {'priority': 'Low'|'Medium'|'High'|'', 'confidence': float 0-100,
              'probabilities': {label: pct}, 'error': str}
    """
    try:
        bundle, vectorizer = _load()
        record = prepare_record(title, description, category, location_type,
                                incident_time, previous_reports)
        X = build_features([record], vectorizer, bundle['encoder'])
        clf = bundle['classifier']
        probs = clf.predict_proba(X)[0]
        best = int(probs.argmax())
        return {
            'priority': str(clf.classes_[best]),
            'confidence': round(float(probs[best]) * 100, 1),
            'probabilities': {str(c): round(float(p) * 100, 1) for c, p in zip(clf.classes_, probs)},
            'error': '',
        }
    except Exception as exc:  # model not trained yet, sklearn missing, corrupt file...
        return {'priority': '', 'confidence': 0.0, 'probabilities': {}, 'error': str(exc)}


def apply_ai_priority(complaint):
    """
    Predict and store the AI priority for a saved Complaint.
    Location type comes from the Location table (by area name). Previous related
    reports are complaints filed earlier with the same category in the same area.
    Only the ai_priority fields are written; nothing else about the complaint changes.
    """
    from .models import Complaint, Location  # local import keeps this module Django-free

    location_type = 'Unknown'
    previous_reports = 0
    if complaint.area:
        loc = Location.objects.filter(name__iexact=complaint.area).first()
        if loc and loc.location_type:
            location_type = loc.location_type
        previous_reports = (Complaint.objects
                            .filter(area__iexact=complaint.area, category__iexact=complaint.category,
                                    pk__lt=complaint.pk).count())

    result = predict_priority(complaint.title, complaint.description, complaint.category,
                              location_type, complaint.incident_time, previous_reports)
    if result['priority']:
        complaint.ai_priority = result['priority']
        complaint.ai_priority_confidence = f"{result['confidence']}%"
        Complaint.objects.filter(pk=complaint.pk).update(
            ai_priority=complaint.ai_priority,
            ai_priority_confidence=complaint.ai_priority_confidence)
    result.update(location_type=location_type, previous_reports=previous_reports)
    return result
