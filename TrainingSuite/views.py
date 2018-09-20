import datetime
import json

import re
from collections import defaultdict, Counter
from functools import wraps

from django.conf.urls import url
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import QuerySet, Q
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.core.urlresolvers import reverse
import requests
from threading import Thread

from TrainingSuite.models import Course, Session, Student, Trainer, Task, Solution, Comment, Resource, Setting, \
    Notification, Slideshow, Slides_to_Sessions, Track_to_Trainer, Course_to_Track, Track, Runner, OfflineCourse, \
    OfflineSession, Resource_to_OfflineSession, Task_to_OfflineSession, Slideshow_to_OfflineSession, OfflineCourse_to_Track, \
    Attendance

from discussions.models import DiscussionThread
from quiz.models import SubmittedResult
from training_suite.settings import EMAIL_HOST_USER, EMAIL_HOST_API_KEY, EMAIL_HOST_SUBJECT, EMAIL_HOST_URL, TIME_ZONE


# Create your views here.
from quiz.models import Quiz

class NotFound(Exception): pass

class TooManyFound(Exception): pass

# Threading to postpone tasks
def threaded(function):
    @wraps(function)
    def decorator(*args, **kwargs):
        t = Thread(target = function, args=args, kwargs=kwargs)
        t.start()
    return decorator

def handle_404(view):
    @wraps(view)
    def wr(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except TooManyFound:
            return HttpResponseNotFound(
                '<h1>Page/resource as you requested not found or you are not subscribed to the related Course</h1>')
        except NotFound:
            return HttpResponseNotFound(
                '<h1>Page/resource requested not found or you are not subscribed to the related Course</h1>')

    return wr


def get_many_or_404(model, *args, **kwargs):
    """
    Helper to get list of elements based on query

    :param model: model used
    :return: list or 404
    """

    try:
        # print("ARGS:", args, kwargs)
        res = model.objects.filter(*args, **kwargs).distinct()
        # print(list(id(x) for x in res))
        # print(res[0] == res[1])
        if not res or not len(res) > 0:
            raise NotFound
        return res
    except ObjectDoesNotExist:
        raise NotFound

def get_one_or_404(model, *args, **kwargs):
    """
    Get single element based on query or 404

    :param model: model used
    :return: object or 404
    """

    results = model.objects.filter(*args, **kwargs).distinct()
    if not results:
        raise NotFound
    elif len(results) > 1:
        raise TooManyFound
    return results[0]


def get_default_context(request, model, object, object_list=None):
    """
    Idea is to have some default pack of data in all views where it is possible - for specific models

    :param request: request
    :param model: Model
    :param object: processed object
    :return: context dict
    """

    # context = {'request': request} # We already have request in context, wow...
    context = dict(request=request)
    # if isinstance(object, model):
    #     context.update(object=object)
    if object:
        context.update(object=object)
    if object_list:
        context.update(object_list=object_list)
    courses_dict = {course: course.session_set.all() for course in get_subscribed_courses(request.user)}
    courses_dict.update({course: course.offlinesession_set.all() for course in get_subscribed_offline_courses(request.user)})
    # for course in get_subscribed_courses(request.user)['courses']:
    #     courses_dict.update({course:course.session_set.all()})
    # for course in get_subscribed_courses(request.user)['offline_courses']:
    #     courses_dict.update({course: course.offlinesession_set.all()})
    context.update(courses=courses_dict)

    if model is Task:
        if object:
            context.update(
                # sessions = object.session.course.session_set.all(),
                # active_session = object.session.order,
                active='sessions',
            )
        if object_list:
            task_courses = set()
            for task in object_list:
                for session in task.sessions.all():
                    task_courses.add(session.course)
            context.update(task_courses=set(task_courses))

    elif model is Session:
        context.update(
            sessions=object.course.session_set.all(),
            active_session=object.order,
            active='sessions',
        )
    elif model is Course:
        context.update(
            active='courses',
        )
        if isinstance(object, model):
            context.update(
                sessions=object.session_set.all(),
            )
    elif model is Solution:
        # if isinstance(object, Solution):
        #     sessions = object.task.session.course.session_set.all()
        # elif isinstance(object, Task):
        #     sessions = object.session.course.session_set.all()
        # else:
        #     sessions = []
        context.update(
            active='reviews',

            # sessions = sessions,
        )
    return context


def get_subscribed_courses(user):
    courses = []
    try:
        courses.extend(list(Course.objects.filter(trainers=user.trainer)))
        # offline_courses = list(OfflineCourse.objects.filter(author=user.trainer))
    except: pass
    try:
        courses.extend(list(user.student.courses.all()))
        # offline_courses = list(user.student.offline_courses.all())
    except: pass

    # combined_courses = {'courses': courses, 'offline_courses': offline_courses}
    # return combined_courses
    return courses

def get_subscribed_offline_courses(user):
    offline_courses = []
    try:
        offline_courses.extend(list(OfflineCourse.objects.filter(author=user.trainer)))
    except:
        pass
    try:
        offline_courses.extend(list(user.student.offline_courses.all()))
    except:
        pass

    return offline_courses

def get_available_assets(tracks, type_):
    try:
        return ordered_set(type_.objects.filter(track__in=tracks))
    except AttributeError:
        return []

def get_allowed_offline_sessions(course, user):
    allowed_sessions = list(course.offlinesession_set.filter(required=False))
    required_sessions = list(course.offlinesession_set.filter(required=True))
    allowed_sessions.append(required_sessions[0])

    try:
        user.trainer
        allowed_sessions = list(course.offlinesession_set.all())
        return allowed_sessions
    except AttributeError:
        pass

    for index, session in enumerate(required_sessions):
        try:
            submitted_result = SubmittedResult.objects.get(quiz=session.quiz, student=user.student)
            if submitted_result.passed:
                allowed_sessions.append(required_sessions[index+1])
        except (ObjectDoesNotExist, IndexError, AttributeError):
            pass

    return allowed_sessions

def ordered_set(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


@login_required
def password_change(request):
    template_name = 'registration/password_change_form.html'
    return render(request, template_name, {})


@login_required
def view_task(request, pk):
    model = Task
    template_name = 'task_detail.html'
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object)
    try:
        commented_lines = [x.target_line for x in Solution.objects.filter(
            task=object,
            author=request.user.student)[0].comment_set.all()]
    except (IndexError, ObjectDoesNotExist):
        commented_lines = []

    if request.method == 'POST':
        solution = Solution.objects.get_or_create(
            author=request.user.student,
            task=object)
        solution = solution[0]  # get_or_create function returns tuple with object and True or False on whether object was created as new
        if not solution.committed:
            solution.content = request.POST.get('solution', '')
            if request.POST.get('committing', '') == 'TRUE':
                solution.committed = True
                solution.committed_at = datetime.datetime.now()
        solution.save()
    context.update(commented_lines=commented_lines)
    return render(request, template_name, context)


@login_required
def view_session(request, pk):
    model = Session
    template_name = 'session_detail.html'
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object)

    chosen_slides = object.slides.all()
    chosen_tasks = object.task_set.all()
    chosen_resources = object.resource_set.all()

    context.update(
        chosen_resources = chosen_resources,
        chosen_tasks = chosen_tasks,
        chosen_slides = chosen_slides,
    )

    return render(request, template_name, context)


