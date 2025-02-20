from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from .models import User, UserToken, ServerOwnerProfile, PentesterProfile, Server, AccessRequest
import uuid
from rest_framework import status

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
        experience = request.data.get('experience', None)
        certifications = request.data.get('certifications', None)

        if not username or not email or not password or not role:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)

        # Create User
        user = User(username=username, email=email, password=make_password(password), role=role)
        user.save()
        print(f"[✅] User created: {user}")

        # Create Profile and Server Entry
        if role == 'server_owner':
            print("[*] Creating ServerOwnerProfile...")
            try:
                owner_profile = ServerOwnerProfile.objects.create(user=user, ip=ip, name=name, domain=domain)
                print(f"[✅] Server Owner Profile created: {owner_profile}")

                # 🔥 **Also add the server to the Server table**
                server = Server.objects.create(
                    owner=user,  # Assuming Server model has an owner field
                    name=name,
                    ip_address=ip,
                    domain=domain
                )
                print(f"[✅] Server added to database: {server}")

            except Exception as e:
                print(f"[❌] Failed to create ServerOwnerProfile or Server: {e}")
                return Response({'error': 'Failed to create server owner profile'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif role == 'pentester':
            print("[*] Creating PentesterProfile...")
            pentester_profile = PentesterProfile.objects.create(
                user=user, 
                aadhar_or_ssn=aadhar_or_ssn, 
                contact_no=contact_no, 
                experience=experience,
                certifications=certifications
            )
            print(f"[✅] Pentester Profile created: {pentester_profile}")

        # Generate Auth Token
        token = str(uuid.uuid4())
        user_token, created = UserToken.objects.update_or_create(user=user, defaults={"token": token})
        print(f"[✅] Token created: {token}")

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

class ServerListView(APIView):
    """ View to list all registered servers """
    def get(self, request):
        servers = Server.objects.all()
        server_list = [
            {
                "id": server.id,
                "name": server.name,
                "ip_address": server.ip_address,
                "domain": server.domain
            }
            for server in servers
        ]
        return Response(server_list, status=status.HTTP_200_OK)

class RequestAccessView(APIView):
    """ View to request access to a server """
    def post(self, request):
        pentester = request.user
        server_id = request.data.get('server_id')

        if not server_id:
            return Response({"error": "Server ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        server = get_object_or_404(Server, id=server_id)

        # Check if a pending request already exists
        if AccessRequest.objects.filter(pentester=pentester, server=server, status='pending').exists():
            return Response({"error": "You already have a pending request for this server"}, status=status.HTTP_400_BAD_REQUEST)

        # Create and save the access request
        access_request = AccessRequest.objects.create(pentester=pentester, server=server)

        return Response(
            {
                "message": "Access request sent successfully",
                "request_id": access_request.id,
                "server": {"id": server.id, "name": server.name, "ip_address": server.ip_address},
                "status": access_request.status
            },
            status=status.HTTP_201_CREATED
        )