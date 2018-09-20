from django.contrib import admin
from nested_inline.admin import NestedStackedInline, NestedTabularInline, NestedModelAdmin
from markdownx.admin import MarkdownxModelAdmin
from markdownx.widgets import AdminMarkdownxWidget
from django.db import models

from polls.models import Poll, Question, Option, UserOption, SubmittedResult, UserOption


class OptionInline(NestedTabularInline):
    model = Option
    extra = 1
    fk_name = 'question'
    exclude = ['votes']


class QuestionInline(NestedTabularInline):
    model = Question
    extra = 1
    fk_name = 'poll'
    formfield_overrides = {models.TextField: {'widget': AdminMarkdownxWidget}}
    inlines = [OptionInline]


class PollAdmin(NestedModelAdmin):
    model = Poll
    inlines = [QuestionInline]


admin.site.register(Poll, PollAdmin)
admin.site.register(SubmittedResult)
admin.site.register(UserOption)
