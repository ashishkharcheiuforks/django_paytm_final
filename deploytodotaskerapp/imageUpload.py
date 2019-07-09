from deploytodotaskerapp.models import ImageStore,User,Customer,Driver
from deploytodotaskerapp.forms import ImageUploadForm
from django.http import JsonResponse
from django.http import HttpResponse
from oauth2_provider.models import AccessToken
from rest_auth.models import TokenModel
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
@csrf_exempt
def upload_pic(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            
            
            try:
               access_token = TokenModel.objects.get(key = form.cleaned_data['token'])
            except TokenModel.DoesNotExist:
               return HttpResponse("changing avatar is not available for sociallogin")
            user=access_token.user
            image = form.cleaned_data['image']
            try:
               image_store = ImageStore.objects.get(user=user)
               image_store.image=image
               image_store.save()
            except ImageStore.DoesNotExist:            
               image_store=ImageStore.objects.create(user=user,image=image)
            IMG_URL=settings.BASE_URL+image_store.image.url
            try:
               customer=Customer.objects.get(user=user)
               customer.avatar=IMG_URL
               customer.save()
            except Customer.DoesNotExist: 
               print("no customer instance")
            try:
               driver=Driver.objects.get(user=user)
               driver.avatar=IMG_URL
               driver.save()            
            except Driver.DoesNotExist: 
               print("no driver instance")

            data={
                "avatar":IMG_URL,
            }
            return JsonResponse(data)
    return HttpResponseForbidden('allowed only via POST')


