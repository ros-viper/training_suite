from django import template
from django.core.exceptions import ObjectDoesNotExist

from polls.models import SubmittedResult

register = template.Library()

@register.assignment_tag(takes_context=True)
def get_is_submitted_by_user(context):
    poll = context['p']
    request = context['request']
    
    try:
        return True if SubmittedResult.objects.filter(poll=poll, student=request.user.student).count() else False    
    except:
        return False


@register.filter
def minutes(text):
    try:
        return int(int(text) * 0.2)
    except TypeError:
        pass