from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from TrainingSuite.models import Course, Session, Student, Trainer, Task, Solution, Comment, Resource, Notification, \
    Slideshow, Slides_to_Sessions, Track, Track_to_Trainer, Course_to_Track, Runner, OfflineCourse, OfflineSession, OfflineCourse_to_Track, \
    Attendance

# Register your models here.
# admin.site.register(Session)
admin.site.register(Student)
admin.site.register(Trainer)
# admin.site.register(Task)
admin.site.register(Runner)
admin.site.register(Solution)
admin.site.register(Resource)
admin.site.register(Notification)
admin.site.register(Attendance)
# admin.site.register(Slideshow)

class CourseInLine(admin.TabularInline):
    model = Course_to_Track
    extra = 1

class CourseAdmin(admin.ModelAdmin):
    inlines = (CourseInLine,)

admin.site.register(Course, CourseAdmin)

class OfflineCourseInline(admin.TabularInline):
    model = OfflineCourse_to_Track
    extra = 1

class OfflineCourseAdmin(admin.ModelAdmin):
    inlines = (OfflineCourseInline,)

admin.site.register(OfflineCourse, OfflineCourseAdmin)

class SlideshowInline(admin.TabularInline):
    model = Slides_to_Sessions
    extra = 1 # how many rows to show

class SlideshowAdmin(admin.ModelAdmin):
    inlines = (SlideshowInline,)

admin.site.register(Slideshow, SlideshowAdmin)

class TrackInLine(admin.TabularInline):
    model = Track_to_Trainer
    extra= 1

class TrackAdmin(admin.ModelAdmin):
    inlines = (TrackInLine,)

admin.site.register(Track, TrackAdmin)

class TaskAdmin(SummernoteModelAdmin):
    pass

class SessionAdmin(SummernoteModelAdmin):
    pass

class OfflineSessionAdmin(SummernoteModelAdmin):
    exclude = ('order',)

class CommentAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)



admin.site.register(Task, TaskAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(OfflineSession, OfflineSessionAdmin)