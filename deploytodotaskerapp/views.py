from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from deploytodotaskerapp.forms import (
    UserForm,
    RegistrationForm,
    UserFormForEdit,
    MealForm,
    DrinkForm,
)
from django.contrib.auth import authenticate, login

from django.contrib.auth.models import User
from deploytodotaskerapp.models import Meal, Drink, Order, Driver

from django.db.models import Sum, Count, Case, When


# Create your views here.
def home(request):
    return redirect(registration_home)


@login_required(login_url="/registration/login/")
def registration_home(request):
    return redirect(registration_order)


@login_required(login_url="/registration/login/")
def registration_account(request):
    user_form = UserFormForEdit(instance=request.user)
    registration_form = RegistrationForm(instance=request.user.registration)

    if request.method == "POST":
        user_form = UserFormForEdit(request.POST, instance=request.user)
        registration_form = RegistrationForm(
            request.POST, request.FILES, instance=request.user.registration
        )

        if user_form.is_valid() and registration_form.is_valid():
            user_form.save()
            registration_form.save()

    return render(
        request,
        "deploytodotaskerapp/registration/account.html",
        {"user_form": user_form, "registration_form": registration_form},
    )


# DOUBT changed filter according to video 32 at 1:21


@login_required(login_url="/registration/login/")
def registration_meal(request):
    meals = Meal.objects.filter(registration=request.user.registration).order_by("-id")
    return render(
        request, "deploytodotaskerapp/registration/meal.html", {"meals": meals}
    )


@login_required(login_url="/registration/login/")
def registration_drink(request):
    drinks = Drink.objects.filter(registration=request.user.registration).order_by(
        "-id"
    )
    return render(
        request, "deploytodotaskerapp/registration/drink.html", {"drinks": drinks}
    )


@login_required(login_url="/registration/login/")
def registration_add_meal(request):
    form = MealForm()

    if request.method == "POST":
        form = MealForm(request.POST, request.FILES)

        if form.is_valid():
            meal = form.save(commit=False)
            meal.registration = request.user.registration
            meal.save()
            return redirect(registration_meal)

    return render(
        request, "deploytodotaskerapp/registration/add_meal.html", {"form": form}
    )


@login_required(login_url="/registration/login/")
def registration_add_drink(request):
    form = DrinkForm()

    if request.method == "POST":
        form = DrinkForm(request.POST, request.FILES)

        if form.is_valid():
            drink = form.save(commit=False)
            drink.registration = request.user.registration
            drink.save()
            return redirect(registration_drink)

    return render(
        request, "deploytodotaskerapp/registration/add_drink.html", {"form": form}
    )


@login_required(login_url="/registration/login/")
def registration_edit_meal(request, meal_id):
    form = MealForm(instance=Meal.objects.get(id=meal_id))

    if request.method == "POST":
        form = MealForm(
            request.POST, request.FILES, instance=Meal.objects.get(id=meal_id)
        )

        if form.is_valid():
            form.save()
            return redirect(registration_meal)
    return render(request, "deploytodotaskerapp/registration/edit_meal.html", {"form": form})


@login_required(login_url="/registration/login/")
def registration_edit_drink(request, drink_id):
    form = DrinkForm(instance=Drink.objects.get(id=drink_id))

    if request.method == "POST":
        form = DrinkForm(
            request.POST, request.FILES, instance=Drink.objects.get(id=drink_id)
        )

        if form.is_valid():
            form.save()
            return redirect(registration_drink)
    return render(request, "deploytodotaskerapp/registration/edit_drink.html", {"form": form})


@login_required(login_url="/registration/login/")
def registration_order(request):
    """
    :param request:
    :return:
    """
    if request.method == "POST":

        order = Order.objects.get(
            id=request.POST["id"], registration=request.user.registration
        )

        if order.status == Order.COOKING:
            order.status = Order.READY
            order.save()

    orders = Order.objects.filter(registration=request.user.registration).order_by(
        "-id"
    )
    return render(
        request, "deploytodotaskerapp/registration/order.html", {"orders": orders}
    )


@login_required(login_url="/registration/login/")
def registration_report(request):
    """
    :param request:
    :return:
    """
    # Calculate revenue and number of order by current week
    from datetime import datetime, timedelta

    revenue = []
    orders = []

    # Calculate weekdays
    today = datetime.now()
    current_weekdays = [
        today + timedelta(days=i)
        for i in range(0 - today.weekday(), 7 - today.weekday())
    ]

    for day in current_weekdays:
        delivered_orders = Order.objects.filter(
            registration=request.user.registration,
            status=Order.DELIVERED,
            created_at__year=day.year,
            created_at__month=day.month,
            created_at__day=day.day,
        )
        revenue.append(sum(order.total for order in delivered_orders))
        orders.append(delivered_orders.count())

    # Top 3 Meals
    top3_meals = (
        Meal.objects.filter(registration=request.user.registration)
        .annotate(total_order=Sum("orderdetails__quantity"))
        .order_by("-total_order")[:3]
    )

    meal = {
        "labels": [meal.name for meal in top3_meals],
        "data": [meal.total_order or 0 for meal in top3_meals],
    }

    # Top 3 Drinks
    top3_drinks = (
        Drink.objects.filter(registration=request.user.registration)
        .annotate(total_order=Sum("orderdetails__quantity"))
        .order_by("-total_order")[:3]
    )

    drink = {
        "labels": [drink.name for drink in top3_drinks],
        "data": [drink.total_order or 0 for drink in top3_drinks],
    }

    # Top 3 Drivers
    top3_drivers = Driver.objects.annotate(
        total_order=Count(
            Case(When(order__registration=request.user.registration, then=1))
        )
    ).order_by("-total_order")[:3]

    driver = {
        "labels": [driver.user.get_full_name() for driver in top3_drivers],
        "data": [driver.total_order for driver in top3_drivers],
    }

    return render(
        request,
        "deploytodotaskerapp/registration/report.html",
        {
            "revenue": revenue,
            "orders": orders,
            "meal": meal,
            "drink": drink,
            "driver": driver,
        },
    )


def registration_sign_up(request):
    user_form = UserForm()
    registration_form = RegistrationForm()

    if request.method == "POST":
        user_form = UserForm(request.POST)
        registration_form = RegistrationForm(request.POST, request.FILES)

        if user_form.is_valid() and registration_form.is_valid():
            new_user = User.objects.create_user(**user_form.cleaned_data)
            new_registration = registration_form.save(commit=False)
            new_registration.user = new_user
            new_registration.save()

            login(
                request,
                authenticate(
                    username=user_form.cleaned_data["username"],
                    password=user_form.cleaned_data["password"],
                ),
            )

            return redirect(registration_home)

    return render(
        request,
        "deploytodotaskerapp/registration/sign_up.html",
        {"user_form": user_form, "registration_form": registration_form},
    )

