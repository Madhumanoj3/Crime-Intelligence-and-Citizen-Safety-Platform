"""
Train the AI Complaint Priority model (Low / Medium / High).

Features:
  * TF-IDF of complaint title + description (words)
  * one-hot crime category, location type and time of day
  * previous related reports in the same area (capped, scaled 0-1)
Model: multinomial Logistic Regression.

Steps: load dataset -> stratified 80/20 train/test split -> fit -> print metrics
-> retrain on all data -> save to ml/models/.

Usage (from the project folder):
    .venv\\Scripts\\python.exe ml\\train_priority_model.py
    .venv\\Scripts\\python.exe ml\\train_priority_model.py --dataset path\\to\\other.csv

Outputs:
    ml/models/priority_model.joblib      classifier + encoder + metadata
    ml/models/tfidf_vectorizer.joblib    fitted TF-IDF vectorizer
    ml/models/priority_model_metrics.json evaluation metrics of this run
"""
import argparse
import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import OneHotEncoder

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from firstapp.priority_predictor import (  # noqa: E402  (shared with the live app)
    CATEGORIES, LOCATION_TYPES, MODEL_PATH, MODELS_DIR, PRIORITY_LABELS, TIME_BUCKETS,
    VECTORIZER_PATH, build_features, prepare_record,
)

DEFAULT_DATASET = os.path.join(ROOT, 'ml', 'dataset', 'complaint_priority_dataset.csv')
METRICS_PATH = os.path.join(MODELS_DIR, 'priority_model_metrics.json')
TEST_SIZE = 0.2
SEED = 42


def load_dataset(path):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    records = [prepare_record(r['title'], r['complaint_description'], r['crime_category'],
                              r['location_type'], r['incident_time'], r['previous_related_reports'])
               for r in rows]
    labels = [r['priority'].strip().title() for r in rows]
    return records, labels


def fit(records, labels):
    """Fit vectorizer, encoder and classifier on the given records."""
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1), min_df=20,
                                 sublinear_tf=True)
    vectorizer.fit([r['text'] for r in records])
    encoder = OneHotEncoder(categories=[CATEGORIES, LOCATION_TYPES, TIME_BUCKETS],
                            handle_unknown='ignore')
    encoder.fit([[r['category'], r['location_type'], r['time_bucket']] for r in records])
    X = build_features(records, vectorizer, encoder)
    clf = LogisticRegression(max_iter=2000, C=5.0, class_weight='balanced', random_state=SEED)
    clf.fit(X, labels)
    return vectorizer, encoder, clf


def line(char='='):
    print(char * 64)


