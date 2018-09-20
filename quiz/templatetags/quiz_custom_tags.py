from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from quiz.models import Question, QuizTries

register = template.Library()

@register.simple_tag(takes_context=True)
def radio_or_checkbox(context):
    question = context['question']
    
    if question.correct_number == 1:
        return "radio"
    return "checkbox"
   
@register.simple_tag(takes_context=True) 
def tries_or_dash(context):
    quiz = context['quiz']
    student = context['student']
    
    try:
        return QuizTries.objects.get(quiz=quiz, student=student).tries
    except ObjectDoesNotExist:
        return "-"
    
    
    