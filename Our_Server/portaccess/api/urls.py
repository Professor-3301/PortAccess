from django.urls import path
from .views import *

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('servers/', ServerListView.as_view(), name='server-list'),
    path('request-access/', RequestAccessView.as_view(), name='request-access'),
    path("my-access-requests/", AccessRequestListView.as_view(), name="my-access-requests"),
    path('server/<int:server_id>/access-requests/', ServerOwnerAccessRequestView.as_view(), name='access_requests'),
    path('server/<int:server_id>/access-requests/<int:request_id>/', ServerOwnerAccessRequestView.as_view(), name='manage_access_request'),
]
