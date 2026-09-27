import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_is_public_and_reports_database(client):
    response = client.get(reverse("v1:core:health"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": True}


def test_api_errors_are_wrapped():
    from rest_framework.exceptions import NotAuthenticated

    from apps.core.exceptions import api_exception_handler

    response = api_exception_handler(NotAuthenticated(), {})
    assert response.data["error"]["code"] == "not_authenticated"
    assert response.data["error"]["details"] is None