@login_required
def view_course(request, pk):
    model = Course
    template_name = 'course_detail.html'
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object)
    sessions = object.session_set.all()
    context.update(
        sessions = sessions,
    )

    return render(request, template_name, context)

@login_required
def view_offline_course(request, pk):
    model = OfflineCourse
    template_name = 'course_detail.html'
    user = request.user
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object)
    sessions = object.offlinesession_set.all()
    allowed_sessions = get_allowed_offline_sessions(object, user)

    try:
        user.student
        current_session = [s for s in allowed_sessions if s.required][-1]
        context.update(current_session=current_session)
    except ObjectDoesNotExist:
        pass

    context.update(
        sessions=sessions,
        allowed_sessions=allowed_sessions
    )

    return render(request, template_name, context)


@login_required
def list_courses(request):
    model = Course
    template_name = 'list_courses.html'
    user = request.user
    courses = get_subscribed_courses(user)
    context = get_default_context(request, model, None)
    offline_courses = get_subscribed_offline_courses(user)

    try:
        tracks = user.trainer.tracks.all()
        additional_trainers = set()

        # Adding available trainers for available tracks
        for track in tracks:
            additional_trainers.update(track.trainers.all())
        additional_trainers.remove(request.user.trainer)
        additional_trainers = list(additional_trainers)
    except (ObjectDoesNotExist, KeyError):
        tracks = []
        additional_trainers = set()

    if request.method == "POST" and 'course_name' in request.POST:
        if 'offline_course' in request.POST and request.POST['offline_course'] == 'True':
            course = OfflineCourse.objects.create(
                name = request.POST['course_name'],
                author = request.user.trainer
            )

            if 'tracks' in request.POST:
                for track in request.POST.getlist('tracks'):
                    try:
                        OfflineCourse_to_Track.objects.create(
                            offline_course = course,
                            track = Track.objects.get(id=int(track))
                        )
                    except (TypeError, ObjectDoesNotExist):
                        pass
        else:
            course = Course.objects.create(
                name = request.POST['course_name'],
            )
            course.trainers.add(request.user.trainer)

            if 'tracks' in request.POST:
                for track in request.POST.getlist('tracks'):
                    try:
                        Course_to_Track.objects.create(
                            course = course,
                            track = Track.objects.get(id=int(track))
                        )
                    except (TypeError, ObjectDoesNotExist):
                        pass
            if 'trainers' in request.POST:
                for trainer in request.POST.getlist('trainers'):
                    course.trainers.add(trainer)

        if 'start_date' in request.POST:
            try:
                date = datetime.datetime.strptime(request.POST['start_date'], "%d/%m/%Y")
                course.start_date = date
            except ValueError:
                pass

        if 'end_date' in request.POST:
            try:
                time = datetime.datetime.strptime(request.POST['end_date'], "%d/%m/%Y")
                course.end_date = time
            except ValueError:
                pass

        course.active = request.POST.get('course_active', False)
        course.save()

        return redirect('view_course' if isinstance(course, Course) else 'view_offline_course', course.id)

    context.update(        
        object_list=courses,
        global_stats=dict(
            total_users=Student.objects.count(),
            hometasks=Task.objects.count(),
            solutions=Solution.objects.count(),
            comments=Comment.objects.count(),
        ),
        user_stats = dict(
            tasks_done=Solution.objects.filter(author=request.user.student, committed=True).count(),
            tasks_in_progress=Solution.objects.filter(author=request.user.student, committed=False).count(),
            tasks_total=Task.objects.filter(sessions__course__in=courses).count(),
            comments=Comment.objects.filter(target_solution__author=request.user.student).count(),
        ) if hasattr(request.user, 'student') else None,
        trainer_stats = dict(
            active_courses=len([x for x in courses if x.active]),
            current_students=Student.objects.filter(courses__in=courses).count(),
            comments_written=Comment.objects.filter(author_trainer=request.user.trainer).count(),
        ) if hasattr(request.user, 'trainer') else None,
        tracks=tracks,
        additional_trainers=additional_trainers,
        offline_courses=offline_courses,
    )
    return render(request, template_name, context)


