from rest_framework import serializers

from deploytodotaskerapp.models import (
    Registration,
    Meal,
    Drink,
    Customer,
    Driver,
    Order,
    OrderDetails,
)


class RegistrationSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, registration):
        request = self.context.get("request")
        logo_url = registration.logo.url
        return request.build_absolute_uri(logo_url)

    class Meta:
        model = Registration
        fields = ("id", "name", "phone", "address", "logo")


class MealSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, meal):
        request = self.context.get("request")
        image_url = meal.image.url
        return request.build_absolute_uri(image_url)

    class Meta:
        model = Meal
        fields = ("id", "name", "short_description", "image", "price")


class DrinkSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, drink):
        request = self.context.get("request")
        image_url = drink.image.url
        return request.build_absolute_uri(image_url)

    class Meta:
        model = Drink
        fields = ("id", "name", "short_description", "image", "price")


# ORDER SERIALIZER
class OrderCustomerSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Customer
        fields = ("id", "name", "avatar", "phone", "address")


class OrderDriverSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Customer
        fields = ("id", "name", "avatar", "phone", "address")


class OrderRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ("id", "name", "phone", "address")


class OrderMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = ("id", "name", "price")

class OrderDrinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drink
        fields = ("id", "name", "price")


class OrderDetailsSerializer(serializers.ModelSerializer):
    meal = OrderMealSerializer()
    drink = OrderDrinkSerializer()


class OrderSerializer(serializers.ModelSerializer):
    customer = OrderCustomerSerializer()
    driver = OrderDriverSerializer()
    registration = OrderRegistrationSerializer()
    order_details = OrderDetailsSerializer(many=True)
    status = serializers.ReadOnlyField(source="get_status_display")

    class Meta:
        model = Order
        fields = (
            "id",
            "customer",
            "registration",
            "driver",
            "order_details",
            "total",
            "status",
            "address",
        )
