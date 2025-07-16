from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Vendor, Feature, SubscriptionPlan


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}
        

class VendorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Vendor
        fields = ['user', 'name', 'subscription_plan']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        vendor = Vendor.objects.create(user=user, **validated_data)
        return vendor



class VendorListSerializer(serializers.ModelSerializer):
    subscription_plan = serializers.CharField(source="subscription_plan.name", read_only=True)
    class Meta:
        model = Vendor
        fields = [
            "id", "fullname", "biz_name", "biz_location", "biz_contact", "biz_mail",
            "subscription_plan", "paystack_connected", "subscription_active"
        ]



class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'name', 'description']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    features = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Feature.objects.all()
    )

    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'features']