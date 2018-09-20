from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth.models import User

from quiz.models import Quiz


class PersonNotFound(Exception):
    """
    Exception telling that student or trainer related to User is not found
    """
    def __init__(self, *args):
        self.msg = "There is no Person associated" + " with User <{}>".format(args.pop()) if len(args) else ""


class Person(models.Model):
    def get_is_trainer(self=None):
        if self and isinstance(self.__class__, Trainer):
            return True
        return False

    class Meta:
        abstract = True

    name = models.CharField(max_length=100, blank=False)
    email = models.EmailField(max_length=100, blank=False, unique=True)
    courses = models.ManyToManyField('Course', blank=True)
    offline_courses = models.ManyToManyField('OfflineCourse', blank=True)
    comments = models.ManyToManyField('Comment', blank=True)
    is_trainer = models.BooleanField(default=get_is_trainer)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def is_subscribed(self, course):
        """
        Check is this person subscribed to the course

        :param course: Course object
        :return: True/False
        """
        if isinstance(course, Course):
            return course in self.courses.all()
        elif isinstance(course, OfflineCourse):
            return course in self.offline_courses.all()

    def __str__(self):
        data = dict(
            who="Trainer" if self.is_trainer else "Student",
            name=self.name,
            email=self.email
        )
        return "{who} {name}({email})".format(**data)


class Trainer(Person):
    pass


class Student(Person):
    pass


class Course(models.Model):
    name = models.CharField(max_length=100, blank=False, unique=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    trainers = models.ManyToManyField('Trainer')
    tracks = models.ManyToManyField('Track', through='Course_to_Track', related_name='tracks')

    active = models.BooleanField(default=False)

    def get_is_subscribed_and_role(self, user):
        """
        Check if user subscribed to this course

        :param user: Django Auth User object
        :return: True/False, Role (string)
        """
        if not (user.student or user.trainer):
            raise PersonNotFound(user)

        if user.trainer and user.trainer.is_subscribed(self):
            return True, "Trainer"
        elif user.student and user.student.is_subscribed(self):
            return True, "Student"
        else:
            return False, ""

    @property
    def is_offline(self):
        return False

    def __str__(self):
        trainers_plural = ''
        if self.trainers.count() == 1:
            trainers_str = self.trainers.first()
        elif self.trainers.count() == 0:
            trainers_str = ''
        else:
            trainers_str = ",".join([x.name for x in self.trainers.all()])
            trainers_plural = 's'

        data = dict(
            name=self.name,
            tr=trainers_str,
            _s=trainers_plural
        )
        return "Course {name}, trainer{_s}: {tr}".format(**data)

    class Meta:
        ordering = ('start_date', )

class Course_to_Track(models.Model):
    course = models.ForeignKey('Course')
    track = models.ForeignKey('Track')


class Session(models.Model):
    order = models.IntegerField(blank=False)
    name = models.CharField(blank=False, max_length=300, default="")
    description = models.TextField(blank=False, max_length=3000, default="")
    course = models.ForeignKey('Course')
    start_time = models.DateTimeField(blank=True, null=True)

    @property
    def is_offline(self):
        return False

    def __str__(self):
        data = dict(
            order=self.order,
            descr="(%s)" % self.name if self.name else "",
            course=self.course.name
        )
        return "Session {order}{descr} of course {course}".format(**data)

    class Meta:
        unique_together = ("order", "course")
        ordering = ["order", "course"]


class Slideshow(models.Model):
    path = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=100)
    comment = models.CharField(max_length=100, blank=True)
    sessions = models.ManyToManyField('Session', through='Slides_to_Sessions', related_name='slides', blank=True)
    courses = models.ManyToManyField('Course', blank=True)
    order = models.IntegerField(default=0)
    track = models.ForeignKey('Track', null=True)

    def __str__(self):
        return "Slides '{}'".format(self.name)

    class Meta:
        ordering = ('order',)


class Slides_to_Sessions(models.Model):
    slideshow = models.ForeignKey('Slideshow')
    session = models.ForeignKey('Session')


class Comment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(max_length=300, blank=False)
    target_line = models.IntegerField(default=-1, help_text="Target line, -1 for OVERALL comment")
    target_solution = models.ForeignKey('Solution', null=True, blank=True)
    target_comment = models.ForeignKey('Comment', null=True, blank=True)
    author_trainer = models.ForeignKey('Trainer', null=True, blank=True)
    author_student = models.ForeignKey('Student', blank=True, null=True)

    @property
    def author(self):
        """Get author of the comment"""
        return self.author_trainer if self.author_trainer else self.author_student

    class Meta:
        ordering = ['target_line', 'created_at', 'author_trainer', 'author_student']

    @property
    def is_by_trainer(self):
        """Is this comment made by trainer"""
        return True if self.author_trainer else False

    def __str__(self):
        if self.target_comment:
            comment_type = 'comment'
            if self.target_comment.author_student:
                target_author = self.target_comment.author_student
            else:
                target_author = self.target_comment.author_trainer
        else:
            comment_type = 'solution'
            target_author = self.target_solution.author
        if self.author_student is not None:
            author = self.author_student
        else:
            author = self.author_trainer

        data = dict(
            author=author,
            comment_type = comment_type,
            target_author = target_author,
        )
        # return "Comment of {author} on {solution_author}'s solution of '{task}' of session {session}".format(**data)
        return "Comment of {author} on {comment_type} of {target_author}".format(**data)


