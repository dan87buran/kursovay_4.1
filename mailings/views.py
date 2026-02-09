from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView,
    UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Mailing, Client, Message, MailingAttempt
from .forms import (
    MailingForm, ClientForm, MessageForm,
    MailingSendForm
)


def index(request):
    """Главная страница"""
    cache_key = 'home_page_stats'
    stats = cache.get(cache_key)

    if not stats:
        total_mailings = Mailing.objects.count()
        active_mailings = Mailing.objects.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).count()
        unique_clients = Client.objects.values('email').distinct().count()

        stats = {
            'total_mailings': total_mailings,
            'active_mailings': active_mailings,
            'unique_clients': unique_clients,
        }
        cache.set(cache_key, stats, 300)  # Кешируем на 5 минут

    context = {
        'stats': stats,
    }
    return render(request, 'mailings/index.html', context)


# Базовый класс для проверки владельца
class OwnerRequiredMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.groups.filter(name='Менеджеры').exists():
            return qs
        return qs.filter(owner=self.request.user)

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user or self.request.user.is_superuser


# CRUD для клиентов
class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'mailings/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.groups.filter(name='Менеджеры').exists():
            return queryset
        return queryset.filter(owner=self.request.user)


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailings/client_form.html'
    success_url = reverse_lazy('mailings:client_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Клиент успешно создан!')
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailings/client_form.html'
    success_url = reverse_lazy('mailings:client_list')

    def form_valid(self, form):
        messages.success(self.request, 'Клиент успешно обновлен!')
        return super().form_valid(form)


class ClientDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Client
    template_name = 'mailings/client_confirm_delete.html'
    success_url = reverse_lazy('mailings:client_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Клиент успешно удален!')
        return super().delete(request, *args, **kwargs)


# CRUD для сообщений
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailings/message_list.html'
    context_object_name = 'messages'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.groups.filter(name='Менеджеры').exists():
            return queryset
        return queryset.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailings/message_form.html'
    success_url = reverse_lazy('mailings:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Сообщение успешно создано!')
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailings/message_form.html'
    success_url = reverse_lazy('mailings:message_list')

    def form_valid(self, form):
        messages.success(self.request, 'Сообщение успешно обновлено!')
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailings/message_confirm_delete.html'
    success_url = reverse_lazy('mailings:message_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Сообщение успешно удалено!')
        return super().delete(request, *args, **kwargs)


# CRUD для рассылок
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = 'mailings/mailing_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.groups.filter(name='Менеджеры').exists():
            return queryset
        return queryset.filter(owner=self.request.user)


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        mailing = form.save()
        messages.success(self.request, 'Рассылка успешно создана!')
        return redirect('mailings:mailing_detail', pk=mailing.pk)


class MailingDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Mailing
    template_name = 'mailings/mailing_detail.html'
    context_object_name = 'mailing'


class MailingUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка успешно обновлена!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('mailings:mailing_detail', kwargs={'pk': self.object.pk})


class MailingDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = 'mailings/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Рассылка успешно удалена!')
        return super().delete(request, *args, **kwargs)


# Попытки рассылок
class MailingAttemptListView(LoginRequiredMixin, ListView):
    model = MailingAttempt
    template_name = 'mailings/attempt_list.html'
    context_object_name = 'attempts'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.groups.filter(name='Менеджеры').exists():
            return queryset
        return queryset.filter(mailing__owner=self.request.user)


# Отчеты
@login_required
def reports(request):
    """Страница отчетов"""
    if request.user.groups.filter(name='Менеджеры').exists():
        mailings = Mailing.objects.all()
    else:
        mailings = Mailing.objects.filter(owner=request.user)

    reports_data = []
    for mailing in mailings:
        attempts = mailing.attempts.all()
        success_count = attempts.filter(status='success').count()
        failure_count = attempts.filter(status='failure').count()

        reports_data.append({
            'mailing': mailing,
            'success_count': success_count,
            'failure_count': failure_count,
            'total_attempts': attempts.count(),
            'last_attempt': attempts.first() if attempts.exists() else None,
        })

    context = {
        'reports_data': reports_data,
    }
    return render(request, 'mailings/reports.html', context)


# Отправка рассылки
@login_required
def send_mailing_view(request, pk):
    """Отправка рассылки через интерфейс"""
    mailing = get_object_or_404(Mailing, pk=pk)

    if not (request.user == mailing.owner or
            request.user.groups.filter(name='Менеджеры').exists()):
        messages.error(request, 'У вас нет прав для отправки этой рассылки')
        return redirect('mailings:mailing_list')

    if request.method == 'POST':
        form = MailingSendForm(request.POST)
        if form.is_valid():
            try:
                send_mailing_manually(mailing, request.user)
                messages.success(request, 'Рассылка успешно отправлена!')
                return redirect('mailings:mailing_detail', pk=mailing.pk)
            except Exception as e:
                messages.error(request, f'Ошибка при отправке: {str(e)}')
    else:
        form = MailingSendForm()

    context = {
        'mailing': mailing,
        'form': form,
    }
    return render(request, 'mailings/send_mailing.html', context)


def send_mailing_manually(mailing, user):
    """Ручная отправка рассылки"""
    from django.utils import timezone

    now = timezone.now()

    # Проверка времени
    if not (mailing.start_time <= now <= mailing.end_time):
        raise Exception('Текущее время не входит в период отправки рассылки')

    if not mailing.is_active:
        raise Exception('Рассылка отключена')

    # Отправка писем
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
        except Exception as e:
            MailingAttempt.objects.create(
                mailing=mailing,
                status='failure',
                server_response=str(e)
            )