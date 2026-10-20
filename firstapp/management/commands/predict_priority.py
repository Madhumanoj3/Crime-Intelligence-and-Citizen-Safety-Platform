"""
Fill in the AI Predicted Priority for complaints that do not have one yet
(for example complaints filed before the model was trained).

Usage:
    python manage.py predict_priority           # only complaints without a priority
    python manage.py predict_priority --all     # re-predict every complaint (after retraining)
"""
from django.core.management.base import BaseCommand

from firstapp.models import Complaint
from firstapp.priority_predictor import apply_ai_priority


class Command(BaseCommand):
    help = 'Predict AI priority (Low/Medium/High) for complaints. Only the ai_priority fields are changed.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Re-predict every complaint.')

    def handle(self, *args, **options):
        qs = Complaint.objects.all().order_by('pk')
        if not options['all']:
            qs = qs.filter(ai_priority='')
        done = 0
        for c in qs:
            result = apply_ai_priority(c)
            if not result['priority']:
                self.stderr.write(f"{c.complaint_id}: prediction failed - {result['error']}")
                continue
            done += 1
            self.stdout.write(f"{c.complaint_id:<10} {c.category:<11} -> {result['priority']:<6} "
                              f"({result['confidence']}%)  {c.title[:50]}")
        self.stdout.write(self.style.SUCCESS(f"Predicted priority for {done} complaint(s)."))
