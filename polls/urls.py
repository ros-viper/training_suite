from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /polls/
    url(r'^$', views.polls_list, name='polls_list'),
    url(r'^([0-9]+)/?$', views.poll_mode, name='poll_mode'),
    url(r'^([0-9]+)/results/?$', views.poll_results, name='poll_results'),
]