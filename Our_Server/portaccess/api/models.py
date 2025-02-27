from djongo import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('server_owner', 'Server Owner'),
        ('pentester', 'Pentester')
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)  # Hashed password should be stored
    token = models.CharField(max_length=255, null=True, blank=True)  # Authentication token

    groups = models.ManyToManyField(
        'auth.Group',
        related_name="custom_user_set",  # Unique related_name to prevent conflict
        blank=True
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="custom_permission_set",  # Unique related_name to prevent conflict
        blank=True
    )

    def __str__(self):
        return f"{self.username} - {self.role}"


class ServerOwnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="server_owner_profile")
    ip = models.GenericIPAddressField(null=True, blank=True)  # IP Address of the server owner
    name = models.CharField(max_length=255, null=True, blank=True)  # Full name
    domain = models.CharField(max_length=255, null=True, blank=True)  # Optional domain name

    def __str__(self):
        return f"Server Owner Profile - {self.user.username}"


class PentesterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="pentester_profile")
    aadhar_or_ssn = models.CharField(max_length=50, null=True, blank=True)  # Aadhar (India) or SSN (Other regions)
    contact_no = models.CharField(max_length=15, null=True, blank=True)  # Contact number
    experience = models.IntegerField(null=True, blank=True)  # Years of experience
    certifications = models.TextField(null=True, blank=True)  # Certifications list (comma-separated)

    def __str__(self):
        return f"Pentester Profile - {self.user.username} | Experience: {self.experience} years"


class UserToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)

    def __str__(self):
        return f"Token for {self.user.username}"

class Server(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_servers')
    name = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    domain = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

class AccessRequest(models.Model):
    pentester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pentester_requests')
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='server_requests')
    pentester_ip = models.GenericIPAddressField(null=True, blank=True) 
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('pentester', 'server')

    def __str__(self):
        return f"Request from {self.pentester.username} to {self.server.name} - {self.status}"
