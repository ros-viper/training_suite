from django.contrib import admin
from nested_inline.admin import NestedStackedInline, NestedTabularInline, NestedModelAdmin
from django_summernote.admin import SummernoteModelAdmin
from django_summernote.widgets import SummernoteWidget
from markdownx.admin import MarkdownxModelAdmin
from markdownx.widgets import AdminMarkdownxWidget
from django.db import models

from quiz.models import Quiz, Question, Answer, SubmittedResult, QuizTries, Quiz_to_Track

    
class AnswerInline(NestedTabularInline):
    model = Answer
    extra = 1
    fk_name = 'question'
    exclude = ('number',)

class TrackInline(NestedTabularInline):
    model = Quiz_to_Track
    extra = 1

class QuestionInline(NestedTabularInline):
    model = Question
    extra = 1
    fk_name = 'quiz'
    formfield_overrides = {models.TextField: {'widget': AdminMarkdownxWidget}}
    inlines = [AnswerInline]
    exclude = ("number",)


class QuizAdmin(NestedModelAdmin):
    model = Quiz
    inlines = [QuestionInline, TrackInline]
    

class QuestionAdmin(MarkdownxModelAdmin):
    list_display = ("__str__", "quiz", "score",)
    exclude = ("number",)
    ordering = ('number', 'quiz',)
    model = Question
    inlines = [AnswerInline]

    
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(SubmittedResult)
admin.site.register(QuizTries)