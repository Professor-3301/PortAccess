from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from .models import User, UserToken, ServerOwnerProfile, PentesterProfile, Server, AccessRequest 
import uuid
from rest_framework.authtoken.models import Token
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

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
    """ View to list all registered servers (Only for authenticated pentesters) """
    permission_classes = [AllowAny]  # We manually handle authentication

    def get(self, request):
        # Extract the token from headers
        token = request.headers.get("Authorization")

        if not token:
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        # Handle "Token <actual_token>" or "Bearer <actual_token>"
        token_parts = token.split()
        if len(token_parts) != 2 or token_parts[0] not in ["Token", "Bearer"]:
            return Response({"error": "Invalid token format."}, status=status.HTTP_401_UNAUTHORIZED)

        actual_token = token_parts[1]  # Extract the real token

        print(f"🔍 Received Token: {actual_token}")  # Debugging step

        # Check if token exists in the database
        user_token = UserToken.objects.filter(token=actual_token).first()
        if not user_token:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        user = user_token.user

        # Ensure the user is a pentester
        if not hasattr(user, "role") or user.role != "pentester":
            return Response({"error": "Access denied. Only pentesters can view servers."}, status=status.HTTP_403_FORBIDDEN)

        # Retrieve all servers
        servers = Server.objects.all()
        if not servers.exists():
            return Response({"error": "No servers available."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize server list
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

    permission_classes = [AllowAny]  # We handle authentication manually

    def get_client_ip(self, request):
        """ Extracts the public IP address of the client """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]  # Get the first IP if multiple exist
        else:
            ip = request.META.get("REMOTE_ADDR")  # Get direct IP if no proxy
        return ip

    def post(self, request):
        # Extract the token from headers
        token = request.headers.get("Authorization")

        if not token:
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        # Handle "Token <actual_token>" or "Bearer <actual_token>"
        token_parts = token.split()
        if len(token_parts) != 2 or token_parts[0] not in ["Token", "Bearer"]:
            return Response({"error": "Invalid token format."}, status=status.HTTP_401_UNAUTHORIZED)

        actual_token = token_parts[1]  # Extract the real token
        print(f"🔍 Received Token: {actual_token}")  # Debugging

        # Check if token exists in the database
        user_token = UserToken.objects.filter(token=actual_token).first()
        if not user_token:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        pentester = user_token.user

        # Ensure the user is a pentester
        if not hasattr(pentester, "role") or pentester.role != "pentester":
            return Response({"error": "Access denied. Only pentesters can request access."}, status=status.HTTP_403_FORBIDDEN)

        # Get server_id from request
        server_id = request.data.get('server_id')
        if not server_id:
            return Response({"error": "Server ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the server
        server = get_object_or_404(Server, id=server_id)

        # Check for existing pending request
        if AccessRequest.objects.filter(pentester=pentester, server=server, status='pending').exists():
            return Response({"error": "You already have a pending request for this server"}, status=status.HTTP_400_BAD_REQUEST)

        # Get pentester's public IP
        pentester_ip = self.get_client_ip(request)
        print(f"🌍 Pentester IP: {pentester_ip}")  # Debugging

        # Create and save the access request
        access_request = AccessRequest.objects.create(
            pentester=pentester,
            server=server,
            pentester_ip=pentester_ip  # Store IP in the model
        )

        return Response(
            {
                "message": "Access request sent successfully",
                "request_id": access_request.id,
                "server": {"id": server.id, "name": server.name, "ip_address": server.ip_address},
                "pentester_ip": pentester_ip,  # Return the captured IP
                "status": access_request.status
            },
            status=status.HTTP_201_CREATED
        )

class AccessRequestListView(APIView):
    """ View to list access requests for a server (owner) or a pentester """

    permission_classes = [AllowAny]  # Now allows all users to access, but token is still required

    def get(self, request):
        """ Retrieve only the access requests made by the authenticated pentester """
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split("Bearer ")[1]  # Extract actual token

        # Verify token
        try:
            user_token = UserToken.objects.get(token=token)
            user = user_token.user
        except UserToken.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Retrieve only the requests made by the authenticated pentester
        access_requests = AccessRequest.objects.filter(pentester=user)

        if not access_requests.exists():
            return Response({"message": "No access requests found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize request data
        request_list = [
            {
                "request_id": req.id,
                "server_name": req.server.name,
                "status": req.status,
                "requested_at": req.requested_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for req in access_requests
        ]

        return Response(request_list, status=status.HTTP_200_OK)
    

class ServerAccessRequestView(APIView):
    """ View for server owners to see and manage access requests made to their servers """

    permission_classes = [AllowAny]  # Open endpoint, but requires authentication via token

    def get(self, request, server_id):
        """ Server owners can view all access requests made to their server """
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split("Bearer ")[1]  # Extract actual token

        # Verify token
        try:
            user_token = UserToken.objects.get(token=token)
            user = user_token.user
        except UserToken.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the server exists and if the user is the owner
        server = get_object_or_404(Server, id=server_id)

        if server.owner != user:
            return Response({"error": "Access denied. Only the server owner can view requests."}, status=status.HTTP_403_FORBIDDEN)

        # Get access requests for this server
        access_requests = AccessRequest.objects.filter(server=server)

        if not access_requests.exists():
            return Response({"message": "No access requests found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize request data
        request_list = [
            {
                "request_id": req.id,
                "pentester": req.pentester.username,
                "status": req.status,  # Now matches ('pending', 'approved', 'rejected')
                "requested_at": req.requested_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for req in access_requests
        ]

        return Response(request_list, status=status.HTTP_200_OK)

    def patch(self, request, server_id, request_id):
        """ Server owner can approve or reject an access request """
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split("Bearer ")[1]  # Extract actual token

        # Verify token
        try:
            user_token = UserToken.objects.get(token=token)
            user = user_token.user
        except UserToken.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the server exists and if the user is the owner
        server = get_object_or_404(Server, id=server_id)

        if server.owner != user:
            return Response({"error": "Access denied. Only the server owner can manage requests."}, status=status.HTTP_403_FORBIDDEN)

        # Get the specific access request
        access_request = get_object_or_404(AccessRequest, id=request_id, server=server)

        # Get action from request body
        action = request.data.get("action")

        if action not in ["approve", "reject"]:
            return Response({"error": "Invalid action. Use 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)

        # Update request status to match model choices
        access_request.status = "approved" if action == "approve" else "rejected"
        access_request.save()

        return Response({"message": f"Request {action}d successfully."}, status=status.HTTP_200_OK)
    

class ServerOwnerAccessRequestView(APIView):
    """View for server owners to manage and verify pentester access requests"""

    permission_classes = [AllowAny]  # Requires authentication via token

    def get(self, request, server_id):
        """Server owner can view all access requests along with pentester details"""
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split("Bearer ")[1]  # Extract actual token

        # Verify token
        try:
            user_token = UserToken.objects.get(token=token)
            user = user_token.user
        except UserToken.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the server exists and if the user is the owner
        server = get_object_or_404(Server, id=server_id)

        if server.owner != user:
            return Response({"error": "Access denied. Only the server owner can view requests."}, status=status.HTTP_403_FORBIDDEN)

        # Get all access requests for this server
        access_requests = AccessRequest.objects.filter(server=server)

        if not access_requests.exists():
            return Response({"message": "No access requests found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize request data with pentester details and IP
        request_list = []
        for req in access_requests:
            pentester_profile = PentesterProfile.objects.filter(user=req.pentester).first()
            
            pentester_data = {
                "username": req.pentester.username,
                "aadhar_or_ssn": pentester_profile.aadhar_or_ssn if pentester_profile else None,
                "contact_no": pentester_profile.contact_no if pentester_profile else None,
                "experience": pentester_profile.experience if pentester_profile else None,
                "certifications": pentester_profile.certifications if pentester_profile else None,
            } if pentester_profile else {}

            request_list.append({
                "request_id": req.id,
                "status": req.status,
                "requested_at": req.requested_at.strftime("%Y-%m-%d %H:%M:%S"),
                "pentester": pentester_data,
                "pentester_ip": req.pentester_ip,  # Include pentester IP
            })

        return Response(request_list, status=status.HTTP_200_OK)

    def patch(self, request, server_id, request_id):
        """Server owner can approve or reject an access request"""
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split("Bearer ")[1]  # Extract actual token

        # Verify token
        try:
            user_token = UserToken.objects.get(token=token)
            user = user_token.user
        except UserToken.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the server exists and if the user is the owner
        server = get_object_or_404(Server, id=server_id)

        if server.owner != user:
            return Response({"error": "Access denied. Only the server owner can manage requests."}, status=status.HTTP_403_FORBIDDEN)

        # Get the specific access request
        access_request = get_object_or_404(AccessRequest, id=request_id, server=server)

        # Get action from request body
        action = request.data.get("action")

        if action not in ["approve", "reject"]:
            return Response({"error": "Invalid action. Use 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)

        # Update request status
        access_request.status = "approved" if action == "approve" else "rejected"
        access_request.save()

        return Response({
            "message": f"Request {action}d successfully.",
            "pentester_ip": access_request.pentester_ip  # Include pentester IP in response
        }, status=status.HTTP_200_OK)
    

class ChangeServerOwnerPasswordView(APIView):
    """
    Allows a server owner to change their password.
    """

    def post(self, request):
        """ Server owner can change their password by providing the old one """
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split("Bearer ")[1]  # Extract actual token

        # Verify token
        try:
            user_token = UserToken.objects.get(token=token)
            user = user_token.user  # Extract authenticated user
        except UserToken.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Get old and new passwords from request data
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        # Validate old password
        if not check_password(old_password, user.password):
            return Response({"error": "Incorrect old password."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate new password length
        if len(new_password) < 6:
            return Response({"error": "New password must be at least 6 characters long."}, status=status.HTTP_400_BAD_REQUEST)

        # Update password
        user.password = make_password(new_password)
        user.save()

        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

class ChangePentesterPasswordView(APIView):
    """
    Allows a pentester to change their password.
    """

    def post(self, request):
        """ Pentester can change their password by providing the old one """
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split("Bearer ")[1]  # Extract actual token

        # Verify token
        try:
            user_token = UserToken.objects.get(token=token)
            user = user_token.user  # Extract authenticated user
        except UserToken.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Get old and new passwords from request data
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        # Validate old password
        if not check_password(old_password, user.password):
            return Response({"error": "Incorrect old password."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate new password length
        if len(new_password) < 6:
            return Response({"error": "New password must be at least 6 characters long."}, status=status.HTTP_400_BAD_REQUEST)

        # Update password
        user.password = make_password(new_password)
        user.save()

        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)


class ServerOwnerDetailsView(APIView):
    """View to retrieve details of the currently logged-in server owner"""
    permission_classes = [AllowAny]  # We manually handle authentication

    def get(self, request):
        # Extract the token from headers
        token = request.headers.get("Authorization")

        if not token:
            return Response({"error": "Authentication token required."}, status=status.HTTP_401_UNAUTHORIZED)

        # Handle "Token <actual_token>" or "Bearer <actual_token>"
        token_parts = token.split()
        if len(token_parts) != 2 or token_parts[0] not in ["Token", "Bearer"]:
            return Response({"error": "Invalid token format."}, status=status.HTTP_401_UNAUTHORIZED)

        actual_token = token_parts[1]  # Extract the real token

        print(f"🔍 Received Token: {actual_token}")  # Debugging step

        # Check if token exists in the database
        user_token = UserToken.objects.filter(token=actual_token).first()
        if not user_token:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)

        user = user_token.user

        # Ensure the user is a server owner
        server_owner = ServerOwnerProfile.objects.filter(user=user).first()
        if not server_owner:
            return Response({"error": "Access denied. Only server owners can view their details."}, status=status.HTTP_403_FORBIDDEN)

        # Serialize the server owner's details
        owner_data = {
            "id": server_owner.id,
            "username": server_owner.user.username,
            "email": server_owner.user.email,
            "ip": server_owner.ip,
            "name": server_owner.name,
            "domain": server_owner.domain
        }

        return Response(owner_data, status=status.HTTP_200_OK)