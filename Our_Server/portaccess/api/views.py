from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from .models import User, UserToken, ServerOwnerProfile, PentesterProfile
import uuid

class SignUpView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role')
        ip = request.data.get('ip', None)
        name = request.data.get('name', None)
        domain = request.data.get('domain', None)
        aadhar_or_ssn = request.data.get('aadhar_or_ssn', None)
        contact_no = request.data.get('contact_no', None)

        if not username or not email or not password or not role:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)

        user = User(username=username, email=email, password=make_password(password), role=role)
        user.save()

        print(f"[*] User {user.username} created with role {role}")  # Debugging print

        # Create profile based on role
        if role == 'server_owner':
            print("[*] Creating ServerOwnerProfile")  # Debugging print
            owner_profile = ServerOwnerProfile.objects.create(user=user, ip=ip, name=name, domain=domain)
            owner_profile.save()
            print(f"[✅] Server Owner Profile created: {owner_profile}")  # Debugging print
        elif role == 'pentester':
            print("[*] Creating PentesterProfile")  # Debugging print
            pentester_profile = PentesterProfile.objects.create(user=user, aadhar_or_ssn=aadhar_or_ssn, contact_no=contact_no)
            pentester_profile.save()
            print(f"[✅] Pentester Profile created: {pentester_profile}")  # Debugging print
        
        try:
            token = str(uuid.uuid4())
            user_token = UserToken.objects.create(user=user, token=token)
            user_token.save()
            print(f"[✅] UserToken created: {user_token.token}")  # Debug
        except Exception as e:
            print(f"[❌] Error creating UserToken: {e}")  # Debug error message
            return Response({'error': 'Failed to generate token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        user_token, created = UserToken.objects.update_or_create(
        user=user,  # Check by user
        defaults={"token": token}  # Update token if exists
)


        return Response({'token': token}, status=status.HTTP_201_CREATED)
    
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = User.objects.filter(email=email).first()
        if user and check_password(password, user.password):
            token = str(uuid.uuid4())  
            user_token, created = UserToken.objects.update_or_create(
                user=user,
                defaults={"token": token}
            )

            return Response({'token': token}, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
