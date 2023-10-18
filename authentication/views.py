from django.shortcuts import render, redirect, HttpResponse
from .models import CustomUser
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import UserRegisterForm, UserEditForm
from django.contrib.auth.decorators import login_required


def login_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        credential = authenticate(request, username=email, password=password)
        previous_url = request.GET.get('next')
        if credential is not None:
            user = CustomUser.objects.get(email=email)
            if user.is_authenticated:
                login(request, credential)
                if previous_url:
                    return redirect(previous_url)
                else:
                    return redirect('upload')
            else:
                messages.success(request, 'Please confirm your login details ')
                return redirect('login')
        else:
            messages.success(request, 'Invalid Username/Password')
            return redirect('login')
    else:
        return render(request, 'login.html', {})


def logout_user(request):
    logout(request)
    messages.success(request, 'You have logged out successfully.')
    return redirect('login')


def register_user(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user_cred = form.save(commit=False)
            user_cred.save()
            login(request, user_cred, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('files')

    else:
        form = UserRegisterForm()
    context = {'form': form}
    return render(request, 'signUp.html', context)


#   @login_required()
#   def change_password(request):
#       if request.method == 'POST':
#           form = PasswordChangeForm(data=request.POST, user=request.user)
#           if form.is_valid():
#               form.save()
#               update_session_auth_hash(request, form.user)
#               messages.success(request, 'Password changed successfully')
#               return redirect('dashboard')

#           else:
#               form = PasswordChangeForm(user=request.user)
#           context = {'form': form}
#           return render(request, 'change_password.html', context)
