from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.organizations.permissions import IsVerifiedUser

from .models import Country, Region, Theme
from .serializers import CountrySerializer, RegionSerializer, ThemeSerializer


@extend_schema(tags=["taxonomy"], responses=RegionSerializer(many=True))
@api_view(["GET"])
@permission_classes([IsVerifiedUser])
def regions(request):
    return Response(RegionSerializer(Region.objects.all(), many=True).data)


@extend_schema(tags=["taxonomy"], responses=CountrySerializer(many=True))
@api_view(["GET"])
@permission_classes([IsVerifiedUser])
def countries(request):
    queryset = Country.objects.select_related("region").all()
    region = request.query_params.get("region")
    if region:
        queryset = queryset.filter(region__code=region)
    return Response(CountrySerializer(queryset, many=True).data)


@extend_schema(tags=["taxonomy"], responses=ThemeSerializer(many=True))
@api_view(["GET"])
@permission_classes([IsVerifiedUser])
def themes(request):
    return Response(ThemeSerializer(Theme.objects.all(), many=True).data)
