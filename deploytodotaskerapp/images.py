from deploytodotaskerapp.models import ImageStore
from deploytodotaskerapp.forms import ImageUploadForm
def upload_pic(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            m = ImageStore()
            m.user=User.objects.first()
            m.image = form.cleaned_data['image']
            print(form.cleaned_data['token'])
            m.save()
            return HttpResponse('image upload success')
    return HttpResponseForbidden('allowed only via POST')
