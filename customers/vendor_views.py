from rest_framework import generics
from .models import Vendor
from .serializers import VendorSerializer

class VendorRegisterView(generics.CreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
