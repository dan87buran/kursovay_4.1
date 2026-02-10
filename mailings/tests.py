from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Client, Message, Mailing, MailingAttempt
import datetime

User = get_user_model()


class UsersTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

    def test_user_registration(self):
        response = self.client.post(reverse('users:register'), {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'phone': '+79991234567',
            'country': 'Россия'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_user_login(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertTrue('_auth_user_id' in self.client.session)


class MailingsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        self.client_model = Client.objects.create(
            email='client@example.com',
            full_name='Иванов Иван',
            comment='Тестовый клиент',
            owner=self.user
        )

        self.message = Message.objects.create(
            subject='Тестовое сообщение',
            body='Тестовое тело сообщения',
            owner=self.user
        )

        self.mailing = Mailing.objects.create(
            start_time=timezone.now() + datetime.timedelta(hours=1),
            end_time=timezone.now() + datetime.timedelta(days=1),
            message=self.message,
            owner=self.user
        )
        self.mailing.clients.add(self.client_model)

    def test_client_creation(self):
        self.assertEqual(self.client_model.email, 'client@example.com')
        self.assertEqual(self.client_model.owner, self.user)

    def test_message_creation(self):
        self.assertEqual(self.message.subject, 'Тестовое сообщение')
        self.assertEqual(self.message.owner, self.user)

    def test_mailing_creation(self):
        self.assertEqual(self.mailing.message, self.message)
        self.assertEqual(self.mailing.clients.count(), 1)
        self.assertEqual(self.mailing.owner, self.user)

    def test_mailing_status(self):
        # Созданная рассылка должна иметь статус "created"
        self.assertEqual(self.mailing.status, 'created')

        # Изменяем время на период рассылки
        self.mailing.start_time = timezone.now() - datetime.timedelta(hours=1)
        self.mailing.save()
        self.assertEqual(self.mailing.status, 'started')

        # Завершенная рассылка
        self.mailing.end_time = timezone.now() - datetime.timedelta(minutes=30)
        self.mailing.save()
        self.assertEqual(self.mailing.status, 'completed')

    def test_mailing_attempt_creation(self):
        attempt = MailingAttempt.objects.create(
            mailing=self.mailing,
            status='success',
            server_response='Тестовый ответ'
        )
        self.assertEqual(attempt.mailing, self.mailing)
        self.assertEqual(attempt.status, 'success')


class ViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='test@example.com', password='testpass123')

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Добро пожаловать')

    def test_mailing_list_view(self):
        response = self.client.get(reverse('mailings:mailing_list'))
        self.assertEqual(response.status_code, 200)

    def test_client_list_view(self):
        response = self.client.get(reverse('mailings:client_list'))
        self.assertEqual(response.status_code, 200)

    def test_message_list_view(self):
        response = self.client.get(reverse('mailings:message_list'))
        self.assertEqual(response.status_code, 200)

    def test_attempt_list_view(self):
        response = self.client.get(reverse('mailings:attempt_list'))
        self.assertEqual(response.status_code, 200)

    def test_reports_view(self):
        response = self.client.get(reverse('mailings:reports'))
        self.assertEqual(response.status_code, 200)


class PermissionTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )

        # Создаем клиента от имени user1
        self.client1 = Client.objects.create(
            email='client1@example.com',
            full_name='Клиент 1',
            owner=self.user1
        )

        # Создаем сообщение от имени user1
        self.message1 = Message.objects.create(
            subject='Сообщение 1',
            body='Тело сообщения 1',
            owner=self.user1
        )

    def test_user_can_only_see_own_clients(self):
        # Логинимся как user2
        client = Client()
        client.login(username='user2@example.com', password='testpass123')

        # Пытаемся получить клиента user1
        response = client.get(reverse('mailings:client_update', args=[self.client1.pk]))
        self.assertEqual(response.status_code, 404)  # Не найдено, так как нет доступа