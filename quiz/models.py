from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth.models import User



class Quiz(models.Model):
    test_length = models.IntegerField(default=5)
    course = models.ManyToManyField('TrainingSuite.Course', blank=False)
    tracks = models.ManyToManyField('TrainingSuite.Track', through='Quiz_to_Track', related_name='quizes', blank=True)
    name = models.CharField(max_length=100, blank=False)
    deadline = models.DateField(blank=True, null=True)
    deadline_active = models.BooleanField(default=False)
    passing_score = models.IntegerField(default=0)
    passed_by_score = models.BooleanField(default=False)
    passing_questions = models.IntegerField(default=0)
    active = models.BooleanField(default=False)
    verbose_results_enabled = models.BooleanField(default=False)
    retry_on_fail_enabled = models.BooleanField(default=True)
    retry_on_pass_enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class Quiz_to_Track(models.Model):
    quiz = models.ForeignKey('Quiz')
    track = models.ForeignKey('TrainingSuite.Track')


class Question(models.Model):
    content = models.TextField(max_length=1000, blank=False, null=False)
    quiz = models.ForeignKey('Quiz', blank=False, null=False)
    score = models.IntegerField(default=1)
    number = models.IntegerField(default=0)
    
    def Meta():
        unique_together = ('number', 'quiz')
        
    def get_available_number(self):
        """
        Get next available number for question for quiz
        
        1. get all questions for self.quiz
        1a. used_numbers = [q.number for q in questions]
        2. loop for 0..len(questions) and find unused number
        """
        if self.number == 0:
            questions = Question.objects.filter(quiz=self.quiz)
            used_numbers = [q.number for q in questions]
            
            if questions:
                for number in range(1,(len(questions))+1):
                    if number not in used_numbers:
                        return number
                return used_numbers[-1]+1
            return 1
        return self.number
        
    def save(self, *args, **kwargs):
        self.number = self.get_available_number()
        super().save(*args, **kwargs)
        
    @property
    def correct_number(self):
        return self.answer_set.filter(correct=True).count()
        
    def __str__(self):
        return "Question #{} of quiz '{}'".format(self.number, self.quiz)
    
class Answer(models.Model):
    content = models.CharField(max_length=500, blank=False, null=False)
    question = models.ForeignKey('Question', blank=False, null=False)
    correct = models.BooleanField(default=False)
    number = models.IntegerField(default=0)
    
    def Meta():
        unique_together = ('number', 'question')
        
    def get_available_answer_number(self):
        """
        Get next available number for answer for question
        
        1. get all answers for self.question
        1a. used_numbers = [a.number for a in answers]
        2. loop for 0..len(answers) and find unused number
        """
        if self.number == 0:
            answers = Answer.objects.filter(question=self.question)
            used_numbers = [a.number for a in answers]
            
            if answers:
                for number in range(1,(len(answers))+1):
                    if number not in used_numbers:
                        return number
                return used_numbers[-1]+1
            return 1
        return self.number
        
    def save(self, *args, **kwargs):
        self.number = self.get_available_answer_number()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return "Answer #{} of question #{}".format(self.number, self.question.number)
  
class SubmittedResult(models.Model):
    quiz = models.ForeignKey('Quiz', blank=False, null=False)
    student = models.ForeignKey('TrainingSuite.Student', blank=False)
    score = models.IntegerField(default=0)
    date_submitted = models.DateField(auto_now_add=True, blank=False, null=False)
    questions_passed = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    answers = models.ManyToManyField('Answer', blank=False)
    
    def __str__(self):
        return '{0} {1}'.format(self.quiz.name, self.student.name)

    class Meta:
        unique_together = ('student', 'quiz')

class QuizTries(models.Model):
    quiz = models.ForeignKey('Quiz', blank=False, null=False)
    student = models.ForeignKey('TrainingSuite.Student', blank=False)
    tries = models.IntegerField(default=0)
    
    def __str__(self):
        return '{0} {1}'.format(self.quiz.name, self.student.name)
