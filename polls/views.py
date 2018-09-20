from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from polls.models import Poll, Question, Option, UserOption, SubmittedResult
from TrainingSuite.models import Trainer, Student, Course
from TrainingSuite.views import get_subscribed_courses, get_default_context


@login_required
def polls_list(request):
    template_name = 'polls_list.html'
    courses = get_subscribed_courses(request.user)
    polls = Poll.objects.filter(course__in=courses)
    context = get_default_context(request, Poll, None, polls)
    
    return render(request, template_name, context)
    

@login_required
def poll_mode(request, pk):
    template_name = 'poll_mode.html'
    courses = get_subscribed_courses(request.user)
    poll = get_object_or_404(Poll, pk=pk, course__in=courses)
    context = get_default_context(request, Poll, poll)
    
    if hasattr(request.user, "trainer") or SubmittedResult.objects.filter(poll=poll, student=request.user.student):
        print("Super bad situation!")
        return redirect('poll_results', pk)
    
    if request.method == 'POST':
        selected_options = []
        user_options = {}
        for k,v in request.POST._iterlists():
            try:
                question_pk = int(k)
                if "usr" in v: # User-defined option found
                    del v[v.index("usr")]
                    user_options[question_pk] = request.POST.get("usr_%s" % question_pk, "")
                option_ids = list(map(int, v))
            except (IndexError, TypeError, ValueError):
                continue
            q = Question.objects.filter(pk=question_pk).first()
            if q.poll == poll:
                for option in Option.objects.filter(pk__in=option_ids):
                    selected_options.append(option)
                    option.votes += 1
                    option.save()
            else:
                return redirect('/')
        
        result = SubmittedResult.objects.update_or_create(
            poll=poll,
            student=request.user.student)[0]
        
        if result.options.all():
            result.options.clear()
        if result.user_options.all():
            result.user_options.clear()
        
        for option in selected_options:
            result.options.add(option)
        for k,v in user_options.items():
            user_option = UserOption.objects.update_or_create(
                question=Question.objects.filter(pk=k).first(), 
                student=request.user.student, 
                content=v)[0]
            result.user_options.add(user_option)
        result.save()
        
        return redirect('poll_results', pk)

    return render(request, template_name, context)


@login_required
def poll_results(request, pk):
    template_name = 'poll_results.html'
    courses = get_subscribed_courses(request.user)
    poll = get_object_or_404(Poll, pk=pk, course__in=courses)
    context = get_default_context(request, Poll, poll)
    
    if hasattr(request.user, "student") and not SubmittedResult.objects.filter(poll=poll, student=request.user.student):
        return redirect('poll_mode', pk)
    
    return render(request, template_name, context)