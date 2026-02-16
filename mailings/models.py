from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError


class Client(models.Model):
    """Модель получателя рассылки"""
    objects = None
    email = models.EmailField(
        verbose_name='Email',
        unique=True
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name='Ф.И.О.'
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Владелец',
        related_name='clients'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        permissions = [
            ('view_all_clients', 'Может просматривать всех клиентов'),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.email})'


class Message(models.Model):
    """Модель сообщения"""
    subject = models.CharField(
        max_length=255,
        verbose_name='Тема письма'
    )
    body = models.TextField(
        verbose_name='Тело письма'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Владелец',
        related_name='messages'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        permissions = [
            ('view_all_messages', 'Может просматривать все сообщения'),
        ]

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    """Модель рассылки"""
    objects = None
    STATUS_CHOICES = [
        ('created', 'Создана'),
        ('started', 'Запущена'),
        ('completed', 'Завершена'),
        ('disabled', 'Отключена'),
    ]

    start_time = models.DateTimeField(
        verbose_name='Время начала отправки'
    )
    end_time = models.DateTimeField(
        verbose_name='Время окончания отправки'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name='Сообщение'
    )
    clients = models.ManyToManyField(
        Client,
        verbose_name='Получатели'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Владелец',
        related_name='mailings'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        permissions = [
            ('view_all_mailings', 'Может просматривать все рассылки'),
            ('disable_mailing', 'Может отключать рассылки'),
        ]

    def __str__(self):
        return f'Рассылка #{self.id} от {self.created_at.strftime("%d.%m.%Y")}'

    @property
    def status(self):
        """Динамическое вычисление статуса"""
        now = timezone.now()

        if not self.is_active:
            return 'disabled'
        elif now < self.start_time:
            return 'created'
        elif self.start_time <= now <= self.end_time:
            return 'started'
        else:
            return 'completed'

    def clean(self):
        """Валидация времени"""
        if self.start_time < timezone.now():
            raise ValidationError('Время начала не может быть в прошлом')

        if self.start_time >= self.end_time:
            raise ValidationError('Время начала должно быть раньше времени окончания')

    def get_active_mailings_count(self):
        """Количество активных рассылок"""
        now = timezone.now()
        return Mailing.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        ).count()


class MailingAttempt(models.Model):
    """Модель попытки рассылки"""
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failure', 'Не успешно'),
    ]

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        verbose_name='Рассылка',
        related_name='attempts'
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время попытки'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        verbose_name='Статус'
    )
    server_response = models.TextField(
        verbose_name='Ответ почтового сервера',
        blank=True
    )

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылок'
        ordering = ['-attempt_time']

    def __str__(self):
        return f'Попытка #{self.id} - {self.get_status_display()}'