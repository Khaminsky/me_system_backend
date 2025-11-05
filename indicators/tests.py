from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from surveys.models import Survey, SurveyData
from indicators.models import Indicator, IndicatorValue, IndicatorTarget
import json

User = get_user_model()


class IndicatorComputationViewTests(TestCase):
    """Test cases for IndicatorComputationView"""

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

        # Create a survey with numeric data
        self.survey = Survey.objects.create(
            name='Test Survey',
            description='Test Description',
            uploaded_by=self.analyst_user,
            file='test.csv'
        )

        # Add survey data
        test_data = [
            {'region': 'North', 'cases': 100, 'recovered': 80},
            {'region': 'South', 'cases': 150, 'recovered': 120},
            {'region': 'East', 'cases': 120, 'recovered': 100},
            {'region': 'West', 'cases': 130, 'recovered': 110},
        ]
        for data in test_data:
            SurveyData.objects.create(survey=self.survey, data=data)

        # Create indicators
        self.count_indicator = Indicator.objects.create(
            name='Total Cases',
            description='Count of all cases',
            formula='COUNT(cases)',
            indicator_type='count',
            created_by=self.analyst_user,
            is_active=True
        )

        self.sum_indicator = Indicator.objects.create(
            name='Total Recovered',
            description='Sum of recovered cases',
            formula='SUM(recovered)',
            indicator_type='sum',
            created_by=self.analyst_user,
            is_active=True
        )

        self.avg_indicator = Indicator.objects.create(
            name='Average Cases',
            description='Average cases per region',
            formula='AVG(cases)',
            indicator_type='average',
            created_by=self.analyst_user,
            is_active=True
        )

    def test_compute_single_indicator(self):
        """Test computing a single indicator"""
        data = {
            'indicator_ids': [self.count_indicator.id]
        }
        response = self.client.post(
            f'/api/indicators/compute/{self.survey.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_compute_multiple_indicators(self):
        """Test computing multiple indicators"""
        data = {
            'indicator_ids': [
                self.count_indicator.id,
                self.sum_indicator.id,
                self.avg_indicator.id
            ]
        }
        response = self.client.post(
            f'/api/indicators/compute/{self.survey.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_compute_creates_indicator_values(self):
        """Test that computation creates IndicatorValue records"""
        data = {
            'indicator_ids': [self.count_indicator.id]
        }
        response = self.client.post(
            f'/api/indicators/compute/{self.survey.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify IndicatorValue was created
        indicator_values = IndicatorValue.objects.filter(
            indicator=self.count_indicator,
            survey=self.survey
        )
        self.assertEqual(indicator_values.count(), 1)

    def test_compute_nonexistent_survey_returns_404(self):
        """Test computation on non-existent survey"""
        data = {'indicator_ids': [self.count_indicator.id]}
        response = self.client.post(
            '/api/indicators/compute/9999/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_compute_unauthenticated_returns_401(self):
        """Test that unauthenticated computation returns 401"""
        self.client.force_authenticate(user=None)
        data = {'indicator_ids': [self.count_indicator.id]}
        response = self.client.post(
            f'/api/indicators/compute/{self.survey.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_viewer_cannot_compute_indicators(self):
        """Test that viewers cannot compute indicators"""
        self.client.force_authenticate(user=self.viewer_user)
        data = {'indicator_ids': [self.count_indicator.id]}
        response = self.client.post(
            f'/api/indicators/compute/{self.survey.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_compute_with_filter_criteria(self):
        """Test computing indicator with filter criteria"""
        # Create indicator with filter criteria
        filtered_indicator = Indicator.objects.create(
            name='North Cases',
            description='Cases in North region',
            formula='COUNT(cases)',
            indicator_type='count',
            filter_criteria={'region': 'North'},
            created_by=self.analyst_user,
            is_active=True
        )

        data = {
            'indicator_ids': [filtered_indicator.id]
        }
        response = self.client.post(
            f'/api/indicators/compute/{self.survey.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class IndicatorViewSetTests(TestCase):
    """Test cases for IndicatorViewSet"""

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

    def test_create_indicator(self):
        """Test creating an indicator"""
        data = {
            'name': 'Test Indicator',
            'description': 'Test Description',
            'formula': 'SUM(value)',
            'indicator_type': 'sum'
        }
        response = self.client.post('/api/indicators/indicators/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Indicator')

    def test_list_indicators(self):
        """Test listing indicators"""
        # Create an indicator first
        Indicator.objects.create(
            name='Test Indicator',
            formula='COUNT(value)',
            indicator_type='count',
            created_by=self.analyst_user
        )

        response = self.client.get('/api/indicators/indicators/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_update_indicator(self):
        """Test updating an indicator"""
        indicator = Indicator.objects.create(
            name='Original Name',
            formula='COUNT(value)',
            indicator_type='count',
            created_by=self.analyst_user
        )

        data = {'name': 'Updated Name'}
        response = self.client.patch(
            f'/api/indicators/indicators/{indicator.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')

    def test_delete_indicator(self):
        """Test deleting an indicator"""
        indicator = Indicator.objects.create(
            name='To Delete',
            formula='COUNT(value)',
            indicator_type='count',
            created_by=self.analyst_user
        )

        response = self.client.delete(f'/api/indicators/indicators/{indicator.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deletion
        self.assertFalse(Indicator.objects.filter(id=indicator.id).exists())
