import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestAccounts:
    # Existing baseline test
    def test_register(self, client):
        resp = client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'district': 'Chennai',
        })
        assert resp.status_code == 302
        assert User.objects.filter(username='newuser').exists()

    def test_login(self, client, user):
        resp = client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        assert resp.status_code == 302

    def test_profile_requires_login(self, client):
        resp = client.get(reverse('accounts:profile'))
        assert resp.status_code == 302

    def test_home_page_requires_login(self, client):
        resp = client.get(reverse('home'))
        assert resp.status_code == 302
        assert reverse('accounts:login') in resp.url

    def test_home_page_accessible_when_authenticated(self, client, user):
        client.force_login(user)
        resp = client.get(reverse('home'))
        assert resp.status_code == 200

    def test_login_redirects_to_home(self, client, user):
        resp = client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        assert resp.status_code == 302
        assert resp.url == reverse('home')

    def test_logout_redirects_to_login(self, client, user):
        client.force_login(user)
        resp = client.post(reverse('accounts:logout'))
        assert resp.status_code == 302
        assert reverse('accounts:login') in resp.url

    # TEST 1: Register a completely new email -> Registration succeeds
    def test_register_new_email_succeeds(self, client):
        resp = client.post(reverse('accounts:register'), {
            'username': 'freshfarmer',
            'email': 'freshfarmer@agri.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'district': 'Madurai',
        })
        assert resp.status_code == 302
        assert User.objects.filter(email='freshfarmer@agri.com').exists()

    # TEST 2: Register the exact same email again -> Registration rejected
    def test_register_duplicate_exact_email_rejected(self, client):
        # Create initial user
        User.objects.create_user(
            username='original_farmer',
            email='farmer1@agri.com',
            password='Password123!',
            district='Salem',
        )

        # Attempt to register second account with same email
        resp = client.post(reverse('accounts:register'), {
            'username': 'duplicate_farmer',
            'email': 'farmer1@agri.com',
            'password1': 'Password123!',
            'password2': 'Password123!',
            'district': 'Salem',
        })

        assert resp.status_code == 200
        form = resp.context['form']
        assert 'email' in form.errors
        assert 'An account with this email already exists.' in form.errors['email']
        assert not User.objects.filter(username='duplicate_farmer').exists()

    # TEST 3: Register the same email with different capitalization -> Rejected
    def test_register_duplicate_case_insensitive_email_rejected(self, client):
        # Create initial user with lowercase email
        User.objects.create_user(
            username='case_farmer',
            email='agrifarmer@domain.com',
            password='Password123!',
            district='Coimbatore',
        )

        # Attempt to register with uppercase/mixed-case email
        resp = client.post(reverse('accounts:register'), {
            'username': 'another_user',
            'email': 'AGRIFARMER@DOMAIN.COM',
            'password1': 'Password123!',
            'password2': 'Password123!',
            'district': 'Coimbatore',
        })

        assert resp.status_code == 200
        form = resp.context['form']
        assert 'email' in form.errors
        assert 'An account with this email already exists.' in form.errors['email']
        assert not User.objects.filter(username='another_user').exists()

    # TEST 4: Verify that only ONE user record exists after duplicate registration attempts
    def test_only_one_user_record_after_duplicate_attempts(self, client):
        User.objects.create_user(
            username='first_user',
            email='single_record@agri.com',
            password='Password123!',
        )

        # Attempt 1: exact duplicate
        client.post(reverse('accounts:register'), {
            'username': 'attempt1',
            'email': 'single_record@agri.com',
            'password1': 'Pass123!aa',
            'password2': 'Pass123!aa',
        })

        # Attempt 2: mixed case duplicate
        client.post(reverse('accounts:register'), {
            'username': 'attempt2',
            'email': 'SINGLE_RECORD@AGRI.COM',
            'password1': 'Pass123!bb',
            'password2': 'Pass123!bb',
        })

        # Check user count with this email
        matching_users = User.objects.filter(email__iexact='single_record@agri.com')
        assert matching_users.count() == 1
        assert matching_users.first().username == 'first_user'

    # TEST 5: Verify that the original user's account information is not modified
    def test_original_user_info_not_modified_on_duplicate_attempt(self, client):
        original = User.objects.create_user(
            username='untouched_user',
            email='untouched@agri.com',
            password='OriginalPassword123!',
            district='Thanjavur',
            village='Papanasam',
            phone='9876543210',
        )

        client.post(reverse('accounts:register'), {
            'username': 'hacker_user',
            'email': 'untouched@agri.com',
            'password1': 'NewPassword999!',
            'password2': 'NewPassword999!',
            'district': 'Madurai',
            'village': 'DifferentVillage',
            'phone': '1234567890',
        })

        refreshed = User.objects.get(id=original.id)
        assert refreshed.username == 'untouched_user'
        assert refreshed.email == 'untouched@agri.com'
        assert refreshed.district == 'Thanjavur'
        assert refreshed.village == 'Papanasam'
        assert refreshed.phone == '9876543210'
        # Verify original password still validates
        assert refreshed.check_password('OriginalPassword123!')

    # TEST 6: Verify that normal registration with another unique email still works
    def test_subsequent_unique_registration_works(self, client):
        # Register user 1
        r1 = client.post(reverse('accounts:register'), {
            'username': 'farmer_alpha',
            'email': 'alpha@agri.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'district': 'Erode',
        })
        assert r1.status_code == 302

        # Register user 2 with different unique email
        r2 = client.post(reverse('accounts:register'), {
            'username': 'farmer_beta',
            'email': 'beta@agri.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'district': 'Tirunelveli',
        })
        assert r2.status_code == 302

        assert User.objects.filter(email='alpha@agri.com').count() == 1
        assert User.objects.filter(email='beta@agri.com').count() == 1