@login_required
def list_resources(request):
    model = Resource
    template_name = 'list_resources.html'
    user = request.user
    courses = get_subscribed_courses(user)

    dict = {}
    resources = []
    for r in Resource.objects.filter(sessions__course__in=courses):
        dict[r] = r.sessions.all().order_by("order")[0].order
    for k, v in sorted(dict.items(), key=lambda x: x[1]):
        resources.append(k)

    context = get_default_context(request, model, None)
    context.update(object_list=resources)
    return render(request, template_name, context)


@login_required
def list_slides(request):
    model = Slideshow
    template_name = 'list_slides.html'
    user = request.user
    courses = get_subscribed_courses(user)
    slides_count = Slideshow.objects.all().count()

    if request.method == "POST" and request.POST['name'] != "" and request.POST['courses'] != "":
        slides = Slideshow.objects.create(
            name=request.POST['name'],
            path = request.POST['path'],
            comment = request.POST['comment'],
            )
        for course in request.POST.getlist('courses'):
            slides.courses.add(course)
        slides.save()

        return redirect('list_slides')

    context = get_default_context(request, model, None)
    context.update(
        object_list=Slideshow.objects.filter(Q(sessions__course__in=courses) | Q(courses__in=courses)).order_by('order').distinct(),
        slides_count=slides_count,
        subscribed_courses=courses,
        )
    return render(request, template_name, context)


@login_required
def list_hometasks(request):
    model = Task
    template_name = 'list_hometasks.html'
    user = request.user
    courses = get_subscribed_courses(user)
    tasks = ordered_set(model.objects.filter(sessions__course__in=courses).order_by('sessions'))
    context = get_default_context(request, model, None, tasks)
    return render(request, template_name, context)


@login_required
@user_passes_test(lambda user: user.trainer)
def list_solutions(request):
    model = Task
    template_name = 'list_solutions.html'
    user = request.user
    courses = get_subscribed_courses(user)
    tasks = set(model.objects.filter(sessions__course__in=courses).all().order_by('sessions'))
    context = get_default_context(request, model, None, tasks)
    return render(request, template_name, context)


@login_required
def view_solutions(request, pk):
    model = Solution
    template_name = 'solutions_review.html'
    task = get_one_or_404(Task, pk=pk)
    object_list = Solution.objects.filter(task=task).all()
    context = get_default_context(request, model, task, object_list)
    return render(request, template_name, context)


@login_required
def download_resource(request, pk):
    resource = get_one_or_404(Resource, id=pk)
    CONTENT_TYPES = defaultdict(
        default_factory=lambda: 'application/pdf',
        PDF='application/pdf',
        DOC='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        EBOOK='application/epub+zip',
        ZIP='application/zip',
    )

    courses = get_subscribed_courses(request.user)
    if resource.sessions.filter(course__in=courses):
        if resource.resource_type == 'URL':
            return redirect(resource.url)
        response = HttpResponse(open(resource.physical_location, 'rb').read(),
                                content_type='%s' % CONTENT_TYPES[resource.resource_type])
        response['Content-Disposition'] = 'attachment; filename=%s' % resource.name
        return response
    else:
        return HttpResponseNotFound('<h1>Resource not found or you are not subscribed to the related Course</h1>')


@login_required
def view_solution(request, pk):
    model = Solution
    user = request.user
    template_name = 'solution_review.html'
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object)
    if request.method == 'POST' and 'comment' in request.POST:
        try:
            target_line = int(request.POST.get('target_line', '-1'))
        except TypeError:
            target_line = -1
        new_comment = Comment(
            target_solution=object,
            content=request.POST.get('comment', ''),
            target_line=target_line)
        if user.trainer:
            new_comment.author_trainer = user.trainer
        else:
            new_comment.author_student = user.student
        new_comment.save()
        return redirect('view_solution', pk=pk)

    context.update(commented_lines=list(set(x.target_line for x in object.comment_set.all())))
    return render(request, template_name, context)


@login_required
def comment_reply(request, pk):
    model = Comment
    if request.method == 'POST' and 'comment' in request.POST:
        comment_type = request.POST.get('comment_type', '')
        try:
            target_solution_or_task = int(request.POST['target'])
        except (KeyError, TypeError):
            target_solution_or_task = None
        if comment_type == 'overall':
            object_ = get_one_or_404(Solution, pk=pk)
        else:
            object_ = get_one_or_404(model, pk=pk)
        new_comment = Comment(
            target_comment=object_ if comment_type != 'overall' else None,
            target_solution=object_ if comment_type == 'overall' else object_.target_solution,
            content=request.POST.get('comment', ''),
            author_student=request.user.student if hasattr(request.user, 'student') else None,
            author_trainer=request.user.trainer if hasattr(request.user, 'trainer') else None,
        )
        new_comment.save()
        if target_solution_or_task:
            if hasattr(request.user, 'student'):
                return redirect(reverse('view_task', kwargs={'pk': target_solution_or_task}))
            else:
                return redirect(reverse('view_solution', kwargs={'pk': target_solution_or_task}))

    return redirect(reverse('list_hometasks'))


