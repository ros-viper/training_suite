from django.db import models

from TrainingSuite.models import Course, Student


class Poll(models.Model):
    name = models.CharField(max_length=500, null=False, blank=False)
    course = models.ManyToManyField(Course)
    deadline = models.DateField(blank=True, null=True)
    deadline_active = models.BooleanField(default=False)
    verbose_results_enabled = models.BooleanField(default=True)

    @property
    def submitted_results(self):
        return self.submittedresult_set.count()

    def __str__(self):
        return "Poll: '%s'" % self.name


class Question(models.Model):
    content = models.CharField(max_length=1000, null=False, blank=False)
    poll = models.ForeignKey('Poll')
    has_user_option = models.BooleanField(default=False)
    has_multiple_options = models.BooleanField(default=False)

    def __str__(self):
        return "Q: '%s' of poll '%s'" % (self.content[:30], self.poll.name)

    class Meta:
        ordering = ['pk']


class Option(models.Model):
    question = models.ForeignKey('Question')
    content = models.CharField(max_length=1500, null=False, blank=False)
    votes = models.IntegerField(default=0)  # Cached number of votes

    def __str__(self):
        return "A: '%s'" % (self.content[:30])

    class Meta:
        ordering = ['pk']


class UserOption(models.Model):
    question = models.ForeignKey('Question')
    content = models.CharField(max_length=3000, null=True, blank=True)
    student = models.ForeignKey(Student)
    
    def __str__(self):
        return "A: '%s'" % (self.content[:30])


class SubmittedResult(models.Model):
    poll = models.ForeignKey('Poll')
    options = models.ManyToManyField('Option', blank=True)
    user_options = models.ManyToManyField('UserOption', blank=True)
    student = models.ForeignKey(Student, related_name="submitted_polls")
    date_submitted = models.DateField(auto_now_add=True, blank=False, null=False)
