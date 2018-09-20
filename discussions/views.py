from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from .models import DiscussionThread, DiscussionMessage
from TrainingSuite.models import Solution
from TrainingSuite.views import get_subscribed_courses, get_default_context

import requests
import base64
import xml.etree.ElementTree as ET


@login_required
def list_threads(request):
    discussion_threads = DiscussionThread.objects.all()

    # GLO API Key: e80d6b8cbea3754bab60a51a6e72b35329df377b

    # payload= {'login':'user_id', 'password':'password'}
    # with requests.Session() as s:
    #     r = s.get('https://glo.globallogic.com/apps/glo/login')
    #     r = s.post('https://glo.globallogic.com/apps/glo/authenticate', data=payload)
    #     print(r.text)

    # credentials = b"r.rzhenetskyy:R1986ttyl"
    # en_credentials = base64.b64encode(credentials)

    # s = requests.session()

    # r = s.post('http://gloapis.globallogic.com/e80d6b8cbea3754bab60a51a6e72b35329df377b/gloapis/login', headers={'Authorization': en_credentials})
    # print(r.text)
    # token = ET.fromstring(r.content)
    # lst = []
    # for node in token.iter():
    #     lst.append(node.text)
    # print(lst[1])
    
    # p = s.get('http://gloapis.globallogic.com/e80d6b8cbea3754bab60a51a6e72b35329df377b/%s/gloapis/users/r.rzhenetskyy/profile_picture/profile' % token)
    # print(p)

    if request.method == "POST" and not request.POST['thread_subject'] == '':
        discussion_thread = DiscussionThread.objects.get_or_create(
                        author = request.user,
                        subject = request.POST["thread_subject"],
                        content = request.POST["thread_content"],
                    )
        discussion_thread=discussion_thread[0]
        discussion_thread.save()
        return redirect('discussions:thread_detail', discussionthread_id=discussion_thread.id)

    context = get_default_context(request, DiscussionThread, None, discussion_threads)
    return render(request, 'discussions/list_threads.html', context)

@login_required
def thread_detail(request, discussionthread_id):
    discussion_thread = get_object_or_404(DiscussionThread, pk=discussionthread_id)
    discussion_messages = discussion_thread.discussionmessage_set.all()

    paginator = Paginator(discussion_messages, 5)
    page = request.GET.get('page')

    pages = [x for x in range(1, paginator.num_pages+1)]

    if len(pages) > 5:
        if page == None or int(page) == 1 or int(page) <= 3:                    # if page is 1-3
            pages = pages[:5] + ['...']

        elif int(page) == pages[-1]:                                            # if page is last
            pages = ['...'] + pages[int(page)-5:]
        elif int(page) > 3 and not int(page) == pages[-2]:                      # if page is 4 and further
            if int(page) == pages[-3]:
                pages = ['...'] + pages[int(page)-3:int(page)+2]
            else:
                pages = ['...'] + pages[int(page)-3:int(page)+2] + ['...']            
        else:                                                                   # if page is pre-last
            pages = ['...'] + pages[int(page)-4:]

    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        messages = paginator.page(paginator.num_pages)

    if request.method == "POST" and 'message' in request.POST and request.POST['message'] !='':
        if 'messageID' in request.POST:
            message = get_object_or_404(DiscussionMessage, pk=request.POST['messageID'])
            if message.author == request.user:
                message.content = request.POST['message']
                message.save()
        else:
            message = DiscussionMessage.objects.create(
                author=request.user,
                content=request.POST['message'],
                thread=DiscussionThread.objects.get(id=discussion_thread.id),
            )
            
            if 'target_messageid' in request.POST:
                message.quote = request.POST['quotedmessage']
            message.save()

        last_page = paginator.num_pages

        if discussion_messages.count() % 5 == 1:
            last_page += 1

        return HttpResponseRedirect("%s?page=%s" % (reverse('discussions:thread_detail', kwargs={'discussionthread_id':discussion_thread.id}), last_page))

    elif request.method == "POST" and 'threadContent' in request.POST:
        discussion_thread = get_object_or_404(DiscussionThread, pk=request.POST['threadID'])
        if discussion_thread.author == request.user:
            discussion_thread.content = request.POST['threadContent']
            discussion_thread.save()
            
        last_page = paginator.num_pages

        if discussion_messages.count() % 5 == 1:
            last_page += 1

        return HttpResponseRedirect("%s?page=%s" % (reverse('discussions:thread_detail', kwargs={'discussionthread_id':discussion_thread.id}), last_page))




    context = get_default_context(request, DiscussionThread, discussion_thread)
    context.update(
        messages=messages,
        pages=pages,
        paginator=paginator)

    return render(request, 'discussions/thread_detail.html', context)

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(DiscussionMessage, pk=message_id)
    current_user = request.user
    discussion_thread = message.thread


    if message.author == current_user:
        message.delete()

    return redirect('discussions:thread_detail', discussionthread_id=discussion_thread.id)

@login_required
def user_detail(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    messages = DiscussionMessage.objects.filter(author=user).reverse()[:5]
    courses = get_subscribed_courses(user)
    solutions_number = 0

    role = '-'

    if hasattr(user, 'trainer'):
        role = 'Trainer'
    elif hasattr(user, 'student'):
        role = 'Student'
        solutions_number = Solution.objects.filter(author=user.student).count()
    

    context = {
        'user': user,
        'messages': messages,
        'courses': courses,
        'role': role,
        'solutions_number': solutions_number,
    }

    return render(request, 'discussions/user_detail.html', context)

    