from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer
from users.models import CustomUser

# Create your views here.
class UserListView(APIView):
    def get_permissions(self):
        """
        Allow unauthenticated access for POST (user creation),
        but require authentication for GET (listing users).
        """
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]
    @swagger_auto_schema(
        operation_description="Retrieve a list of all active users",
        operation_summary="List all active users",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request):
        """
        Get all active users in the system.
        """
        users = CustomUser.objects.filter(is_active=True)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create a new user",
        operation_summary="Create user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role (admin, analyst, viewer)'),
                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is staff'),
            },
            required=['username', 'email', 'password']
        ),
        responses={201: UserSerializer(), 400: openapi.Response('Bad request')}
    )
    def post(self, request):
        """
        Create a new user.
        """
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            role = request.data.get('role', 'viewer')
            is_staff = request.data.get('is_staff', False)

            # Validate required fields
            if not username or not email or not password:
                return Response({'error': 'username, email, and password are required'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if user already exists
            if CustomUser.objects.filter(username=username).exists():
                return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

            if CustomUser.objects.filter(email=email).exists():
                return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

            # Create user
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_staff=is_staff
            )

            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Retrieve a specific user by ID",
        operation_summary="Get user details",
        responses={200: UserSerializer(), 404: openapi.Response('User not found')}
    )
    def get(self, request, user_id):
        """
        Get a specific user by ID (only if active).
        """
        try:
            user = CustomUser.objects.get(id=user_id, is_active=True)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update a user (full update)",
        operation_summary="Update user details",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role (admin, analyst, viewer)'),
                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is staff'),
            },
            required=['username', 'email']
        ),
        responses={200: UserSerializer(), 404: openapi.Response('User not found'), 400: openapi.Response('Bad request')}
    )
    def put(self, request, user_id):
        """
        Update a user (full update).
        """
        try:
            user = CustomUser.objects.get(id=user_id, is_active=True)

            # Update fields
            if 'username' in request.data:
                # Check if username is already taken
                if CustomUser.objects.filter(username=request.data['username']).exclude(id=user_id).exists():
                    return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
                user.username = request.data['username']

            if 'email' in request.data:
                # Check if email is already taken
                if CustomUser.objects.filter(email=request.data['email']).exclude(id=user_id).exists():
                    return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
                user.email = request.data['email']

            if 'password' in request.data:
                user.set_password(request.data['password'])

            if 'first_name' in request.data:
                user.first_name = request.data['first_name']

            if 'last_name' in request.data:
                user.last_name = request.data['last_name']

            if 'role' in request.data:
                user.role = request.data['role']

            if 'is_staff' in request.data:
                user.is_staff = request.data['is_staff']

            user.save()
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Partially update a user",
        operation_summary="Partial update user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role (admin, analyst, viewer)'),
                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is staff'),
            }
        ),
        responses={200: UserSerializer(), 404: openapi.Response('User not found'), 400: openapi.Response('Bad request')}
    )
    def patch(self, request, user_id):
        """
        Partially update a user.
        """
        try:
            user = CustomUser.objects.get(id=user_id, is_active=True)

            # Update fields if provided
            if 'username' in request.data:
                if CustomUser.objects.filter(username=request.data['username']).exclude(id=user_id).exists():
                    return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
                user.username = request.data['username']

            if 'email' in request.data:
                if CustomUser.objects.filter(email=request.data['email']).exclude(id=user_id).exists():
                    return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
                user.email = request.data['email']

            if 'password' in request.data:
                user.set_password(request.data['password'])

            if 'first_name' in request.data:
                user.first_name = request.data['first_name']

            if 'last_name' in request.data:
                user.last_name = request.data['last_name']

            if 'role' in request.data:
                user.role = request.data['role']

            if 'is_staff' in request.data:
                user.is_staff = request.data['is_staff']

            user.save()
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Deactivate a user (soft delete)",
        operation_summary="Deactivate user",
        responses={204: openapi.Response('User deactivated'), 404: openapi.Response('User not found')}
    )
    def delete(self, request, user_id):
        """
        Deactivate a user (soft delete - sets is_active to False).
        """
        try:
            user = CustomUser.objects.get(id=user_id, is_active=True)
            user.is_active = False
            user.save()
            return Response({'message': 'User deactivated successfully'}, status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class UserInactiveListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all inactive users",
        operation_summary="List inactive users",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request):
        """
        Get all inactive (deactivated) users in the system.
        """
        users = CustomUser.objects.filter(is_active=False)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserReactivateView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Reactivate an inactive user",
        operation_summary="Reactivate user",
        responses={200: UserSerializer(), 404: openapi.Response('User not found')}
    )
    def post(self, request, user_id):
        """
        Reactivate an inactive user back to active status.
        """
        try:
            user = CustomUser.objects.get(id=user_id, is_active=False)
            user.is_active = True
            user.save()
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Inactive user not found'}, status=status.HTTP_404_NOT_FOUND)


class UserLoginView(APIView):
    """
    JWT Login endpoint.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Login with username and password to get JWT tokens",
        operation_summary="User login",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            },
            required=['username', 'password']
        ),
        responses={
            200: openapi.Response('Login successful'),
            401: openapi.Response('Invalid credentials'),
            400: openapi.Response('Bad request')
        }
    )
    def post(self, request):
        """
        Login with username and password to get JWT tokens.
        """
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            if not username or not password:
                return Response(
                    {'error': 'username and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Authenticate user
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)

            if user is None:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not user.is_active:
                return Response(
                    {'error': 'User account is inactive'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Generate tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(APIView):
    """
    Get current user profile.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get current user profile",
        operation_summary="Get user profile",
        responses={200: UserSerializer(), 401: openapi.Response('Unauthorized')}
    )
    def get(self, request):
        """
        Get the profile of the currently authenticated user.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update current user profile",
        operation_summary="Update user profile",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='New password (optional)'),
            }
        ),
        responses={200: UserSerializer(), 400: openapi.Response('Bad request')}
    )
    def put(self, request):
        """
        Update the profile of the currently authenticated user.
        """
        try:
            user = request.user

            if 'first_name' in request.data:
                user.first_name = request.data['first_name']

            if 'last_name' in request.data:
                user.last_name = request.data['last_name']

            if 'email' in request.data:
                # Check if email is already taken
                if CustomUser.objects.filter(email=request.data['email']).exclude(id=user.id).exists():
                    return Response(
                        {'error': 'Email already exists'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user.email = request.data['email']

            if 'password' in request.data:
                user.set_password(request.data['password'])

            user.save()
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )