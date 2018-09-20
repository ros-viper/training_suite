from django.conf.urls import url

from . import views

app_name = 'discussions'
urlpatterns = [
    # ex: /discussions/
    url(r'^$', views.list_threads, name='list_threads'),
    url(r'^(?P<discussionthread_id>[0-9]+)/$', views.thread_detail, name='thread_detail'),
    # url(r'^(?P<discussionthread_id>[0-9]+)/?page=(?P<page>\d+)$', views.thread_detail, name='thread_detail_page'),
    url(r'^([0-9]+)/delete/(?P<message_id>[0-9]+)/$', views.delete_message, name='delete_message'),
    url(r'^user/([0-9]+)/$', views.user_detail, name='user_detail'),
]