@login_required
def edit_course(request, pk):
    model = Course
    template_name = 'edit_course.html'
    object = get_one_or_404(model, pk=pk)
    user = request.user
    tracks = user.trainer.tracks.all()
    additional_trainers = set()


    # Adding available trainers for available tracks

    for track in tracks:
        additional_trainers.update(track.trainers.all())
    additional_trainers.remove(request.user.trainer)
    additional_trainers = list(additional_trainers)

    if request.method == 'POST' and 'users' in request.POST:
        users_list = []
        for list_part in request.POST.get('users', '').replace('\n', '').split(','):
            res = re.search(r'["\']?(\w+(?:\s\w+)*?)["\']?\s+<?([\w\._\-+]+@[\w\._\-]+)', list_part)
            try:
                users_list.append(res.groups())
            except: pass
        users_list = set(users_list)
        missing_users = set(list(filter(lambda x: not User.objects.filter(username=x[1][:30]), users_list)))
        for x in missing_users:
            fn, ln = x[0].rsplit(maxsplit=1) if ' ' in x[0] else (x[0], '')
            user = User.objects.create_user(username=x[1][:30], first_name=fn, last_name=ln, email=x[1], password=x[1])
            student = Student.objects.create(email=x[1], name=x[0], user=user)
            student.save()
            student.courses.add(object)
            student.save()
            send_mail(x[1], "Hello, "+fn+"!\n\nThe user in Training Suite has been created for you.\nYour login/password: your Email.")
        existing_users = users_list - missing_users
        for x in existing_users:
            student = User.objects.get(username=x[1][:30]).student
            student.courses.add(object)
            student.save()

    # Update the course
    elif request.method == 'POST' and 'course_name' in request.POST:
        object.name = request.POST['course_name']
        object.active = request.POST.get('course_active', False)


        # Change the start_date
        try:
            object.start_date = datetime.datetime.strptime(request.POST['start_date'], "%d/%m/%Y")
        except (ValueError, KeyError):
            object.start_date = None

        # Change the end_date
        try:
            object.end_date = datetime.datetime.strptime(request.POST['end_date'], "%d/%m/%Y")
        except (ValueError, KeyError):
            object.end_date = None

        object.trainers.clear()
        object.trainers.add(request.user.trainer)

        # Change the trainers list
        if 'trainers' in request.POST:
            try:
                for trainer in request.POST.getlist('trainers'):
                    object.trainers.add(trainer)
            except KeyError:
                pass
        object.save()

        # Clear Course_to_Track m2m bindings and create new ones
        # print("DEL:", Course_to_Track.objects.exclude(course=object, track__in=request.POST.getlist('tracks')))
        Course_to_Track.objects.filter(course=object).exclude(track__in=request.POST.getlist('tracks')).delete()

        for track in request.POST.getlist('tracks'):
            try:
                Course_to_Track.objects.get_or_create(
                    course=object,
                    track=Track.objects.get(id=int(track))
                )
            except (TypeError, ObjectDoesNotExist):
                pass

        return redirect('edit_course', pk=object.id)


    context = get_default_context(request, model, object)
    context.update(
        tracks = tracks,
        additional_trainers = additional_trainers,
        course_type = 'Course',
    )
    return render(request, template_name, context)

@login_required
def edit_offline_course(request, pk):
    model = OfflineCourse
    template_name = 'edit_course.html'
    object = get_one_or_404(model, pk=pk)
    user = request.user
    offline_courses = get_subscribed_offline_courses(user)
    tracks = user.trainer.tracks.all()

    # Change order of sessions
    if request.method == 'POST' and 'sessions' in request.POST:
        sessions = json.loads(request.POST['sessions'])

        for s_id, order in sessions.items():
            session = OfflineSession.objects.get(id=int(s_id))
            if session.course in offline_courses:
                session.order = order
                session.save()

        return HttpResponse("OK")

    elif request.method == 'POST' and 'users' in request.POST:
        users_list = []
        for list_part in request.POST.get('users', '').replace('\n', '').split(','):
            res = re.search(r'["\']?(\w+(?:\s\w+)*?)["\']?\s+<?([\w\._\-+]+@[\w\._\-]+)', list_part)
            try:
                users_list.append(res.groups())
            except: pass
        users_list = set(users_list)
        missing_users = set(list(filter(lambda x: not User.objects.filter(username=x[1][:30]), users_list)))
        for x in missing_users:
            fn, ln = x[0].rsplit(maxsplit=1) if ' ' in x[0] else (x[0], '')
            user = User.objects.create_user(username=x[1][:30], first_name=fn, last_name=ln, email=x[1], password=x[1])
            student = Student.objects.create(email=x[1], name=x[0], user=user)
            student.save()
            student.offline_courses.add(object)
            student.save()
            send_mail(x[1], "Hello, "+fn+"!\n\nThe user in Training Suite has been created for you.\nYour login/password: your Email.")
        existing_users = users_list - missing_users
        for x in existing_users:
            student = User.objects.get(username=x[1][:30]).student
            student.offline_courses.add(object)
            student.save()

    # Update the course
    elif request.method == 'POST' and 'course_name' in request.POST:
        object.name = request.POST['course_name']
        object.active = request.POST.get('course_active', False)

        # Change the start_date
        try:
            object.start_date = datetime.datetime.strptime(request.POST['start_date'], "%d/%m/%Y")
        except (ValueError, KeyError):
            object.start_date = None

        # Change the end_date
        try:
            object.end_date = datetime.datetime.strptime(request.POST['end_date'], "%d/%m/%Y")
        except (ValueError, KeyError):
            object.end_date = None

        object.save()

        # Clear OfflineCourse_to_Track m2m bindings and create new ones
        OfflineCourse_to_Track.objects.filter(offline_course=object).exclude(track__in=request.POST.getlist('tracks')).delete()

        for track in request.POST.getlist('tracks'):
            try:
                OfflineCourse_to_Track.objects.get_or_create(
                    offline_course=object,
                    track=Track.objects.get(id=int(track))
                )
            except (TypeError, ObjectDoesNotExist):
                pass

        return redirect('edit_offline_course', pk=object.id)


    context = get_default_context(request, model, object)
    context.update(
        tracks = tracks,
        course_type='OfflineCourse',
    )
    return render(request, template_name, context)

