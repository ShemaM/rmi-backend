from rest_framework import serializers

from .models import Country, Region, Theme


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("code", "name")
        read_only_fields = fields


class CountrySerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)

    class Meta:
        model = Country
        fields = ("code", "name", "region")
        read_only_fields = fields


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = ("slug", "name_en", "name_fr", "description_en", "description_fr")
        read_only_fields = fields