class Solution(models.Model):
    author = models.ForeignKey('Student')
    task = models.ForeignKey('Task')
    content = models.TextField(max_length=3000)
    committed = models.BooleanField(default=False)
    favorited = models.BooleanField(default=False)
    committed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        data = dict(
            author=self.author.name,
            task=self.task.name,
        )
        return "Solution of '{task}' by {author}".format(**data)


class Task(models.Model):
    DEFAULT_SOLUTION = '''def test_me(*args, **kwargs):
    print("Hello World")
    return True
'''

    # number = models.IntegerField(blank=False)
    name = models.CharField(max_length=100, default="Home Task", unique=True)
    sessions = models.ManyToManyField('Session')
    content = models.TextField(max_length=3000, blank=False)
    default_solution = models.TextField(max_length=1000, default=DEFAULT_SOLUTION)
    track = models.ForeignKey('Track', null=True)
    runner = models.ForeignKey('Runner')

    def is_solved_by(self, user):
        """
        Is it solved by current user? Checking only students

        :param user: Django user
        :return: True/False
        """
        try:
            return user.student.solution_set.filter(task=self).count() == 1
        except ObjectDoesNotExist:
            # TODO: Handle properly
            return False
            
    @property
    def courses(self):
        return list(set([s.course for s in self.sessions.all()]))

    class Meta:
        ordering = ["pk"]
        # unique_together = ("number", "session")

    def __str__(self):
        data = dict(
            task=self.name,
        )
        return "Hometask '{task}'".format(**data)


class Resource(models.Model):
    RESOURCE_TYPES = (
        ('PDF', 'PDF file'),
        ('DOC', 'Word document'),
        ('PPT', 'Powerpoint presentation'),
        ('EBOOK', 'Ebook file'),
        ('URL', 'Link to resource in Web'),
        ('ZIP', 'Zipped data'),
    )

    def get_resource_path(self, filename):
        return 'resources/course_{}/session_{}__{}'.format(
            self.sessions.first().course.start_date,
            self.sessions.first().order,
            filename
        )

    resource_type = models.CharField(max_length=5, choices=RESOURCE_TYPES, blank=True)
    physical_location = models.CharField(max_length=200, blank=True, null=True)
    # physical_location = models.FileField(upload_to=get_resource_path, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=100)
    comment = models.CharField(max_length=100, blank=True)
    sessions = models.ManyToManyField('Session')
    track = models.ForeignKey('Track', null=True)

    class Meta:
        ordering = ['sessions__order']

    def __str__(self):
        return "Resource '{}'".format(self.name)


class Setting(models.Model):
    """
    Table to keep all needed user settings
    - New fields are to be added via migrate to save Heroku DB space
    """
    user = models.OneToOneField(User, blank=False, null=False, unique=True)
    setting_send_email_new_resource = models.BooleanField(default=False)
    setting_send_email_new_comment = models.BooleanField(default=False)

    def __str__(self):
        return "Settings for {}".format(self.user.email)

class Notification(models.Model):
    """
    Table to keep all pending notifications for User for the following events:

    * custom message (global notification)
    * new comment added to solution
    * new discussion thread
    * new message in discussion

    user / student:
    * new session available
    * new resource available
    * new task available

    user / trainer:
    * new Solution from Student
    """

    NOTIFICATION_TYPES = (
        ('session', "New session is available"),
        ('resource', "New resource is available"),
        ('task', "Task is assigned/updated"),
        ('comment', "New reply on solution"),
        ('solution', "New solution submitted"),
        ('quiz', "Quiz is updated/assigned"),
        ('discussion_thread', "New discussion started"),
        ('discussion_update', "New message in discussion"),
        ('general', "Notification"),
    )

    user = models.ForeignKey(User)
    seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=200, default="")
    url = models.CharField(max_length=200, default="")
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default="general")
    
    # Links to related objects
    resource = models.ForeignKey('Resource', blank=True, null=True)
    session = models.ForeignKey('Session', blank=True, null=True)
    task = models.ForeignKey('Task', blank=True, null=True)
    comment = models.ForeignKey('Comment', blank=True, null=True)
    solution = models.ForeignKey('Solution', blank=True, null=True)
    #discussion_thread = models.ForeignKey('DiscussionThread', blank=True, null=True)
    #discussion_update = models.ForeignKey('DiscussionMessage', blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def message(self):
        """
        Get needed message to display for notification
        """ 
        if self.content != '':
            return self.content
        else:
            return self.get_notification_type_display()

    def __str__(self):
        data = dict(
            user = self.user.email,
            n_type = self.notification_type.title(),
            dt = str(self.created_at),
            seen = "seen" if self.seen else "unseen",
        )
        return "Notification about {n_type} for {user} ({dt}, {seen})".format(**data)

