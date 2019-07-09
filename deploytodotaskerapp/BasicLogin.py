from rest_auth.registration.serializers import RegisterSerializer
from rest_auth.serializers import PasswordResetSerializer
from django.conf import settings
from deploytodotaskerapp.models import Customer,Driver
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_auth.models import TokenModel
from allauth.account.forms import ResetPasswordForm
class CustomRegisterSerializers(RegisterSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()    

    def custom_signup(self, request, user):
        user.first_name = self.validated_data.get('first_name', '')
        user.last_name=self.validated_data.get('last_name', '')
        user.save()
        
        customer=Customer.objects.create(user=user,avatar=settings.DISPLAY_PIC_DEFAULT_URL)
        driver=Driver.objects.create(user=user,avatar=settings.DISPLAY_PIC_DEFAULT_URL)
        

class CustomTokenSerializers(serializers.ModelSerializer):
   
    full_name = serializers.ReadOnlyField(source="user.get_full_name")
    avatar = serializers.ReadOnlyField(source="user.customer.avatar")
    class Meta:
        model = TokenModel
        fields = ('key','full_name','avatar')

class CustomPasswordResetSerializer(PasswordResetSerializer):
    """
    Serializer for requesting a password reset e-mail.
    """
   # email = serializers.EmailField()

    password_reset_form_class = ResetPasswordForm

