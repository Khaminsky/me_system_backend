from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class UserListViewTests(TestCase):
    """Test cases for UserListView"""

    def setUp(self):
        """Set up test client and create test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='analyst'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_only_active_users(self):
        """Test that list view only returns active users"""
        # Create an inactive user
        inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='testpass123',
            is_active=False
        )

        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'testuser')

    def test_create_user(self):
        """Test creating a new user"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'viewer'
        }
        response = self.client.post('/api/users/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        self.assertEqual(response.data['role'], 'viewer')

    def test_create_user_duplicate_username(self):
        """Test that duplicate username is rejected"""
        data = {
            'username': 'testuser',
            'email': 'another@example.com',
            'password': 'pass123'
        }
        response = self.client.post('/api/users/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response.data['error'])

    def test_create_user_duplicate_email(self):
        """Test that duplicate email is rejected"""
        data = {
            'username': 'anotheruser',
            'email': 'test@example.com',
            'password': 'pass123'
        }
        response = self.client.post('/api/users/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response.data['error'])

    def test_create_user_missing_required_fields(self):
        """Test that missing required fields are rejected"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com'
            # Missing password
        }
        response = self.client.post('/api/users/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserDetailViewTests(TestCase):
    """Test cases for UserDetailView"""

    def setUp(self):
        """Set up test client and create test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='analyst'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_user_detail(self):
        """Test retrieving a specific user"""
        response = self.client.get(f'/api/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_get_nonexistent_user_returns_404(self):
        """Test retrieving a non-existent user"""
        response = self.client.get('/api/users/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_inactive_user_returns_404(self):
        """Test that inactive users cannot be retrieved"""
        self.user.is_active = False
        self.user.save()

        response = self.client.get(f'/api/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_update_user(self):
        """Test full update of a user"""
        data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'role': 'admin'
        }
        response = self.client.put(f'/api/users/{self.user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'updateduser')
        self.assertEqual(response.data['email'], 'updated@example.com')
        self.assertEqual(response.data['role'], 'admin')

    def test_patch_partial_update_user(self):
        """Test partial update of a user"""
        data = {'first_name': 'Patched'}
        response = self.client.patch(f'/api/users/{self.user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Patched')
        self.assertEqual(response.data['username'], 'testuser')  # Unchanged

    def test_cannot_update_inactive_user(self):
        """Test that inactive users cannot be updated"""
        self.user.is_active = False
        self.user.save()

        data = {'first_name': 'Updated'}
        response = self.client.put(f'/api/users/{self.user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_user_deactivates_it(self):
        """Test that delete operation deactivates the user"""
        response = self.client.delete(f'/api/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify user is deactivated
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_cannot_delete_inactive_user(self):
        """Test that inactive users cannot be deleted"""
        self.user.is_active = False
        self.user.save()

        response = self.client.delete(f'/api/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserInactiveListViewTests(TestCase):
    """Test cases for UserInactiveListView"""

    def setUp(self):
        """Set up test client and create test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_only_inactive_users(self):
        """Test that inactive list view only returns inactive users"""
        # Create an inactive user
        inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='testpass123',
            is_active=False
        )

        response = self.client.get('/api/users/inactive/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'inactive')


class UserReactivateViewTests(TestCase):
    """Test cases for UserReactivateView"""

    def setUp(self):
        """Set up test client and create test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='testpass123',
            is_active=False
        )

    def test_reactivate_inactive_user(self):
        """Test reactivating an inactive user"""
        response = self.client.post(f'/api/users/{self.inactive_user.id}/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_active'])

        # Verify user is reactivated
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)

    def test_reactivate_active_user_returns_404(self):
        """Test that reactivating an active user returns 404"""
        response = self.client.post(f'/api/users/{self.user.id}/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reactivate_nonexistent_user_returns_404(self):
        """Test that reactivating a non-existent user returns 404"""
        response = self.client.post('/api/users/9999/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
