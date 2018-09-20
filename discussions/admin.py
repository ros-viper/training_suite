from django.contrib import admin
from nested_inline.admin import NestedStackedInline, NestedTabularInline, NestedModelAdmin
from markdownx.admin import MarkdownxModelAdmin
from markdownx.widgets import AdminMarkdownxWidget
from django.db import models
from discussions.models import DiscussionMessage, DiscussionThread
# Register your models here.

class DiscussionMessageInline(NestedTabularInline):
    model = DiscussionMessage
    extra = 1
    fk_name = 'thread'
    formfield_overrides = {models.TextField: {'widget': AdminMarkdownxWidget}}
    exclude = ("number",)

class DiscussionThreadAdmin(NestedModelAdmin):
    model = DiscussionThread
    inlines = [DiscussionMessageInline]

admin.site.register(DiscussionThread, DiscussionThreadAdmin)