from rest_framework import generics
from .models import Vendor
from .serializers import VendorSerializer, VendorListSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
class VendorRegisterView(generics.CreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer



@api_view(["GET"])
@permission_classes([IsAuthenticated])  # Optional: You can remove if public
def list_vendors(request):
    """
    Returns a list of all vendors and their basic details.
    """
    vendors = Vendor.objects.all()
    serializer = VendorListSerializer(vendors, many=True)
    return Response(serializer.data)