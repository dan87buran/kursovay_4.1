from django.contrib import admin
from .models import Client, Message, Mailing, MailingAttempt


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'owner', 'created_at')
    list_filter = ('owner', 'created_at')
    search_fields = ('email', 'full_name', 'comment')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'full_name', 'owner')}),
        ('Дополнительно', {'fields': ('comment', 'created_at')}),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'owner', 'created_at')
    list_filter = ('owner', 'created_at')
    search_fields = ('subject', 'body')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('subject', 'body', 'owner')}),
        ('Дополнительно', {'fields': ('created_at',)}),
    )


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'start_time', 'end_time', 'status_display', 'owner', 'is_active')
    list_filter = ('is_active', 'start_time', 'end_time', 'owner')
    search_fields = ('message__subject',)
    filter_horizontal = ('clients',)
    readonly_fields = ('created_at', 'status_display')
    fieldsets = (
        (None, {'fields': ('message', 'clients', 'owner')}),
        ('Время отправки', {'fields': ('start_time', 'end_time')}),
        ('Статус', {'fields': ('status_display', 'is_active', 'created_at')}),
    )

    def status_display(self, obj):
        return obj.get_status_display()

    status_display.short_description = 'Статус'


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ('mailing', 'attempt_time', 'status', 'server_response_preview')
    list_filter = ('status', 'attempt_time', 'mailing')
    search_fields = ('server_response', 'mailing__message__subject')
    readonly_fields = ('attempt_time',)
    fieldsets = (
        (None, {'fields': ('mailing', 'status')}),
        ('Детали', {'fields': ('server_response', 'attempt_time')}),
    )

    def server_response_preview(self, obj):
        if len(obj.server_response) > 50:
            return f'{obj.server_response[:50]}...'
        return obj.server_response

    server_response_preview.short_description = 'Ответ сервера'