@login_required
@user_passes_test(lambda user: user.trainer)
def remove_student_from_course(request, course_id, student_id):

    if request.method == "POST" and request.is_ajax():
        student = Student.objects.get(id=int(student_id))
        if request.POST['mode'] == 'Course':
            course = Course.objects.get(id = int(course_id))
            student.courses.remove(course)
        else:
            course = OfflineCourse.objects.get(id = int(course_id))
            student.offline_courses.remove(course)
        student.save()

    return HttpResponse("OK")


@login_required
@user_passes_test(lambda user: user.trainer)
def uncommit_solution(request, pk):
    object = get_one_or_404(Solution, pk=pk)
    object.committed = False
    object.save()
    return redirect('view_solution', pk)


@login_required
def user_settings(request):
    model = Setting
    template_name = 'user_settings.html'
    object = model.objects.get_or_create(user=request.user)
    context = get_default_context(request, model, object)
    return render(request, template_name, context)


@login_required
def run_code(request):
    result = '[]'
    if request.is_ajax():
        code = request.POST.get('code', '')
        if code:
            try:
                runner = Runner.objects.get(pk=int(request.POST.get('runner', 1)))
            except ObjectDoesNotExist:
                return HttpResponse("<strong>Hacking detected! But anyway - wrong runner id passed</strong>")
            body = {
                runner.token_name: runner.token,
                "cmd": code,
            }
            if runner.query_method == 'post':
                r = requests.post(runner.url, data=body)
            elif runner.query_method == 'get':
                r = requests.get(runner.url, data=body)
            else:
                return HttpResponse("Sorry, problem with runner method")
            if r.status_code == 200:
                result = r.text
    return HttpResponse(result)


# NOTIFICATIONS
@login_required
def notifications_mark_all_seen(request):
    # Notification.objects.filter(user=request.user).delete()
    for notification in Notification.objects.filter(user=request.user, seen=False):
        notification.seen = True
        notification.save()

    return redirect(request.GET.get('url', 'root'))


@login_required
def notifications_goto(request, pk):
    '''
    Construct url to see what is Notification about
    '''

    NOTIFICATION_TO_URL_ISPKNEEDED = dict(
        resource=('download', True),
        session=('view_session', True),
        task=('view_task', True),
        solution=('view_solution', True),
        quiz=('quiz:quiz_mode', False),
    )

    notification = get_one_or_404(Notification, pk=pk, user=request.user)
    notification.seen = True
    notification.save()
    if notification.notification_type in NOTIFICATION_TO_URL_ISPKNEEDED:
        if notification.url:
            return redirect(notification.url)
        url, is_pk_needed = NOTIFICATION_TO_URL_ISPKNEEDED[notification.notification_type]
        if is_pk_needed:
            return redirect(url, getattr(notification, notification.notification_type).pk)
        return redirect(url)
    else:
        # Special cases
        #
        if notification.notification_type == 'comment':
            solution = notification.comment.target_solution or notification.comment.target_comment.target_solution
            if solution:
                # TODO: fix mess with COMMENTS!!!!!!
                if hasattr(request.user, "student"):
                    if solution.author == request.user.student:
                        return redirect(reverse('view_task', args=(solution.task.pk,)) + "#review")
                else:
                    return redirect('view_solution', solution.pk)

    return redirect(request.GET.get('url', 'root'))


@login_required
@user_passes_test(lambda user: user.trainer)
def uncommit_solution(request, pk):
    object = get_one_or_404(Solution, pk=pk)
    object.committed = False
    object.save()
    return HttpResponse(
        json.dumps({"result": "OK"}),
        content_type="application/json"
    )


@login_required
@user_passes_test(lambda user: user.trainer)
def fav_solution(request, pk):
    object = get_one_or_404(Solution, pk=pk)
    object.favorited = True
    object.save()
    return HttpResponse(
        json.dumps({"result": "OK"}),
        content_type="application/json"
    )


@login_required
@user_passes_test(lambda user: user.trainer)
def unfav_solution(request, pk):
    object = get_one_or_404(Solution, pk=pk)
    object.favorited = False
    object.save()
    return HttpResponse(
        json.dumps({"result": "OK"}),
        content_type="application/json"
    )


