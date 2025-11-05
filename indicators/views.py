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
            return Response(
                {'error': f'Error computing indicators: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
