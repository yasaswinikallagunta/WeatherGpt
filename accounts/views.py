from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import SignupForm
from .models import UserProfile


def signup_view(request):

    if request.method == "POST":

        form = SignupForm(request.POST)

        if form.is_valid():

            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            email = form.cleaned_data["email"]
            phone = form.cleaned_data["phone"]
            password = form.cleaned_data["password"]

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            UserProfile.objects.create(
                user=user,
                phone=phone
            )

            messages.success(
                request,
                "Account created successfully! Please login."
            )

            return redirect("login")

    else:
        form = SignupForm()

    return render(
        request,
        "accounts/signup.html",
        {"form": form}
    )


def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:

            messages.error(
                request,
                "Please enter your email and password."
            )

            return render(
                request,
                "accounts/login.html"
            )

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("home")

        else:

            messages.error(
                request,
                "Invalid email or password."
            )

    return render(
        request,
        "accounts/login.html"
    )


@login_required(login_url="login")
def home_view(request):

    return render(
        request,
        "home.html"
    )


def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("login")


# =========================================================
# PROFILE
# =========================================================

@login_required(login_url="login")
def profile_view(request):

    user = request.user

    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={"phone": ""}
    )

    if request.method == "POST":

        first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        profile_image = request.FILES.get(
            "profile_image"
        )


        # FIRST NAME VALIDATION

        if not first_name:

            messages.error(
                request,
                "First name is required."
            )

            return redirect("profile")


        # LAST NAME VALIDATION

        if not last_name:

            messages.error(
                request,
                "Last name is required."
            )

            return redirect("profile")


        # EMAIL VALIDATION

        if not email:

            messages.error(
                request,
                "Email is required."
            )

            return redirect("profile")


        # PHONE VALIDATION

        if not phone or not phone.isdigit() or len(phone) != 10:

            messages.error(
                request,
                "Enter a valid 10-digit phone number."
            )

            return redirect("profile")


        # CHECK DUPLICATE EMAIL

        email_exists = User.objects.filter(
            email=email
        ).exclude(
            id=user.id
        ).exists()


        if email_exists:

            messages.error(
                request,
                "This email is already used by another account."
            )

            return redirect("profile")


        # UPDATE USER DETAILS

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = email

        user.save()


        # UPDATE PHONE

        profile.phone = phone


        # UPDATE PROFILE IMAGE

        if profile_image:

            profile.profile_image = profile_image


        profile.save()


        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("profile")


    return render(
        request,
        "accounts/profile.html"
    )