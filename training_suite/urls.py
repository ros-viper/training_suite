"""training_suite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from TrainingSuite.views import *


def required(wrapping_functions,patterns_rslt):
    '''
    Used to require 1..n decorators in any view returned by a url tree

    Usage:
      urlpatterns = required(func,patterns(...))
      urlpatterns = required((func,func,func),patterns(...))

    Note:
      Use functools.partial to pass keyword params to the required
      decorators. If you need to pass args you will have to write a
      wrapper function.

    Example:
      from functools import partial

      urlpatterns = required(
          partial(login_required,login_url='/accounts/login/'),
          patterns(...)
      )
    '''
    if not hasattr(wrapping_functions,'__iter__'):
        wrapping_functions = (wrapping_functions,)

    return [
        _wrap_instance__resolve(wrapping_functions, instance)
        for instance in patterns_rslt
    ]

def _wrap_instance__resolve(wrapping_functions,instance):
    if not hasattr(instance,'resolve'): return instance
    resolve = getattr(instance,'resolve')

    def _wrap_func_in_returned_resolver_match(*args,**kwargs):
        rslt = resolve(*args,**kwargs)

        if not hasattr(rslt,'func'):return rslt
        f = getattr(rslt,'func')

        for _f in reversed(wrapping_functions):
            # @decorate the function from inner to outter
            f = _f(f)

        setattr(rslt,'func',f)

        return rslt

    setattr(instance,'resolve',_wrap_func_in_returned_resolver_match)

    return instance

urlpatterns = [
    url('^', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^$', list_courses, name="root"),
    url(r'^courses/?$', list_courses, name="list_courses"),
    url(r'^resources/?$', list_resources, name="list_resources"),
    url(r'^slides/?$', list_slides, name="list_slides"),
    url(r'^hometasks/?$', list_hometasks, name="list_hometasks"),
    url(r'^reviews/?$', list_solutions, name="reviews"),
    url(r'^course/(?P<pk>\d+)/?$', view_course, name="view_course"),
    url(r'^offline_course/(?P<pk>\d+)/?$', view_offline_course, name="view_offline_course"),
    url(r'^session/(?P<pk>\d+)/?$', view_session, name="view_session"),
    url(r'^offline_session/(?P<pk>\d+)/?$', view_offline_session, name="view_offline_session"),
    url(r'^task/(?P<pk>\d+)/?$', view_task, name="view_task"),
    url(r'^comment/reply/(?P<pk>\d+)/?$', comment_reply, name="comment_reply"),
    url(r'^download/(?P<pk>\d+)/?$', download_resource, name="download"),
    url(r'^trainer/solutions/(?P<pk>\d+)/?$', view_solutions, name="view_solutions"),
    url(r'^trainer/course/(?P<pk>\d+)/?$', edit_course, name="edit_course"),
    url(r'^trainer/offline_course/(?P<pk>\d+)/?$', edit_offline_course, name="edit_offline_course"),
    url(r'^trainer/solution/(?P<pk>\d+)/?$', view_solution, name="view_solution"),
    url(r'^trainer/solution/fav(?P<pk>\d+)/?$', fav_solution, name="fav_solution"),
    url(r'^trainer/solution/unfav(?P<pk>\d+)/?$', unfav_solution, name="unfav_solution"),
    url(r'^trainer/uncommit/(?P<pk>\d+)/?$', uncommit_solution, name="uncommit"),
    url(r'^user_settings/?$', user_settings, name="user_settings"),
    url(r'^notif_all_seen/?$', notifications_mark_all_seen, name="notifications_mark_all_seen"),
    url(r'^notif_go/(?P<pk>\d+)/?$', notifications_goto, name="notifications_goto"),
    url(r'^search/?$', search_results, name="search_results"),
    url(r'^create_session/(?P<pk>\d+)/?$', create_session, name="create_session"),
    url(r'^create_offline_session/(?P<pk>\d+)/?$', create_offline_session, name="create_offline_session"),
    url(r'^update_session/(?P<pk>\d+)/?$', update_session, name="update_session"),
    url(r'^update_attendance/(?P<session_id>\d+)/?$', update_attendance, name="update_attendance"),
    url(r'^edit_offline_session/(?P<pk>\d+)/?$', edit_offline_session, name="edit_offline_session"),
    url(r'^trainer/course/(?P<course_id>\d+)/student/(?P<student_id>\d+)/?$', remove_student_from_course, name="delete_student"),
    url(r'^trainer/offline_course/(?P<course_id>\d+)/student/(?P<student_id>\d+)/?$', remove_student_from_course, name="delete_student_off"),

    url(r'^run_code/?', run_code, name="run_code"),


    # url(r'^passchange/?$', password_change, name='password_change'),
    # url(r'^/accounts/password/reset/$', password_reset, {'template_name': 'my_templates/password_reset.html'}))

    url(r'^summernote/', include('django_summernote.urls')),
    url(r'^markdownx/', include('markdownx.urls')),
    url(r'^quiz/', include('quiz.urls')),
    url(r'^polls/', include('polls.urls')),
    url(r'^discussions/', include('discussions.urls')),

    # SETTINGS
    url (r'^settings/', include('settings.urls')),
]

urlpatterns = required(handle_404, urlpatterns)