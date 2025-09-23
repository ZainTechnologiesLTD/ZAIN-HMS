from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Patient
from .serializers import PatientSerializer, AppointmentSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('last_name', 'first_name')
    serializer_class = PatientSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'blood_type']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    ordering_fields = ['last_name', 'first_name', 'date_of_birth']

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            )
        return queryset

    @action(detail=True, methods=['get'], url_path='appointments')
    def appointments(self, request, pk=None):
        """Retrieve all appointments for a specific patient."""
        patient = self.get_object()
        appointments = patient.appointments.all().order_by('date', 'time')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {'message': 'Patient created successfully.', 'patient': serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(
                {'message': 'Patient updated successfully.', 'patient': serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Patient deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )
