import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('cloudvault')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-expired-trash': {
        'task': 'apps.trash.tasks.cleanup_expired_trash',
        'schedule': crontab(hour=2, minute=0),
    },
    'cleanup-expired-shared-links': {
        'task': 'apps.sharing.tasks.cleanup_expired_links',
        'schedule': crontab(hour=3, minute=0),
    },
    'recalculate-storage-usage': {
        'task': 'apps.accounts.tasks.recalculate_all_storage_usage',
        'schedule': crontab(hour=4, minute=0),
    },
}

app.conf.task_routes = {
    'apps.files.tasks.*': {'queue': 'files'},
    'apps.trash.tasks.*': {'queue': 'maintenance'},
    'apps.sharing.tasks.*': {'queue': 'maintenance'},
    'apps.accounts.tasks.*': {'queue': 'maintenance'},
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
