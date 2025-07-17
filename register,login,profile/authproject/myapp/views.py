from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import AuthUser
from django.http import JsonResponse
from .serializers import UserSerializer
from django.contrib.auth import update_session_auth_hash
import os
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
import re
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework.views import APIView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


User = get_user_model()
# Create your views here.
pattern = r'^[\w\.-]+@(gmail\.com|yahoo\.com)$'
# pattern1 = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,16}$'
@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        try:
            data = request.POST
            username = data.get('username')
            email    = data.get('email')
            phone    = data.get('phone')
            password = data.get('password')
            image = request.FILES.get('image')



            if not re.match(pattern, email):
                return JsonResponse({'errors': ' Email must be from gmail.com or yahoo.com.'}, status=400)
            # if not re.match(pattern1, password):
            #     return JsonResponse({'errors': ' Password must be min len 8 and max len 16.'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'errors': ' Username already exists.'}, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({'errors': ' Email already exists.'}, status=400)

            serializer = UserSerializer(data=request.POST)
            if serializer.is_valid():
                user = User.objects.create_user(username=username, email=email, password=password, image=image)
                user.set_password(password)
                user.phone = phone
                user.save()

                #Send verification email here
                send_verification_email(user, request)

                return JsonResponse({
                        'message': 'Registered successfully! Please verify your email.',
                        'redirect_url': '/token-send'}, status=201)

            else:
                return JsonResponse({'errors': serializer.errors}, status=400)

        except Exception as e:
            return JsonResponse({'errors': str(e)}, status=400)

    return render(request, 'Singup.html')

@csrf_exempt
def login_view(request):
    if request.method == 'GET':
        return render(request, 'Login.html')  #  render form when page is opened

    elif request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            username = data.get('username')
            password = data.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'message': ' Login successful!', 'redirect_url': '/profile'}, status=200)
            else:
                return JsonResponse({'errors': ' Invalid username or password'}, status=400)

        except Exception as e:
            return JsonResponse({'errors': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)
def success(request):
    return render(request, 'success.html')
def token_send(request):
    return render(request, 'token_send.html')

@login_required(login_url='login')
def profile_view(request):
    return render(request, 'profile.html')

def logout_page(request):
    logout(request)
    return redirect('login')

@login_required
def delete_account(request):
   
    if request.method == 'POST':
        request.user.delete()
        profile_delete_profile_nitification(request.user)   
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'error': 'Invalid method'}, status=400)


@csrf_exempt
@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            data = request.POST
            user = request.user

            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            phone = data.get('phone', '').strip()
            password = data.get('password', '').strip()
            image = request.FILES.get('image')
            
            print("Incoming:", username, email, phone, password, image)
            print("User before update:", user.username, user.email)


            # Optional: Add email pattern check if not in serializer
            pattern = r'^[\w\.-]+@(?:gmail|yahoo)\.com$'
            if email and not re.match(pattern, email):
                return JsonResponse({'errors': ' Email must be from gmail.com or yahoo.com.'}, status=400)

            if username and username != user.username:
                user.username = username

            if email and email != user.email:
                user.email = email
            if image and image != user.image:
                user.image = image

            if phone and hasattr(user, 'phone') and phone != user.phone:
                user.phone = phone

            if password:
                user.set_password(password)
                update_session_auth_hash(request, user)  # Prevent logout

            user.save()

            # if email and email != user.email:
            #     user.email = email
            #     update_verification(user, request)
            send_profile_update_notification(user)

            return JsonResponse({'message': ' Profile updated successfully!'}, status=200)

        except Exception as e:
            return JsonResponse({'errors': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)

def send_profile_update_notification(user):
    subject = 'Your profile was updated'
    message = 'Hi {},\n\nYour account profile was successfully updated.'.format(user.username)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)

def profile_delete_profile_nitification(user):
    subject = 'Your profile was deleted'
    message = 'Hi {},\n\nYour account profile was successfully deleted.'.format(user.username)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)



def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verify_url = request.build_absolute_uri(
        reverse('verify-email', kwargs={'uidb64': uid, 'token': token})
    )

    subject = 'Verify your email'
    message = f'Click the link to verify your email:\n{verify_url}'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)
# views.py

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            return redirect('success')
        else:
            return HttpResponse("Invalid or expired token", status=400)