NOTIFICATIONS_MSGS = dict(
    comment="New comment from {author.name} on solution of task '{solution.task.name}'",
    session="New session '{session.name}') is available",
    resource="New resource '{resource.name} ({resource.resource_type})' is available",
    task="Task '{task.name}' is assigned/updated",
    solution="Solution of task '{solution.task.name}' submitted by {solution.author}",
    quiz="Quiz '{quiz.name}' updated/assigned",
    # general=("New notification", tuple()),
)

@receiver(post_save)
def signals_handler(instance, sender, **kwargs):
    if sender == Comment:
        if instance.target_comment:
            # Should notify author of the comment
            receiver_ = instance.target_comment.author
        else:
            # Should notify author of the solution
            receiver_ = instance.target_solution.author
        solution = instance.target_solution or instance.target_comment.target_solution
        if hasattr(instance.author.user, "student"):
            author = instance.author.user.student
        else:
            author = instance.author.user.trainer

        # message_template, message_payload = NOTIFICATIONS_MSGS['comment']
        message_template = NOTIFICATIONS_MSGS['comment']
        message = message_template.format(solution=solution, instance=instance, author=author)
        if author != receiver_:
            if not Notification.objects.filter(
                    user=receiver_.user, comment=instance, notification_type="comment", content=message):
                Notification.objects.create(
                    user=receiver_.user, comment=instance, notification_type="comment", content=message)
    elif sender == Solution:
        if instance.committed:
            message_template = NOTIFICATIONS_MSGS['solution']
            author = instance.author
            courses = {session.course for session in instance.task.sessions.all()}
            receivers = set(Trainer.objects.filter(courses__in=courses))
            for receiver_ in receivers:
                message = message_template.format(solution=instance, author=author)
                if author != receiver_:
                    if not Notification.objects.filter(
                            user=receiver_.user, solution=instance, notification_type="solution", content=message):
                        Notification.objects.create(
                            user=receiver_.user, solution=instance, notification_type="solution", content=message)
    elif sender == Session:
        message_template = NOTIFICATIONS_MSGS['session']
        receivers = set(Student.objects.filter(courses=instance.course))
        for receiver_ in receivers:
            message = message_template.format(session=instance)
            if not Notification.objects.filter(
                    user=receiver_.user, session=instance, notification_type="session", content=message):
                Notification.objects.create(
                    user=receiver_.user, session=instance, notification_type="session", content=message)
    elif sender == Quiz:
        if isinstance(instance, Quiz):
            courses = instance.course.all()
            receivers = Student.objects.filter(courses__in=courses)
            message = NOTIFICATIONS_MSGS['quiz'].format(quiz=instance)
            url = reverse('quiz:quiz_mode', kwargs={'quiz_id': instance.pk})
            for receiver_ in receivers:
                Notification.objects.get_or_create(user=receiver_.user, notification_type="quiz",
                                                   content=message, url=url)


@receiver(m2m_changed)
def signals_handler_m2m(sender, instance, **kwargs):
    if sender == Resource.sessions.through:
        if isinstance(instance, Resource):
            message_template = NOTIFICATIONS_MSGS['resource']
            courses = set(session.course for session in instance.sessions.all())
            receivers = Student.objects.filter(courses__in=courses)
            message = message_template.format(resource=instance)
            # print(receivers, message)
            for receiver_ in receivers:
                if not Notification.objects.filter(
                        user=receiver_.user, resource=instance, notification_type="resource", content=message):
                    Notification.objects.create(
                        user=receiver_.user, resource=instance, notification_type="resource", content=message)

    elif sender == Task.sessions.through:
        if isinstance(instance, Task):
            message_template = NOTIFICATIONS_MSGS['task']
            courses = set(session.course for session in instance.sessions.all())
            updated_students = [x.author for x in Solution.objects.filter(task=instance)]
            receivers = [student for student in Student.objects.filter(courses__in=courses) if student not in updated_students]
            message = message_template.format(task=instance)
            # print(receivers, message)
            for receiver_ in receivers:
                if not Notification.objects.filter(
                        user=receiver_.user, task=instance, notification_type="task", content=message):
                    Notification.objects.create(
                        user=receiver_.user, task=instance, notification_type="task", content=message)
    elif sender == Quiz.course.through:
        if isinstance(instance, Quiz):
            courses = instance.course.all()
            receivers = Student.objects.filter(courses__in=courses)
            message = NOTIFICATIONS_MSGS['quiz'].format(quiz=instance)
            url = reverse('quiz:quiz_mode', kwargs={'quiz_id': instance.pk})
            # print(receivers, message)
            for receiver_ in receivers:
                Notification.objects.get_or_create(user=receiver_.user, notification_type="quiz",
                                                   content=message, url=url)


