import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.taxonomy.models import Country, Region, Theme


@pytest.fixture
def verified_user(db):
    user = User.objects.create_user("researcher@example.com", "Str0ng-pass-123")
    user.mark_email_verified()
    return user


@pytest.fixture
def taxonomy_data(db):
    region = Region.objects.create(code="east-africa", name="East Africa")
    Country.objects.create(code="rw", name="Rwanda", region=region)
    Country.objects.create(code="ke", name="Kenya", region=region)
    Theme.objects.create(
        slug="forced-displacement",
        name_en="Forced displacement",
        name_fr="Déplacement forcé",
    )
    return region


@pytest.mark.django_db
def test_taxonomy_requires_verified_user(taxonomy_data):
    client = APIClient()
    response = client.get(reverse("v1:taxonomy:regions"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_verified_user_can_read_active_taxonomy(verified_user, taxonomy_data):
    client = APIClient()
    client.force_authenticate(verified_user)

    response = client.get(reverse("v1:taxonomy:countries"), {"region": "east-africa"})
    assert response.status_code == 200
    assert [country["code"] for country in response.json()] == ["KE", "RW"]

    response = client.get(reverse("v1:taxonomy:themes"))
    assert response.status_code == 200
    assert response.json()[0]["name_fr"] == "Déplacement forcé"


@pytest.mark.django_db
def test_archived_taxonomy_is_not_publicly_returned(verified_user, taxonomy_data):
    Country.objects.filter(code="KE").delete()
    client = APIClient()
    client.force_authenticate(verified_user)

    response = client.get(reverse("v1:taxonomy:countries"))
    assert response.status_code == 200
    assert [country["code"] for country in response.json()] == ["RW"]
