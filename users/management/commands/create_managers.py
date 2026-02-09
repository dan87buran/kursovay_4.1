from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import User
from mailings.models import Mailing, Client, Message


class Command(BaseCommand):
    help = 'Создание группы менеджеров с необходимыми правами'

    def handle(self, *args, **options):
        # Создаем группу менеджеров
        manager_group, created = Group.objects.get_or_create(name='Менеджеры')

        # Получаем разрешения из мета-классов моделей
        mailing_content_type = ContentType.objects.get_for_model(Mailing)
        client_content_type = ContentType.objects.get_for_model(Client)
        message_content_type = ContentType.objects.get_for_model(Message)
        user_content_type = ContentType.objects.get_for_model(User)

        # Добавляем права на просмотр всех записей
        view_all_mailings = Permission.objects.get(
            codename='view_all_mailings',
            content_type=mailing_content_type
        )
        view_all_clients = Permission.objects.get(
            codename='view_all_clients',
            content_type=client_content_type
        )
        view_all_messages = Permission.objects.get(
            codename='view_all_messages',
            content_type=message_content_type
        )

        # Права для блокировки пользователей и отключения рассылок
        can_disable_mailing = Permission.objects.get(
            codename='disable_mailing',
            content_type=mailing_content_type
        )

        # Права на просмотр пользователей
        view_user = Permission.objects.get(
            codename='view_user',
            content_type=user_content_type
        )

        # Добавляем права в группу
        manager_group.permissions.add(
            view_all_mailings,
            view_all_clients,
            view_all_messages,
            can_disable_mailing,
            view_user,
        )

        self.stdout.write(self.style.SUCCESS('Группа "Менеджеры" создана с правами доступа'))