@login_required
def search_results(request):
    template_name = 'search_results.html'
    context = get_default_context(request, None, None, None)
    available_courses = get_subscribed_courses(request.user)
    sorted_available_tasks = []
    sorted_sessions = []
    sorted_discussions = []
    query = ''

    if request.method == 'GET' and request.GET.get('q', None):
        query = request.GET['q']
        key_words = query.split()   # Splitted search request for multiple words
        sessions = []
        tasks = []
        discussions = []

        for word in key_words:
            # Adds objects to the final list from queryset for the search word present in session's description
            # or name
            sessions.extend(Session.objects.filter(course__in=available_courses).filter(
                Q(name__icontains=word) |
                Q(description__icontains=word)
            ))

            tasks.extend(Task.objects.filter(
                Q(name__icontains=word) |
                Q(content__icontains=word)
            ))

            discussions.extend(DiscussionThread.objects.filter(
                Q(subject__icontains = word) |
                Q(content__icontains = word)
            ))

        available_tasks = []
        for task in tasks:
            for session in task.sessions.all():
                if session.course in available_courses:
                    available_tasks.append(task)

        # Adds objects after Counter() counts how many times object is present in the list (how many words
        # from the search query are in the object) and .most_common() sorts based on the Counter() count
        sorted_sessions = list(set([key[0] for key in Counter(sessions).most_common()]))

        sorted_available_tasks = [key[0] for key in Counter(available_tasks).most_common()]

        sorted_discussions = [key[0] for key in Counter(discussions).most_common()]

    context.update(
        tasks=sorted_available_tasks,
        sessions=sorted_sessions,
        discussions=sorted_discussions,
        query=query,
    )

    return render(request, template_name, context)

@login_required
@user_passes_test(lambda user: user.trainer)
def create_session(request, pk):
    model = Course
    template_name = 'update_session.html'
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object, None)

    # Calculate appropriate session order
    try:
        session_order = Session.objects.filter(course=object).last().order + 1
    except (ObjectDoesNotExist, AttributeError):
        session_order = 1

    slides = list(get_available_assets(object.tracks.all(), Slideshow))
    resources = list(get_available_assets(object.tracks.all(), Resource))
    tasks = list(get_available_assets(object.tracks.all(), Task))

    if request.method == "POST":

        session = Session.objects.create(
            order = session_order,
            course = object,
            name = request.POST['name'],
            description = request.POST['description'],
        )

        try:
            session.start_time = datetime.datetime.strptime(request.POST['start_time'] + " +0200", "%d/%m/%Y %H:%M %z")
        except (ValueError, KeyError):
            session.start_time = None
        session.save()

        for task_id in map(int, request.POST.getlist('tasks', [])):
            task = Task.objects.get(id=task_id)
            task.sessions.add(session)
            task.save()

        for slide_id in map(int, request.POST.getlist('slides', [])):
            slide = Slideshow.objects.get(id=slide_id)
            Slides_to_Sessions.objects.create(slideshow=slide, session=session)

        for resource_id in map(int, request.POST.getlist('resources', [])):
            resource = Resource.objects.get(id=resource_id)
            resource.sessions.add(session)
            resource.save()

        return redirect('view_session', pk=session.id)

    context.update(
        course = object,
        resources = resources,
        tasks = tasks,
        slides = slides,
        mode = "create_session",
    )

    return render(request, template_name, context)

@login_required
@user_passes_test(lambda user: user.trainer)
def update_session(request, pk):
    model = Session
    template_name = 'update_session.html'
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object)

    slides = list(get_available_assets(object.course.tracks.all(), Slideshow))
    resources = list(get_available_assets(object.course.tracks.all(), Resource))
    tasks = list(get_available_assets(object.course.tracks.all(), Task))
    chosen_slides = object.slides.all()
    chosen_tasks = object.task_set.all()
    chosen_resources = object.resource_set.all()

    if request.method == "POST":
        # Update name and description
        object.name = request.POST['name']
        object.description = request.POST['description']

        # Clear all m2m bindings
        Slides_to_Sessions.objects.filter(session=object).delete()
        object.resource_set.clear()  # TODO: M2M 3
        object.task_set.clear()  # TODO: M2M 3

        # object.start_time
        try:
            object.start_time = datetime.datetime.strptime(request.POST['start_time'] + " +0200", "%d/%m/%Y %H:%M %z")
        except (ValueError, KeyError):
            object.start_time = None

        object.save()


        # Add new m2m bindings
        for task_id in map(int, request.POST.getlist('tasks', [])):
            task = Task.objects.get(id=task_id)
            task.sessions.add(object)  # TODO: M2M 3
            task.save()

        for slide_id in map(int, request.POST.getlist('slides', [])):
            slide = Slideshow.objects.get(id=slide_id)
            Slides_to_Sessions.objects.create(slideshow=slide, session=object)

        for resource_id in map(int, request.POST.getlist('resources', [])):
            resource = Resource.objects.get(id=resource_id)
            resource.sessions.add(object)  # TODO: M2M 3
            resource.save()

        return redirect('view_session', pk=object.id)


    context.update(
        slides = slides,
        resources = resources,
        tasks = tasks,
        chosen_slides = chosen_slides,
        chosen_tasks = chosen_tasks,
        chosen_resources = chosen_resources,
        mode = "update_session",
    )

    return render(request, template_name, context)

