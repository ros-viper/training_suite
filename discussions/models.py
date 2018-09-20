from django.db import models

from django.contrib.auth.models import User
from TrainingSuite.models import Session, Course

# Create your models here.

class DiscussionThread(models.Model):
    subject = models.TextField(max_length=200)
    content = models.TextField(max_length=5000, default='')
    author = models.ForeignKey(User, blank=False)
    session = models.ForeignKey(Session, blank=True, null=True)
    course = models.ForeignKey(Course, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    
    def __str__(self):
        return "'%s'...: '%s'" % (self.subject[:20], self.author)
    
class DiscussionMessage(models.Model):
    thread = models.ForeignKey(DiscussionThread, blank=False)
    content = models.TextField(max_length=5000, null=False, blank=False)
    author = models.ForeignKey(User, blank=False)
    date_added = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    quote = models.TextField(max_length=5000, default='')
    
    def __str__(self):
        return "Thread: '%s'; Author: '%s'; Target: '%s'" % (self.thread, self.author, self.quote)