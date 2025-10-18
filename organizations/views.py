from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from hirethon_template.users.models import Membership,Organization,User,Invite
from .serializers import OrganizationSerializer,MembershipSerializer,InviteSerializer


class OrganizationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id=None):
        """
        List all organizations the user belongs to, or get details of a specific org
        """
        user = request.user
        if org_id:
            try:
                org = Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

            # Check membership
            if not Membership.objects.filter(user=user, organization=org).exists():
                return Response({"error": "Not a member of this org"}, status=status.HTTP_403_FORBIDDEN)

            serializer = OrganizationSerializer(org)
            return Response(serializer.data)

        else:
            orgs = Organization.objects.filter(members__user=user)
            serializer = OrganizationSerializer(orgs, many=True)
            return Response(serializer.data)

    def post(self, request):
        """
        Create a new organization; the requesting user becomes Admin
        """
        serializer = OrganizationSerializer(data=request.data)
        if serializer.is_valid():
            org = serializer.save()
            # Add the requesting user as Admin
            Membership.objects.create(user=request.user, organization=org, role="Admin")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, org_id):
        """
        Update organization info (Admin only)
        """
        user = request.user
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is Admin
        membership = Membership.objects.filter(user=user, organization=org).first()
        if not membership or membership.role != "Admin":
            return Response({"error": "Only Admin can update the organization"}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrganizationSerializer(org, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, org_id):
        """
        Delete an organization (Admin only)
        """
        user = request.user
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is Admin
        membership = Membership.objects.filter(user=user, organization=org).first()
        if not membership or membership.role != "Admin":
            return Response({"error": "Only Admin can delete the organization"}, status=status.HTTP_403_FORBIDDEN)

        org.delete()
        return Response({"success": "Organization deleted"}, status=status.HTTP_204_NO_CONTENT)


class MembershipView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id):
        """
        List all members of an organization.
        """
        user = request.user
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if requester is a member
        if not Membership.objects.filter(user=user, organization=org).exists():
            return Response({"error": "You are not a member of this organization."},
                            status=status.HTTP_403_FORBIDDEN)

        memberships = Membership.objects.filter(organization=org)
        serializer = MembershipSerializer(memberships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, org_id):
        """
        Invite a user to the organization (Admin only).
        """
        user = request.user
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if requester is Admin
        membership = Membership.objects.filter(user=user, organization=org).first()
        if not membership or membership.role != "Admin":
            return Response({"error": "Only Admin can send invites."},
                            status=status.HTTP_403_FORBIDDEN)

        # Prepare invite data
        data = request.data.copy()
        data["organization"] = org.id

        serializer = InviteSerializer(data=data, context={"organization": org})
        if serializer.is_valid():
            invite = serializer.save()
            return Response({
                "success": "Invite sent successfully.",
                "invite_token": str(invite.token)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, org_id, user_id):
        """
        Update a member’s role (Admin only).
        """
        user = request.user
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        # Verify Admin
        membership = Membership.objects.filter(user=user, organization=org).first()
        if not membership or membership.role != "Admin":
            return Response({"error": "Only Admin can update member roles."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            member = Membership.objects.get(user__id=user_id, organization=org)
        except Membership.DoesNotExist:
            return Response({"error": "Member not found in this organization."},
                            status=status.HTTP_404_NOT_FOUND)

        new_role = request.data.get("role")
        if new_role not in dict(Membership.ROLE_CHOICES):
            return Response({"error": "Invalid role."},
                            status=status.HTTP_400_BAD_REQUEST)

        member.role = new_role
        member.save()
        return Response({"success": "Member role updated."}, status=status.HTTP_200_OK)

    def delete(self, request, org_id, user_id):
        """
        Remove a member from the organization (Admin only).
        """
        user = request.user
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        # Verify Admin
        membership = Membership.objects.filter(user=user, organization=org).first()
        if not membership or membership.role != "Admin":
            return Response({"error": "Only Admin can remove members."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            member = Membership.objects.get(user__id=user_id, organization=org)
        except Membership.DoesNotExist:
            return Response({"error": "Member not found in this organization."},
                            status=status.HTTP_404_NOT_FOUND)

        member.delete()
        return Response({"success": "Member removed from organization."},
                        status=status.HTTP_200_OK)


class InviteView(APIView):
    permissions_classes =[permissions.IsAuthenticated]
    
    def post(self, request,token):
        """
        Accept an invitation to join an organization.
        """
        user = request.user
        try:
            invite = Invite.objects.get(token=token, status="Pending")
        except Invite.DoesNotExist:
            return Response({"error": "Invalid or expired invite token."}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is already a member
        if Membership.objects.filter(user=user, organization=invite.organization).exists():
            return Response({"error": "You are already a member of this organization."}, status=status.HTTP_400_BAD_REQUEST)

        # Create membership
        Membership.objects.create(user=user, organization=invite.organization, role=invite.role)

        # Update invite status
        invite.status = "Accepted"
        invite.accepted_at = timezone.now()
        invite.save()

        return Response({"success": f"You have joined the organization '{invite.organization.name}' as {invite.role}."}, status=status.HTTP_200_OK)