class Track(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False)
    short_name = models.CharField(max_length=20, unique=True, null=False)
    color = models.CharField(max_length=50, default="grey", unique=True, null=False)
    trainers = models.ManyToManyField('Trainer', through='Track_to_Trainer', related_name='tracks')

    def __str__(self):
        return "Track '{}'('{}')".format(self.name, self.short_name)

class Track_to_Trainer(models.Model):
    track = models.ForeignKey('Track')
    trainer = models.ForeignKey('Trainer')

# Offline course
class OfflineCourse(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False)
    description = models.TextField(max_length=3000)
    author = models.ForeignKey('Trainer', blank=False, null=False)
    tracks = models.ManyToManyField('Track', through='OfflineCourse_to_Track', related_name='offline_courses')
    active = models.BooleanField(default = False)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    @property
    def is_offline(self):
        return True


    def __str__(self):
        return "Offline course: '{}'".format(self.name)

class OfflineCourse_to_Track(models.Model):
    offline_course = models.ForeignKey('OfflineCourse')
    track = models.ForeignKey('Track')

class OfflineSession(models.Model):
    name = models.CharField(max_length=100, null=False)
    order = models.IntegerField(blank=False)
    description = models.TextField(max_length=3000, blank=False, default="")
    course = models.ForeignKey('OfflineCourse')
    required = models.BooleanField(default=True)
    quiz = models.ForeignKey(Quiz, blank=True, null=True, related_name='offline_sessions')
    slides = models.ManyToManyField('Slideshow', through='Slideshow_to_OfflineSession', related_name='offline_sessions')
    tasks = models.ManyToManyField('Task', through='Task_to_OfflineSession', related_name='offline_sessions')
    resources = models.ManyToManyField('Resource', through='Resource_to_OfflineSession', related_name='offline_sessions')


    class Meta:
        unique_together = ('course', 'name', 'order')
        ordering = ['order']

    @property
    def is_offline(self):
        return True

    def __str__(self):
        data = dict(
            order=self.order,
            name="(%s)" % self.name,
            course=self.course.name
        )
        return "Session {order}{name} of course {course}".format(**data)

class Resource_to_OfflineSession(models.Model):
    session = models.ForeignKey('OfflineSession')
    resource = models.ForeignKey('Resource')

class Task_to_OfflineSession(models.Model):
    session = models.ForeignKey('OfflineSession')
    task = models.ForeignKey('Task')

class Slideshow_to_OfflineSession(models.Model):
    session = models.ForeignKey('OfflineSession')
    slideshow = models.ForeignKey('Slideshow')

class OfflineCourseResults(models.Model):
    student = models.ForeignKey('Student', blank=False, null=False)
    course = models.ForeignKey('OfflineCourse', blank=False, null=False)
    passed = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True)
    results = models.TextField(max_length=1000, blank=True, null=True)
    current_session = models.ForeignKey('OfflineSession', blank=True, null=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        data = dict(
            course=course,
            student=student
        )
        return "Results for offline {course} of {student}".format(**data)

class Runner(models.Model):
    tracks = models.ManyToManyField('Track', through='Runner_to_Track', related_name='runners')
    name = models.CharField(max_length=200, unique=True)
    token = models.CharField(max_length=200, null=Track, blank=True, default='')
    token_name = models.CharField(max_length=50, default='API_TOKEN')
    url = models.CharField(max_length=200, null=False, blank=False)
    query_method = models.CharField(max_length=10, default='post')

    def __str__(self):
        return "Runner <{}>".format(self.name)

class Runner_to_Track(models.Model):
    runner = models.ForeignKey('Runner')
    track = models.ForeignKey('Track')


class Attendance(models.Model):
    student = models.ForeignKey('Student', null=False, blank=False)
    session = models.ForeignKey('Session', null=False, blank=False)

    @property
    def dt(self):
        return self.session.start_time

    def __str__(self):
        return "Attendance record of {student} for {session}".format(student=self.student.name, session=self.session.name)

    class Meta:
        unique_together = ('session', 'student')
