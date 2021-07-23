import json
import csv
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib import messages
from better_profanity import profanity
import re
import string

from .models import User, Post, Comment
from .forms import *



# Create Post
def index(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES or None)

        if form.is_valid():
            post = Post(
                user=User.objects.get(pk=request.user.id),
                content=form.cleaned_data.get("content"),
                image = form.cleaned_data.get("image")
            )
            
            post.save()
            return redirect('index')
    else:
        form = PostForm()
    
    posts = Post.objects.all().order_by("-timestamp")
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, "network/index.html", {
        "page_obj": page_obj,
        'form' : form

    })

@login_required
def user_page(request, username):
    target_user = User.objects.get(username=username)

    posts = Post.objects.filter(user__username=username).order_by("-timestamp")

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, "network/profile.html", {
        "target_user": target_user,
        "page_obj": page_obj
    })

@login_required
def following(request):
    posts = [] 
    all_posts = Post.objects.order_by("-timestamp").all()
    
    # Iterating each and every post and checking if that post's owner is in the loggedin user's following list
    for post in all_posts:
        
        if post.user in request.user.following.all():
            # Then append that post to the post list initialized above
            posts.append(post)

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, "network/following.html", {
        "page_obj": page_obj
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")



@csrf_exempt
def follow_user(request, username):
    target_user = User.objects.get(username=username)

    # Unfollow the user if the user is already in the followers
    if request.user in target_user.followers.all():
        target_user.followers.remove(request.user)
        target_user.save()

        return JsonResponse({"message": f'{username} unfollowed!'})

    # Follow the user if the user is not in the followers
    target_user.followers.add(request.user)
    target_user.save()

    return JsonResponse({"message": f'{username} followed!'})

@csrf_exempt
@login_required
def edit_post(request):
    # Liking a new post must be via PUT
    if request.method == "PUT":
        data = json.loads(request.body)
        post_id = data.get("postId", "")
        content = data.get("content", "")
        post = Post.objects.get(pk=post_id)

        # Ensure to edit only the user's own posts
        if request.user.username != post.user.username:
            return JsonResponse({"error": "Can't edit another user's post"}, status=403)
        
        post.content = content
        post.save()

        return JsonResponse({"message": "Post edited!"}, status=200)
    else:
        return JsonResponse({"error": "Must be PUT method"}, status=400)

    

@csrf_exempt
@login_required
def like_post(request):
    # Liking a new post must be via PUT
    if request.method == "PUT":
        data = json.loads(request.body)
        post_id = data.get("postId", "")
        post = Post.objects.get(pk=post_id)

        # Unlike if the User already liked 
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            post.save()

            return JsonResponse({"liked": False}, status=200)
        
        # Else Like it 
        post.likes.add(request.user)
        post.save()

        return JsonResponse({"liked": True}, status=200)
    else:
        return JsonResponse({"error": "Must be PUT method"}, status=400)

@csrf_exempt
@login_required
def comment_post(request, id):
    if request.method == "POST":
        
        if not request.user.is_authenticated:
            messages.warning(request, 'Log in to submit comments, like posts and more!')
            return HttpResponseRedirect(reverse("index"))

        else:
            if request.POST["type"] == "comment":
                added_comment = request.POST["content"]

                comment = Comment(
                    user = User.objects.get(pk=request.user.id),
                    post = Post.objects.get(pk=id),
                    comment = added_comment
        
                )

                comment.save()
                return HttpResponseRedirect(reverse("index"))