import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAdminPanel:
    def test_admin_requires_staff(self, client, user):
        client.login(username='testuser', password='testpass123')
        resp = client.get(reverse('adminpanel:dashboard'))
        assert resp.status_code == 302

    def test_admin_accessible_by_staff(self, client, user):
        user.is_staff = True
        user.save()
        client.login(username='testuser', password='testpass123')
        resp = client.get(reverse('adminpanel:dashboard'))
        assert resp.status_code == 200
