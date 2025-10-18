# urls.py
from django.urls import path
from .views import OrganizationView, MembershipView, InviteView

urlpatterns = [
    # Organization routes
    path('api/organizations/', OrganizationView.as_view(), name='organization_list_create'),  
    path('api/organizations/<int:org_id>/', OrganizationView.as_view(), name='organization_detail'),  
    # Membership routes
    path('api/organizations/<int:org_id>/members/', MembershipView.as_view(), name='membership_list_create'), 
    path('api/organizations/<int:org_id>/members/<int:user_id>/', MembershipView.as_view(), name='membership_update_delete'), 

    # Invite routes
    path('api/invites/', InviteView.as_view(), name='invite_list'),  
    path('api/invites/<uuid:token>/', InviteView.as_view(), name='invite_accept'),  
]
