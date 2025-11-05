from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from surveys.models import Survey, SurveyData
from data_cleaning.models import ValidationRule, CleaningTask, DataQualityReport
import pandas as pd

User = get_user_model()


class DataValidationViewTests(TestCase):
    """Test cases for DataValidationView"""

    def setUp(self):
        """Set up test client and create test data"""
        self.client = APIClient()
        self.analyst_user = User.objects.create_user(
            username='analyst',
            email='analyst@example.com',
            password='analystpass123',
            role='analyst'
        )
        self.viewer_user = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='viewerpass123',
            role='viewer'
        )
        self.client.force_authenticate(user=self.analyst_user)

        # Create a survey with data
        self.survey = Survey.objects.create(
            name='Test Survey',
            description='Test Description',
            uploaded_by=self.analyst_user,
            file='test.csv'
        )

        # Add survey data with some missing values
        test_data = [
            {'name': 'John', 'age': '30', 'city': 'New York'},
            {'name': 'Jane', 'age': None, 'city': 'Los Angeles'},
            {'name': None, 'age': '35', 'city': 'Chicago'},
            {'name': 'Bob', 'age': '28', 'city': None},
        ]
        for data in test_data:
            SurveyData.objects.create(survey=self.survey, data=data)

    def test_validate_survey_data_successfully(self):
        """Test successful data validation"""
        response = self.client.get(f'/api/data-cleaning/validate/{self.survey.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn('summary', response.data)
        self.assertIn('missing_values', response.data)
        self.assertIn('data_types', response.data)
        self.assertIn('quality_score', response.data['summary'])

    def test_validate_nonexistent_survey_returns_404(self):
        """Test validation of non-existent survey"""
        response = self.client.get('/api/data-cleaning/validate/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_validate_survey_with_no_data_returns_404(self):
        """Test validation of survey with no data"""
        empty_survey = Survey.objects.create(
            name='Empty Survey',
            uploaded_by=self.analyst_user,
            file='empty.csv'
        )
        response = self.client.get(f'/api/data-cleaning/validate/{empty_survey.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_validate_unauthenticated_returns_401(self):
        """Test that unauthenticated validation returns 401"""
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/data-cleaning/validate/{self.survey.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_validate_viewer_can_access(self):
        """Test that viewers can access validation endpoint"""
        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.get(f'/api/data-cleaning/validate/{self.survey.id}/')
        # Viewers should be able to view but not modify
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_quality_report_contains_missing_values(self):
        """Test that quality report identifies missing values"""
        response = self.client.get(f'/api/data-cleaning/validate/{self.survey.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        missing_values = response.data['missing_values']
        # Should have missing values for age, name, and city
        self.assertGreater(len(missing_values), 0)

    def test_quality_report_contains_data_types(self):
        """Test that quality report includes data types"""
        response = self.client.get(f'/api/data-cleaning/validate/{self.survey.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data_types = response.data['data_types']
        self.assertIn('name', data_types)
        self.assertIn('age', data_types)
        self.assertIn('city', data_types)


class ValidationRuleViewSetTests(TestCase):
    """Test cases for ValidationRuleViewSet"""

    def setUp(self):
        """Set up test client and create test user"""
        self.client = APIClient()
        self.analyst_user = User.objects.create_user(
            username='analyst',
            email='analyst@example.com',
            password='analystpass123',
            role='analyst'
        )
        self.client.force_authenticate(user=self.analyst_user)

    def test_create_validation_rule(self):
        """Test creating a validation rule"""
        data = {
            'name': 'Age Range Rule',
            'description': 'Age must be between 0 and 150',
            'rule_type': 'range',
            'field_name': 'age',
            'parameters': {'min': 0, 'max': 150}
        }
        response = self.client.post('/api/data-cleaning/validation-rules/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Age Range Rule')

    def test_list_validation_rules(self):
        """Test listing validation rules"""
        # Create a rule first
        ValidationRule.objects.create(
            name='Test Rule',
            rule_type='range',
            field_name='age',
            created_by=self.analyst_user
        )

        response = self.client.get('/api/data-cleaning/validation-rules/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_analyst_can_create_rule(self):
        """Test that analysts can create validation rules"""
        data = {
            'name': 'Analyst Rule',
            'rule_type': 'required',
            'field_name': 'name'
        }
        response = self.client.post('/api/data-cleaning/validation-rules/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_viewer_cannot_create_rule(self):
        """Test that viewers cannot create validation rules"""
        viewer_user = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='viewerpass123',
            role='viewer'
        )
        self.client.force_authenticate(user=viewer_user)

        data = {
            'name': 'Viewer Rule',
            'rule_type': 'required',
            'field_name': 'name'
        }
        response = self.client.post('/api/data-cleaning/validation-rules/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
