from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import pandas as pd
from .models import Indicator, IndicatorValue, IndicatorTarget
from .serializers import IndicatorSerializer, IndicatorValueSerializer, IndicatorTargetSerializer
from .services import IndicatorComputationService
from surveys.models import Survey, SurveyData
from users.permissions import CanComputeIndicators, CanViewReports


class IndicatorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing M&E indicators.
    """
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [IsAuthenticated, CanComputeIndicators]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        operation_description="List all indicators",
        operation_summary="Get indicators"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class IndicatorValueViewSet(viewsets.ModelViewSet):
    """
    API endpoint for indicator values.
    """
    queryset = IndicatorValue.objects.all()
    serializer_class = IndicatorValueSerializer
    permission_classes = [IsAuthenticated, CanViewReports]

    def perform_create(self, serializer):
        serializer.save(calculated_by=self.request.user)

    @swagger_auto_schema(
        operation_description="Get indicator values for a specific indicator",
        operation_summary="List values by indicator"
    )
    @action(detail=False, methods=['get'])
    def by_indicator(self, request):
        indicator_id = request.query_params.get('indicator_id')
        if not indicator_id:
            return Response({'error': 'indicator_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        values = IndicatorValue.objects.filter(indicator_id=indicator_id)
        serializer = self.get_serializer(values, many=True)
        return Response(serializer.data)


class IndicatorTargetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for indicator targets.
    """
    queryset = IndicatorTarget.objects.all()
    serializer_class = IndicatorTargetSerializer
    permission_classes = [IsAuthenticated, CanComputeIndicators]

    @swagger_auto_schema(
        operation_description="Get targets for a specific indicator",
        operation_summary="List targets by indicator"
    )
    @action(detail=False, methods=['get'])
    def by_indicator(self, request):
        indicator_id = request.query_params.get('indicator_id')
        if not indicator_id:
            return Response({'error': 'indicator_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        targets = IndicatorTarget.objects.filter(indicator_id=indicator_id)
        serializer = self.get_serializer(targets, many=True)
        return Response(serializer.data)


class IndicatorComputationView(APIView):
    """
    API endpoint for computing indicators from survey data.
    """
    permission_classes = [IsAuthenticated, CanComputeIndicators]

    @swagger_auto_schema(
        operation_description="Compute indicators for a specific survey",
        operation_summary="Compute survey indicators",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'indicator_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='List of indicator IDs to compute'
                ),
            },
            required=['indicator_ids']
        ),
        responses={
            200: openapi.Response('Indicators computed successfully'),
            404: openapi.Response('Survey or indicators not found'),
            400: openapi.Response('Error computing indicators')
        }
    )
    def post(self, request, survey_id):
        """
        Compute indicators for a survey.
        """
        try:
            # Get the survey
            survey = Survey.objects.get(id=survey_id)

            # Load survey data
            survey_data = SurveyData.objects.filter(survey=survey).values('data')

            if not survey_data.exists():
                return Response(
                    {'error': 'No data found for this survey'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Convert to DataFrame
            data_list = [item['data'] for item in survey_data]
            df = pd.DataFrame(data_list)

            # Get indicator IDs from request
            indicator_ids = request.data.get('indicator_ids', [])

            if not indicator_ids:
                return Response(
                    {'error': 'indicator_ids required in request body'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get indicators
            indicators = Indicator.objects.filter(id__in=indicator_ids, is_active=True)

            if not indicators.exists():
                return Response(
                    {'error': 'No active indicators found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Compute indicators
            computation_service = IndicatorComputationService(df)
            results = []

            for indicator in indicators:
                result = computation_service.compute_indicator(
                    indicator_name=indicator.name,
                    formula=indicator.formula,
                    filter_criteria=indicator.filter_criteria
                )

                # Save the computed value
                if result['status'] == 'success':
                    IndicatorValue.objects.create(
                        indicator=indicator,
                        survey=survey,
                        value=result['value'],
                        period='Current',
                        calculated_by=request.user
                    )

                results.append(result)

            # Get summary statistics
            summary = computation_service.get_summary_statistics()

            return Response({
                'survey_id': survey_id,
                'survey_name': survey.name,
                'computed_indicators': results,
                'summary_statistics': summary,
                'total_rows_processed': len(df)
            }, status=status.HTTP_200_OK)

        except Survey.DoesNotExist:
            return Response(
                {'error': 'Survey not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"Error computing indicators: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Error computing indicators: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class FormulaValidationView(APIView):
    """
    API endpoint for validating indicator formulas.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Validate an indicator formula syntax",
        operation_summary="Validate formula",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'formula': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Formula to validate (e.g., "COUNT(age) / SUM(total)")'
                ),
                'survey_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Survey ID to validate against (optional)'
                ),
            },
            required=['formula']
        ),
        responses={
            200: openapi.Response('Formula is valid'),
            400: openapi.Response('Formula is invalid')
        }
    )
    def post(self, request):
        """
        Validate a formula string.
        """
        formula = request.data.get('formula', '')
        survey_id = request.data.get('survey_id')

        if not formula:
            return Response(
                {'valid': False, 'error': 'Formula is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # If survey_id provided, validate against actual fields
            if survey_id:
                survey = Survey.objects.get(id=survey_id)
                survey_data = SurveyData.objects.filter(survey=survey).values('data')

                if survey_data.exists():
                    data_list = [item['data'] for item in survey_data]
                    df = pd.DataFrame(data_list)

                    # Try to evaluate the formula
                    computation_service = IndicatorComputationService(df)
                    try:
                        result = computation_service._evaluate_formula(formula, df)
                        return Response({
                            'valid': True,
                            'message': 'Formula is valid',
                            'sample_result': float(result) if result == result else None  # Check for NaN
                        }, status=status.HTTP_200_OK)
                    except Exception as e:
                        return Response({
                            'valid': False,
                            'error': f'Formula evaluation error: {str(e)}'
                        }, status=status.HTTP_400_BAD_REQUEST)

            # Basic syntax validation without data
            # Check for supported functions
            import re
            supported_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'PERCENTAGE']
            function_pattern = r'(' + '|'.join(supported_functions) + r')\s*\('

            if not re.search(function_pattern, formula, re.IGNORECASE):
                return Response({
                    'valid': False,
                    'error': f'Formula must contain at least one supported function: {", ".join(supported_functions)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'valid': True,
                'message': 'Formula syntax appears valid (test with survey data for full validation)'
            }, status=status.HTTP_200_OK)

        except Survey.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Survey not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'valid': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class IndicatorPreviewView(APIView):
    """
    API endpoint for previewing indicator computation on sample data.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Preview indicator computation on sample survey data",
        operation_summary="Preview indicator",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'survey_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Survey ID'
                ),
                'formula': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Formula to compute'
                ),
                'filter_criteria': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Filter criteria (optional)'
                ),
            },
            required=['survey_id', 'formula']
        ),
        responses={
            200: openapi.Response('Preview computed successfully'),
            404: openapi.Response('Survey not found'),
            400: openapi.Response('Error computing preview')
        }
    )
    def post(self, request):
        """
        Preview indicator computation.
        """
        survey_id = request.data.get('survey_id')
        formula = request.data.get('formula', '')
        filter_criteria = request.data.get('filter_criteria', {})

        if not survey_id or not formula:
            return Response(
                {'error': 'survey_id and formula are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the survey
            survey = Survey.objects.get(id=survey_id)

            # Load survey data
            survey_data = SurveyData.objects.filter(survey=survey).values('data')

            if not survey_data.exists():
                return Response(
                    {'error': 'No data found for this survey'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Convert to DataFrame
            data_list = [item['data'] for item in survey_data]
            df = pd.DataFrame(data_list)

            # Compute preview
            computation_service = IndicatorComputationService(df)
            result = computation_service.compute_indicator(
                indicator_name='Preview',
                formula=formula,
                filter_criteria=filter_criteria
            )

            return Response({
                'survey_id': survey_id,
                'survey_name': survey.name,
                'formula': formula,
                'filter_criteria': filter_criteria,
                'result': result,
                'total_records': len(df)
            }, status=status.HTTP_200_OK)

        except Survey.DoesNotExist:
            return Response(
                {'error': 'Survey not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error computing preview: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
