from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import (
    Teaching, Schedule, Donation, Event, Blog, Subscriber,
    Message, ChatGroup, GroupMembership, GroupMessage
)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'content')
    ordering = ('-created_at',)

@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_private', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'user', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'group__name')
    ordering = ('-joined_at',)

@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'sender', 'created_at')
    search_fields = ('group__name', 'sender__username', 'content')
    ordering = ('created_at',)

admin.site.register(Teaching)
admin.site.register(Schedule)
admin.site.register(Donation)
admin.site.register(Event)
admin.site.register(Blog)
admin.site.register(Subscriber)