def main():
    parser = argparse.ArgumentParser(description='Train the complaint priority model.')
    parser.add_argument('--dataset', default=DEFAULT_DATASET)
    args = parser.parse_args()

    line()
    print(' AI COMPLAINT PRIORITY MODEL - TRAINING')
    print(' TF-IDF text features + Logistic Regression')
    line()
    records, labels = load_dataset(args.dataset)
    dist = Counter(labels)
    print(f"Dataset        : {args.dataset}")
    print(f"Records        : {len(records)}")
    print('Class balance  : ' + ', '.join(f"{p}={dist.get(p, 0)} ({dist.get(p, 0) / len(labels):.1%})"
                                          for p in PRIORITY_LABELS))

    idx_train, idx_test = train_test_split(np.arange(len(records)), test_size=TEST_SIZE,
                                           stratify=labels, random_state=SEED)
    tr_rec = [records[i] for i in idx_train]; tr_y = [labels[i] for i in idx_train]
    te_rec = [records[i] for i in idx_test]; te_y = [labels[i] for i in idx_test]
    print(f"Train / test   : {len(tr_rec)} / {len(te_rec)}  (stratified {1 - TEST_SIZE:.0%}/{TEST_SIZE:.0%} split, seed {SEED})")

    vectorizer, encoder, clf = fit(tr_rec, tr_y)
    n_text = len(vectorizer.vocabulary_)
    print(f"Features       : {n_text} TF-IDF terms + {sum(len(c) for c in encoder.categories_)} one-hot + 1 report count")

    train_pred = clf.predict(build_features(tr_rec, vectorizer, encoder))
    test_pred = clf.predict(build_features(te_rec, vectorizer, encoder))
    train_acc = accuracy_score(tr_y, train_pred)
    test_acc = accuracy_score(te_y, test_pred)
    macro_f1 = f1_score(te_y, test_pred, average='macro')
    baseline = Counter(tr_y).most_common(1)[0]
    baseline_acc = sum(y == baseline[0] for y in te_y) / len(te_y)

    line('-')
    print(' EVALUATION ON HELD-OUT TEST SET')
    line('-')
    print(f"Accuracy (train)          : {train_acc:.2%}")
    print(f"Accuracy (test)           : {test_acc:.2%}")
    print(f"Macro F1 (test)           : {macro_f1:.3f}")
    print(f"Baseline (always '{baseline[0]}') : {baseline_acc:.2%}")
    print('\nClassification report (test):')
    print(classification_report(te_y, test_pred, labels=PRIORITY_LABELS, digits=3))

    cm = confusion_matrix(te_y, test_pred, labels=PRIORITY_LABELS)
    print('Confusion matrix (rows = actual, columns = predicted):')
    print('            ' + ''.join(f"{p:>9}" for p in PRIORITY_LABELS))
    for p, row in zip(PRIORITY_LABELS, cm):
        print(f"  {p:<9} " + ''.join(f"{v:>9}" for v in row))

    # 5-fold cross-validation on the training split for a steadier estimate.
    cv_scores = []
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    for a, b in skf.split(np.zeros(len(tr_y)), tr_y):
        v, e, c = fit([tr_rec[i] for i in a], [tr_y[i] for i in a])
        cv_scores.append(accuracy_score([tr_y[i] for i in b],
                                        c.predict(build_features([tr_rec[i] for i in b], v, e))))
    print(f"\n5-fold cross-validation accuracy (train split): "
          f"{np.mean(cv_scores):.2%} +/- {np.std(cv_scores):.2%}  "
          f"[{', '.join(f'{s:.1%}' for s in cv_scores)}]")

    # Most influential words per class.
    terms = np.array(sorted(vectorizer.vocabulary_, key=vectorizer.vocabulary_.get))
    print('\nTop words pushing each priority:')
    for k, cls in enumerate(clf.classes_):
        top = np.argsort(clf.coef_[k][:n_text])[::-1][:8]
        print(f"  {cls:<7}: {', '.join(terms[top])}")

    line('-')
    print(' SAMPLE PREDICTIONS (test set)')
    line('-')
    probs = clf.predict_proba(build_features(te_rec[:6], vectorizer, encoder))
    for rec, actual, p in zip(te_rec[:6], te_y[:6], probs):
        pred = clf.classes_[p.argmax()]
        mark = 'OK ' if pred == actual else 'MISS'
        print(f"[{mark}] predicted {pred:<6} ({p.max():.0%})  actual {actual:<6} | {rec['category']}, "
              f"{rec['location_type']}, {rec['time_bucket']}, prev={rec['previous_reports']}")
        print(f"       {rec['text'][:95]}")

    # Final model: retrain on all data, then save.
    vectorizer, encoder, clf = fit(records, labels)
    metrics = {
        'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dataset': os.path.relpath(args.dataset, ROOT),
        'records': len(records),
        'train_size': len(tr_rec), 'test_size': len(te_rec),
        'class_distribution': dict(dist),
        'train_accuracy': round(train_acc, 4),
        'test_accuracy': round(test_acc, 4),
        'test_macro_f1': round(macro_f1, 4),
        'baseline_accuracy': round(baseline_acc, 4),
        'cv_accuracy_mean': round(float(np.mean(cv_scores)), 4),
        'cv_accuracy_std': round(float(np.std(cv_scores)), 4),
        'classification_report': classification_report(te_y, test_pred, labels=PRIORITY_LABELS,
                                                       output_dict=True),
        'confusion_matrix': {'labels': PRIORITY_LABELS, 'matrix': cm.tolist()},
        'sklearn_version': sklearn.__version__,
        'note': 'Trained on SYNTHETIC data; metrics show method behaviour, not real-world accuracy.',
    }
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump({'classifier': clf, 'encoder': encoder, 'labels': PRIORITY_LABELS,
                 'metrics': metrics}, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    with open(METRICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    line()
    print(' SAVED (final model retrained on all records)')
    print(f"  {os.path.relpath(MODEL_PATH, ROOT)}")
    print(f"  {os.path.relpath(VECTORIZER_PATH, ROOT)}")
    print(f"  {os.path.relpath(METRICS_PATH, ROOT)}")
    line()


if __name__ == '__main__':
    main()
