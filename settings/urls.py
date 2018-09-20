from django.conf.urls import url
from .views import settings_view, edit_settings_view


urlpatterns = [url(r'^(?i)edit_(?P<settings_type>[\w_]+)/$', edit_settings_view, name='edit_settings_view'),
               url(r'^(?i)(?P<settings_type>[\w_]+)/$', settings_view, name='settings_view'),
                ]
