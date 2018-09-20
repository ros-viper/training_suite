from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from .models import Quiz, Question, Answer, SubmittedResult, QuizTries
from TrainingSuite.views import get_subscribed_courses, get_one_or_404, get_subscribed_offline_courses, get_default_context, handle_404, get_allowed_offline_sessions, NotFound


def recalculate_if_needed(submitted_result):
    score = 0
    questions_passed = 0
    passed = False
    answers = submitted_result.answers.all()
    questions = []

    for answer in answers:
        questions.append(answer.question)
    for question in set(questions):
        correct = [answer for answer in Question.objects.get(id=question.id).answer_set.all() if answer.correct]
        if all(answer in answers for answer in correct):
            score += question.score
            questions_passed += 1

        if submitted_result.quiz.passed_by_score:  # checks if quiz is being passed by score, else by number of correct questions
            if score >= submitted_result.quiz.passing_score:
                passed = True
        else:
            if questions_passed >= submitted_result.quiz.passing_questions:
                passed = True

    if not (score == submitted_result.score and
                    questions_passed == submitted_result.questions_passed and
                    passed == submitted_result.passed):
        submitted_result.score = score
        submitted_result.questions_passed = questions_passed
        submitted_result.passed = passed
        submitted_result.save()


@login_required
def list_quizes(request):
    model = Quiz
    user = request.user
    courses = get_subscribed_courses(user)
    offline_courses = get_subscribed_offline_courses(user)
    context = get_default_context(request, model, None)


    quizes = set()
    for course in courses:
        for quiz in course.quiz_set.all():
            quizes.add(quiz)

    # Add quizes from offline courses
    for off_course in offline_courses:
        for session in get_allowed_offline_sessions(off_course, user):
            quizes.add(session.quiz)

    context.update(
        quizes=quizes,
    )
    return render(request, 'quiz/list_quizes.html', context)


@login_required
def quiz_mode(request, quiz_id):
    model = Quiz
    quiz = get_one_or_404(Quiz, pk=quiz_id)
    question_list = quiz.question_set.all().order_by('?')[:quiz.test_length]
    user = request.user  # gets the currently logged user
    context = get_default_context(request, model, None)
    courses = get_subscribed_courses(user)  # lists all courses the user is subscribed for
    offline_courses = get_subscribed_offline_courses(user)
    quiz_list = set()

    is_trainer = False
    try:
        is_trainer = bool(user.trainer)
    except ObjectDoesNotExist:
        pass

    for course in courses:
        for q in course.quiz_set.all():
            quiz_list.add(q)

    # Add quizes from offline courses
    for off_course in offline_courses:
        for session in get_allowed_offline_sessions(off_course, user):
            quiz_list.add(session.quiz)

    if is_trainer:
        context = {
            'quiz': quiz,
            'courses': courses,
        }
        return render(request, 'quiz/quiz_detail.html', context)

    elif quiz not in quiz_list:
        raise NotFound

    else:
        if SubmittedResult.objects.filter(quiz=quiz,
                                          student=user.student).exists():  # checks if there is submitted_result object for this quiz/user
            submitted_result = get_one_or_404(SubmittedResult, quiz=quiz, student=user.student)

            recalculate_if_needed(submitted_result)

            return redirect('quiz:submitted_result', submittedresult_id=submitted_result.id)

        else:
            if request.method == "POST":
                if quiz in quiz_list:  # if user is subscribed to the course this quiz is associated with
                    submitted_result = SubmittedResult.objects.get_or_create(
                        student=user.student,
                        quiz=quiz
                    )
                    if submitted_result[1] == False:
                        submitted_result = submitted_result[0]
                        return redirect('quiz:submitted_result', submittedresult_id=submitted_result.id)
                    else:
                        submitted_result = submitted_result[0]
                        for question, answer in request.POST._iterlists():

                            try:
                                correct = [str(answer.id) for answer in
                                        Question.objects.get(id=int(question)).answer_set.all() if
                                        answer.correct]  # returns list of only correct answers for the question
                                for a in answer:
                                    submitted_result.answers.add(
                                        Answer.objects.get(id=int(a)))  # adds chosen answers to the submitted_result object

                                if (set(answer) == set(correct)):  # checks if the question was answered correctly
                                    submitted_result.score += Question.objects.get(id=int(question)).score
                                    submitted_result.questions_passed += 1

                            except:
                                continue

                        if submitted_result.quiz.passed_by_score:  # checks if quiz is being passed by score, else by number of correct questions
                            if submitted_result.score >= submitted_result.quiz.passing_score:
                                submitted_result.passed = True
                        else:
                            if submitted_result.questions_passed >= submitted_result.quiz.passing_questions:
                                submitted_result.passed = True

                        submitted_result.save()
                        return redirect('quiz:submitted_result', submittedresult_id=submitted_result.id)

    number_of_tries = QuizTries.objects.get_or_create(
        student=user.student,
        quiz=quiz
    )
    number_of_tries = number_of_tries[0]
    number_of_tries.tries += 1
    number_of_tries.save()

    context.update(
        question_list=question_list,
        quiz_name=quiz.name,
    )
    return render(request, 'quiz/quiz_mode.html', context)


@login_required
def quiz_result(request, submittedresult_id):
    model = SubmittedResult
    context = get_default_context(request, model, None)
    submitted_result = get_one_or_404(SubmittedResult, pk=submittedresult_id)
    quiz = submitted_result.quiz
    user = request.user
    answers = submitted_result.answers.all()
    courses = get_subscribed_courses(user)
    offline_courses = get_subscribed_offline_courses(user)
    questions = []
    quiz_list = set()

    for course in courses:
        for q in course.quiz_set.all():
            quiz_list.add(q)

    # Add quizes from offline courses
    for off_course in offline_courses:
        for session in get_allowed_offline_sessions(off_course, user):
            quiz_list.add(session.quiz)

    if quiz not in quiz_list:
        raise NotFound
    else:

        recalculate_if_needed(submitted_result)

        is_trainer = False
        try:
            is_trainer = bool(user.trainer)
        except ObjectDoesNotExist:
            pass

        for answer in answers:
            questions.append(answer.question)
        questions = set(questions)

        context.update(
            submitted_result=submitted_result,
            questions=questions,
            is_trainer=is_trainer,
        )

        return render(request, 'quiz/submitted_result.html', context)


@login_required
def quiz_retry(request, submittedresult_id):
    submitted_result = get_one_or_404(SubmittedResult, pk=submittedresult_id)
    user = request.user
    courses = get_subscribed_courses(user)
    offline_courses = get_subscribed_offline_courses(user)
    quiz = submitted_result.quiz
    quiz_list = set()

    for course in courses:
        for q in course.quiz_set.all():
            quiz_list.add(q)

    # Add quizes from offline courses
    for off_course in offline_courses:
        for session in get_allowed_offline_sessions(off_course, user):
            quiz_list.add(session.quiz)

    if quiz in quiz_list:
        submitted_result.delete()
    else:
        pass

    return redirect('quiz:quiz_mode', quiz_id=quiz.id)
