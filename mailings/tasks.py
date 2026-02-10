
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Mailing, MailingAttempt


@shared_task
def send_scheduled_mailings():
    """Автоматическая отправка запланированных рассылок"""
    now = timezone.now()

    # Находим рассылки, которые нужно отправить прямо сейчас
    mailings = Mailing.objects.filter(
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    )

    total_sent = 0
    total_failed = 0

    for mailing in mailings:
        for client in mailing.clients.all():
            try:
                send_mail(
                    subject=mailing.message.subject,
                    message=mailing.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[client.email],
                    fail_silently=False,
                )

                MailingAttempt.objects.create(
                    mailing=mailing,
                    status='success',
                    server_response='Отправлено автоматически'
                )
                total_sent += 1

            except Exception as e:
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status='failure',
                    server_response=str(e)
                )
                total_failed += 1

    return {
        'total_sent': total_sent,
        'total_failed': total_failed,
        'timestamp': now.isoformat()
    }


@shared_task
def update_mailing_statuses():
    """Обновление статусов рассылок (например, завершенных)"""
    now = timezone.now()

    # Находим рассылки, которые должны быть завершены
    completed_mailings = Mailing.objects.filter(
        is_active=True,
        end_time__lt=now
    )

    count = completed_mailings.count()
    # Статус вычисляется динамически, поэтому ничего обновлять не нужно
    # Но можно добавить логику для уведомлений и т.д.

    return {
        'updated_count': count,
        'timestamp': now.isoformat()
    }