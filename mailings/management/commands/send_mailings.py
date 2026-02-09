from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from mailings.models import Mailing, MailingAttempt


class Command(BaseCommand):
    help = 'Отправка рассылок через командную строку'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mailing-id',
            type=int,
            help='ID конкретной рассылки для отправки'
        )

    def handle(self, *args, **options):
        mailing_id = options.get('mailing_id')
        now = timezone.now()

        if mailing_id:
            # Отправка конкретной рассылки
            mailings = Mailing.objects.filter(pk=mailing_id, is_active=True)
        else:
            # Автоматическая отправка активных рассылок
            mailings = Mailing.objects.filter(
                is_active=True,
                start_time__lte=now,
                end_time__gte=now
            )

        total_sent = 0
        total_failed = 0

        for mailing in mailings:
            self.stdout.write(f'Отправка рассылки #{mailing.id}')

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
                        server_response='Успешно отправлено'
                    )
                    total_sent += 1
                    self.stdout.write(f'  ✓ Отправлено: {client.email}')

                except Exception as e:
                    MailingAttempt.objects.create(
                        mailing=mailing,
                        status='failure',
                        server_response=str(e)
                    )
                    total_failed += 1
                    self.stdout.write(f'  ✗ Ошибка для {client.email}: {str(e)}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Отправка завершена. Успешно: {total_sent}, Ошибок: {total_failed}'
            )
        )