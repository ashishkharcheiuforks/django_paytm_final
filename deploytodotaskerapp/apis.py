import json
import requests
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from oauth2_provider.models import AccessToken
from django.conf import settings
from deploytodotaskerapp import Checksum
from django.utils.translation import get_language
from deploytodotaskerapp.models import Registration, Meal, Order, OrderDetails, Driver,PaytmHistory,Customer
from deploytodotaskerapp.serializers import RegistrationSerializer, \
    MealSerializer, \
    OrderSerializer
from rest_auth.models import TokenModel
#import stripe
#from deploytodotasker.settings import STRIPE_API_KEY



##############
# CUSTOMERS
##############

def customer_get_registrations(request):
    registrations = RegistrationSerializer(
        Registration.objects.all().order_by("-id"),
        many = True,
        context = {"request": request}
    ).data

    return JsonResponse({"registrations": registrations})

def customer_get_meals(request, registration_id):
    meals = MealSerializer(
        Meal.objects.filter(registration_id = registration_id).order_by("-id"),
        many = True,
        context = {"request": request}
    ).data

    return JsonResponse({"meals": meals})

@csrf_exempt
def customer_add_order(request):
    """
        params:
            access_token
            registration_id
            address
            order_details (json format), example:
                [{"meal_id": 1, "quantity": 2},{"meal_id": 2, "quantity": 3}]
            stripe_token

        return:
            {"status": "success"}
    """

    if request.method == "POST":

        ## Get Paytm param Details
        MERCHANT_KEY = settings.PAYTM_MERCHANT_KEY
        MERCHANT_ID = settings.PAYTM_MERCHANT_ID
        CHANNEL_ID = settings.CHANNEL_ID
        WEBSITE=settings.WEBSITE
        INDUSTRY_TYPE_ID=settings.INDUSTRY_TYPE_ID

        ## Get token
        try:
            access_token = TokenModel.objects.get(key = request.POST.get("access_token"))
        except TokenModel.DoesNotExist:
            access_token = AccessToken.objects.get(token = request.POST.get("access_token"),expires__gt = timezone.now())

        ## Get profile
        customer = access_token.user.customer

        ##get order details        
        order_details = json.loads(request.POST["order_details"])
        order_total=0
        for meal in order_details:
            order_total += Meal.objects.get(id = meal["meal_id"]).price * meal["quantity"]
        bill_amount = str(order_total)
 
        ## Generating unique  ids
        order_id = Checksum.__id_generator__()
        CALLBACK_URL =settings.CALLBACK_URL + order_id
        

        data_dict = {
                'MERCHANT_ID':MERCHANT_ID,
                'ORDER_ID':order_id,
                'TXN_AMOUNT': bill_amount,
                'CUST_ID':customer.user.username,
                'CALLBACK_URL':CALLBACK_URL,
                'CHANNEL_ID':CHANNEL_ID,
                'WEBSITE': WEBSITE,
                'INDUSTRY_TYPE_ID':INDUSTRY_TYPE_ID,
                 
        }
        param_dict = data_dict
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(data_dict, MERCHANT_KEY)
        
        return JsonResponse(param_dict)
        

@csrf_exempt
def response(request):


   if request.method == "POST":

        MERCHANT_KEY = settings.PAYTM_MERCHANT_KEY
        MERCHANT_ID = settings.PAYTM_MERCHANT_ID
        orderId=request.POST['ORDER_ID']
    

        ## Get token
        try:
            access_token = TokenModel.objects.get(key = request.POST.get("access_token"))
        except TokenModel.DoesNotExist:
            access_token = AccessToken.objects.get(token = request.POST.get("access_token"),expires__gt = timezone.now())


        ## Get profile
        customer = access_token.user.customer

        ## Get Order Details
        order_details = json.loads(request.POST["order_details"])

        order_total = 0
        for meal in order_details:
            order_total += Meal.objects.get(id = meal["meal_id"]).price * meal["quantity"]
        bill_amount = str(order_total)

        ## initialize a dictionary
        paytmParams = dict()
        paytmParams["MID"] = MERCHANT_ID
        paytmParams["ORDERID"] = orderId
        ## Generate checksum by parameters we have in body
        checksum = Checksum.generate_checksum(paytmParams, MERCHANT_KEY)
        ## put generated checksum value here
        paytmParams["CHECKSUMHASH"] = checksum
        ## prepare JSON string for request
        post_data = json.dumps(paytmParams)

        url = settings.VERIFY_URL
        pay_res = requests.post(url, data = post_data, headers = {"Content-type": "application/json"}).json()
        
        if('ErrorMsg' in pay_res):
            return JsonResponse({'PAY_STATUS':pay_res['ErrorMsg']})

        status=pay_res['STATUS']
        back_response={
                'PAY_STATUS':status,
            }



        if status== 'TXN_SUCCESS':


            ##Step 2 - Create an Order
            order = Order.objects.create(
               customer =customer,
               registration_id =request.POST["registration_id"],
               total = order_total,
               status = Order.COOKING,
               address = request.POST["address"]
            )

            ## Step 3 - Create Order details
            for meal in order_details:
                OrderDetails.objects.create(
                   order = order,
                   meal_id = meal["meal_id"],
                   quantity = meal["quantity"],
                   sub_total = Meal.objects.get(id = meal["meal_id"]).price * meal["quantity"]
                   )
            ## step 4 save the payment
            PaytmHistory.objects.create(customer=customer,order=order,**pay_res)
            return JsonResponse(back_response)
        return JsonResponse(back_response)
       

