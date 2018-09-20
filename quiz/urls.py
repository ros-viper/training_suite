from django.conf.urls import url

from . import views

app_name = 'quiz'
urlpatterns = [
    # ex: /quiz/
    url(r'^$', views.list_quizes, name='list_quizes'),
    url(r'^(?P<quiz_id>[0-9]+)/$', views.quiz_mode, name='quiz_mode'),
    url(r'^submittedresult/(?P<submittedresult_id>[0-9]+)/$', views.quiz_result, name='submitted_result'),
    url(r'^retry/(?P<submittedresult_id>[0-9]+)/$', views.quiz_retry, name='quiz_retry'),
]