@login_required
@user_passes_test(lambda user: user.trainer)
def create_offline_session(request, pk):
    model = OfflineCourse
    template_name = 'update_session.html'
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object, None)

    # Calculate appropriate session order
    try:
        session_order = OfflineSession.objects.filter(course=object).last().order + 1
    except (ObjectDoesNotExist, AttributeError):
        session_order = 1

    slides = list(get_available_assets(object.tracks.all(), Slideshow))
    resources = list(get_available_assets(object.tracks.all(), Resource))
    tasks = list(get_available_assets(object.tracks.all(), Task))
    quizes = Quiz.objects.filter(tracks__in=object.tracks.all())

    if request.method == "POST":

        session = OfflineSession.objects.create(
            order = session_order,
            course = object,
            name = request.POST['name'],
            description = request.POST['description'],
        )

        try:
            session.quiz = Quiz.objects.get(pk=int(request.POST['quiz']))
        except ObjectDoesNotExist:
            session.quiz = None
        session.save()

        for task_id in map(int, request.POST.getlist('tasks', [])):
            task = Task.objects.get(id=task_id)
            Task_to_OfflineSession.objects.create(task=task, session=session)

        for slide_id in map(int, request.POST.getlist('slides', [])):
            slide = Slideshow.objects.get(id=slide_id)
            Slideshow_to_OfflineSession.objects.create(slideshow=slide, session=session)

        for resource_id in map(int, request.POST.getlist('resources', [])):
            resource = Resource.objects.get(id=resource_id)
            Resource_to_OfflineSession.objects.create(resource=resource, session=session)

        return redirect('view_offline_session', pk=session.id)

    context.update(
        course = object,
        resources = resources,
        tasks = tasks,
        slides = slides,
        mode = "create_session",
        quizes = quizes,
    )

    return render(request, template_name, context)

@login_required
@user_passes_test(lambda user: user.trainer)
def edit_offline_session(request, pk):
    model = OfflineSession
    template_name = 'update_session.html'
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object)

    slides = list(get_available_assets(object.course.tracks.all(), Slideshow))
    resources = list(get_available_assets(object.course.tracks.all(), Resource))
    tasks = list(get_available_assets(object.course.tracks.all(), Task))
    chosen_slides = object.slides.all()
    chosen_tasks = object.tasks.all()
    chosen_resources = object.resources.all()
    quizes = Quiz.objects.filter(tracks__in=object.course.tracks.all())


    if request.method == "POST":
        # Update name and description
        object.name = request.POST['name']
        object.description = request.POST['description']

        # object.quiz
        try:
            object.quiz = Quiz.objects.get(pk=int(request.POST['quiz']))
        except ObjectDoesNotExist:
            object.quiz = None


        # is_required?
        try:
            object.required = request.POST['session_required']
        except KeyError:
            object.required = False

        object.save()

        # Remove unchecked m2m connections and add missing ones

        Task_to_OfflineSession.objects.filter(session=object).exclude(task__in=request.POST.getlist('tasks')).delete()
        for task_id in map(int, request.POST.getlist('tasks', [])):
            try:
                Task_to_OfflineSession.objects.get_or_create(
                    session = object,
                    task = Task.objects.get(id=task_id)
                )
            except (TypeError, ObjectDoesNotExist):
                pass

        Slideshow_to_OfflineSession.objects.filter(session=object).exclude(slideshow__in=request.POST.getlist('slides')).delete()
        for slide_id in map(int, request.POST.getlist('slides', [])):
            try:
                Slideshow_to_OfflineSession.objects.get_or_create(
                    session = object,
                    slideshow = Slideshow.objects.get(id=slide_id)
                )
            except (TypeError, ObjectDoesNotExist):
                pass

        Resource_to_OfflineSession.objects.filter(session=object).exclude(resource__in=request.POST.getlist('resources')).delete()
        for resource_id in map(int, request.POST.getlist('resources', [])):
            try:
                Resource_to_OfflineSession.objects.get_or_create(
                    session = object,
                    resource = Resource.objects.get(id=resource_id)
                )
            except (TypeError, ObjectDoesNotExist):
                pass

        return redirect('view_offline_session', pk=object.id)


    context.update(
        slides = slides,
        resources = resources,
        tasks = tasks,
        chosen_slides = chosen_slides,
        chosen_resources = chosen_resources,
        chosen_tasks = chosen_tasks,
        quizes = quizes,
        mode = "update_session",
    )

    return render(request, template_name, context)

@login_required
def view_offline_session(request, pk):
    model = OfflineSession
    template_name = 'session_detail.html'
    object = get_one_or_404(model, pk=pk)
    context = get_default_context(request, model, object)

    chosen_slides = set(object.slides.all())
    chosen_tasks = set(object.tasks.all())
    chosen_resources = set(object.resources.all())

    context.update(
        chosen_resources = chosen_resources,
        chosen_tasks = chosen_tasks,
        chosen_slides = chosen_slides,
    )

    return render(request, template_name, context)


@login_required
def update_attendance(request, session_id):
    try:
        trainer = request.user.trainer
        session = get_object_or_404(Session, pk=int(session_id))
        if not session.course in trainer.course_set.all() or request.method != "POST":
            return redirect('root')

        attended_student_ids = map(int, request.POST.getlist('attendances[]'))

        # Looking for attendances to delete:
        Attendance.objects.filter(session=session).exclude(student__pk__in=attended_student_ids).delete()

        for student in [get_object_or_404(Student, pk=student_id) for student_id in attended_student_ids]:
            Attendance.objects.get_or_create(session=session, student=student)

        return HttpResponse("OK")
    except (ObjectDoesNotExist, AttributeError):
        return HttpResponse("FAILED")


@threaded
def send_mail(sender_list, message):
    recipients = []
    if isinstance(sender_list, str):
        recipients.append(sender_list)
    elif isinstance(sender_list, list):
        for recipient in sender_list:
            recipients.append(recipient)
    return requests.post(
        EMAIL_HOST_URL,
        auth=("api", EMAIL_HOST_API_KEY),
        data={"from": EMAIL_HOST_USER,
            "to": recipients,
            "subject": EMAIL_HOST_SUBJECT,
            "text": message})

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@ REST @@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


