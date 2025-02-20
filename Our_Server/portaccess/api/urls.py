from django.urls import path
from .views import *

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('servers/', ServerListView.as_view(), name='server-list'),
    path('request-access/', RequestAccessView.as_view(), name='request-access'),
]