def customer_get_latest_order(request):
    try:
       access_token = TokenModel.objects.get(key = request.GET.get("access_token"))
    except TokenModel.DoesNotExist:
       access_token = AccessToken.objects.get(token = request.GET.get("access_token"),expires__gt = timezone.now())

    customer = access_token.user.customer
    order = OrderSerializer(Order.objects.filter(customer = customer).last()).data

    return JsonResponse({"order": order})

def customer_driver_location(request):
    try:
       access_token = TokenModel.objects.get(key = request.GET.get("access_token"))
    except TokenModel.DoesNotExist:
       access_token = AccessToken.objects.get(token = request.GET.get("access_token"),expires__gt = timezone.now())

    customer = access_token.user.customer

    # Get driver's location related to this customer's current order.
    # CHANGED DOUBT ONTHEWAY FOR LOCATION VIDEO LECTURE 53
    current_order = Order.objects.filter(customer = customer, status = Order.ONTHEWAY).last()
    location = current_order.driver.location

    return JsonResponse({"location": location})


##############
# Registration
##############

def registration_order_notification(request, last_request_time):
    print(request.user.registration)
    notification = Order.objects.filter(created_at__gt = last_request_time).count()

    return JsonResponse({"notification": notification})


##############
# DRIVERS
##############

def driver_get_ready_orders(request):
    orders = OrderSerializer(
        Order.objects.filter(status = Order.READY, driver = None).order_by("-id"),
        many = True
    ).data

    return JsonResponse({"orders": orders})

@csrf_exempt
# POST
# params: access_token, order_id
def driver_pick_order(request):

    if request.method == "POST":
        # Get token
        try:
            access_token = TokenModel.objects.get(key = request.POST.get("access_token"))
        except TokenModel.DoesNotExist:
            access_token = AccessToken.objects.get(token = request.POST.get("access_token"),expires__gt = timezone.now())

        # Get Driver
        driver = access_token.user.driver

        # Check if driver can only pick up one order at the same time
        if Order.objects.filter(driver = driver).exclude(status = Order.ONTHEWAY):
            return JsonResponse({"status": "failed", "error": "You can only pick one order at the same time."})

        try:
            order = Order.objects.get(
                id = request.POST["order_id"],
                driver = None,
                status = Order.READY
            )
            order.driver = driver
            order.status = Order.ONTHEWAY
            order.picked_at = timezone.now()
            order.save()

            return JsonResponse({"status": "success"})

        except Order.DoesNotExist:
            return JsonResponse({"status": "failed", "error": "This order has been picked up by another."})

    return JsonResponse({})

# GET params: access_token
def driver_get_latest_order(request):
    # Get token
    try:
       access_token = TokenModel.objects.get(key = request.GET.get("access_token"))
    except TokenModel.DoesNotExist:
       access_token = AccessToken.objects.get(token = request.GET.get("access_token"),expires__gt = timezone.now())
    driver = access_token.user.driver
    order = OrderSerializer(
        Order.objects.filter(driver = driver).order_by("picked_at").last()
    ).data

    return JsonResponse({"order": order})

# POST params: access_token, order_id
@csrf_exempt
def driver_complete_order(request):
    # Get token
    try:
       access_token = TokenModel.objects.get(key = request.POST.get("access_token"))
    except TokenModel.DoesNotExist:
       access_token = AccessToken.objects.get(token = request.POST.get("access_token"),expires__gt = timezone.now())

    driver = access_token.user.driver

    order = Order.objects.get(id = request.POST["order_id"], driver = driver)
    order.status = Order.DELIVERED
    order.save()

    return JsonResponse({"status": "success"})

# GET params: access_token
def driver_get_revenue(request):
    try:
       access_token = TokenModel.objects.get(key = request.GET.get("access_token"))
    except TokenModel.DoesNotExist:
       access_token = AccessToken.objects.get(token = request.GET.get("access_token"),expires__gt = timezone.now())

    driver = access_token.user.driver

    from datetime import timedelta

    revenue = {}
    today = timezone.now()
    current_weekdays = [today + timedelta(days = i) for i in range(0 - today.weekday(), 7 - today.weekday())]

    for day in current_weekdays:
        orders = Order.objects.filter(
            driver = driver,
            status = Order.DELIVERED,
            created_at__year = day.year,
            created_at__month = day.month,
            created_at__day = day.day
        )

        revenue[day.strftime("%a")] = sum(order.total for order in orders)

    return JsonResponse({"revenue": revenue})

# POST - params: access_token, "lat,lng"
@csrf_exempt
def driver_update_location(request):
    if request.method == "POST":

        try:
            access_token = TokenModel.objects.get(key = request.POST.get("access_token"))
        except TokenModel.DoesNotExist:
            access_token = AccessToken.objects.get(token = request.POST.get("access_token"),expires__gt = timezone.now())
        driver = access_token.user.driver

        # Set location string => database
        driver.location = request.POST["location"]
        driver.save()

        return JsonResponse({"status": "success"})












