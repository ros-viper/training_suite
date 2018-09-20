from uuid import uuid4

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.template import TemplateSyntaxError, Node

from TrainingSuite.models import Comment, Task, Solution, Notification, OfflineSession, Attendance
from quiz.models import SubmittedResult

register = template.Library()


@register.simple_tag(takes_context=True)
def task_is_solved_by(context):
    task = context['task']
    user = context['request'].user

    return task.is_solved_by(user)

@register.simple_tag(takes_context=True)
def comments_number(context):
    task = context.get('object', None)
    if not isinstance(task, Task): # Sometimes object is Session so we need to be sure it is Task object
        task = context['task']
    user = context['request'].user

    try:
        target_solution = Solution.objects.filter(Q(task=task)&Q(author=user.student)).distinct()
        if target_solution:
            target_solution = target_solution[0]
            comments_on_solutions = Comment.objects.filter(target_solution=target_solution).filter(target_comment=None)
            comments_on_comments = Comment.objects.filter(target_comment__in=comments_on_solutions).distinct()
            return comments_on_solutions.count() + comments_on_comments.count()
        return 0
    except ObjectDoesNotExist:  # If trainer
        target_solutions = Solution.objects.filter(task=task).distinct()
        comments_on_solutions = Comment.objects.filter(target_solution__in=target_solutions).distinct()
        comments_on_comments = Comment.objects.filter(target_comment__in=comments_on_solutions).distinct()
        return comments_on_solutions.count() + comments_on_comments.count()
    except ObjectDoesNotExist:  # If trainer
        return Comment.objects.filter(target_solution__task=task).count()
    except UnboundLocalError:  # if no solutions - .one() will throw this
        return 0

@register.simple_tag(takes_context=True)
def solutions_number(context):
    task = context.get('object', None)
    if not isinstance(task, Task): # Sometimes object is Session so we need to be sure it is Task object
        task = context['task']

    return Solution.objects.filter(task=task).count()


@register.simple_tag(takes_context=True)
def get_submitted_solution(context):
    task = context['object']
    user = context['request'].user

    try:
        if task.solution_set.filter(author=user.student).count():
            return task.solution_set.filter(author=user.student)[0]
        else:
            return task.default_solution
    except ObjectDoesNotExist:
        return ""


@register.simple_tag(takes_context=True)
def is_solution_submitted(context):
    task = context['object']
    user = context['request'].user

    try:
        return task.solution_set.filter(author=user.student)[0].committed
    except (ObjectDoesNotExist, IndexError):
        #In case Trainer is used instead of Student or solution not found
        return False

@register.simple_tag(takes_context=True)
def get_all_unseen_notification(context):
    user = context['request'].user

    return Notification.objects.filter(user=user, seen=False)


class UUIDNode(Node):
    """
    Implements the logic of this tag.
    """

    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        context[self.var_name] = str(uuid4())
        return ''


def do_uuid(parser, token):
    """
    The purpose of this template tag is to generate a random
    UUID and store it in a named context variable.

    Sample usage:
        {% uuid var_name %}
        var_name will contain the generated UUID
    """
    try:
        tag_name, var_name = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError("%s tag requires exactly one argument" % token.contents.split()[0])
    return UUIDNode(var_name)


do_uuid = register.tag('uuid', do_uuid)


def short_name(value):
    """Returns Name L. instead of Name Lastname"""
    parts = value.split()
    return "{} {}.".format(parts[0].capitalize(), parts[1][0].upper()) if (len(parts) > 1 and len(parts[1]) > 1) else value.capitalize()
register.filter('short_name', short_name)

# check if quiz for offline_session has been passed
@register.simple_tag(takes_context=True)
def is_passed(context, session_id):
    student = context['request'].user.student
    object = context['object']
    try:
        quiz = OfflineSession.objects.get(id=int(session_id)).quiz
    except ObjectDoesNotExist:
        return False

    try:
        return SubmittedResult.objects.get(student=student, quiz=quiz).passed
    except ObjectDoesNotExist:
        return False


@register.simple_tag(takes_context=True)
def attendance_checked(context):
    session = context['object']
    student = context['student']

    return "checked" if Attendance.objects.filter(session=session, student=student).count() else ""