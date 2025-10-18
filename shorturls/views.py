from django.shortcuts import render
from .serializers import ShortURLSerializer,NamespaceSerializer
from rest_framework.views import APIView
from rest_framework import permissions,status
from rest_framework.response import Response
from hirethon_template.users.models import Namespace,ShortURL,Membership
# Create your views here.

class NamespaceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, organization_id=None):
        """
        List all namespaces for an organization (members only) 
        or get details of a specific namespace.
        """
        user = request.user

        if organization_id:
            # Check if user is a member of this organization
            if not Membership.objects.filter(user=user, organization_id=organization_id).exists():
                return Response({"error": "You are not a member of this organization."},
                                status=status.HTTP_403_FORBIDDEN)

            namespaces = Namespace.objects.filter(organization_id=organization_id)
        else:
            # List namespaces of all organizations the user belongs to
            memberships = Membership.objects.filter(user=user)
            org_ids = memberships.values_list("organization_id", flat=True)
            namespaces = Namespace.objects.filter(organization_id__in=org_ids)

        serializer = NamespaceSerializer(namespaces, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, organization_id):
        """
        Create a new namespace within an organization (Admin or Editor)
        """
        user = request.user

        # Check if user is Admin or Editor in this organization
        membership = Membership.objects.filter(
            user=user, 
            organization_id=organization_id, 
            role__in=["Admin", "Editor"]
        ).first()
        if not membership:
            return Response({"error": "Only Admins or Editors can create namespaces."},
                            status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data["organization"] = organization_id
        serializer = NamespaceSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            namespace = serializer.save()
            return Response(NamespaceSerializer(namespace).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, name):
        """
        Update a namespace (Admin or Editor)
        """
        user = request.user
        try:
            namespace = Namespace.objects.get(name=name)
        except Namespace.DoesNotExist:
            return Response({"error": "Namespace not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check Admin or Editor role
        membership = Membership.objects.filter(
            user=user, 
            organization=namespace.organization, 
            role__in=["Admin", "Editor"]
        ).first()
        if not membership:
            return Response({"error": "Only Admins or Editors can update this namespace."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = NamespaceSerializer(namespace, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, name):
        """
        Delete a namespace (Admin or Editor)
        """
        user = request.user
        try:
            namespace = Namespace.objects.get(name=name)
        except Namespace.DoesNotExist:
            return Response({"error": "Namespace not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check Admin or Editor role
        membership = Membership.objects.filter(
            user=user, 
            organization=namespace.organization, 
            role__in=["Admin", "Editor"]
        ).first()
        if not membership:
            return Response({"error": "Only Admins or Editors can delete this namespace."},
                            status=status.HTTP_403_FORBIDDEN)

        namespace.delete()
        return Response({"success": "Namespace deleted."}, status=status.HTTP_200_OK)
    

class ShortURLView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, namespace_name=None):
        """
        List all short URLs in a namespace (members only)
        """
        user = request.user
        try:
            namespace = Namespace.objects.get(name=namespace_name)
        except Namespace.DoesNotExist:
            return Response({"error": "Namespace not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check membership
        if not Membership.objects.filter(user=user, organization=namespace.organization).exists():
            return Response({"error": "You are not a member of this organization."}, status=status.HTTP_403_FORBIDDEN)

        urls = ShortURL.objects.filter(namespace=namespace)
        serializer = ShortURLSerializer(urls, many=True)
        return Response(serializer.data)

    def post(self, request, namespace_name):
        """
        Create a new short URL (Admin or Editor)
        """
        user = request.user
        try:
            namespace = Namespace.objects.get(name=namespace_name)
        except Namespace.DoesNotExist:
            return Response({"error": "Namespace not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check role
        membership = Membership.objects.filter(
            user=user, 
            organization=namespace.organization,
            role__in=["Admin", "Editor"]
        ).first()
        if not membership:
            return Response({"error": "Only Admins or Editors can create short URLs."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data["namespace"] = namespace.id
        serializer = ShortURLSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            short_url = serializer.save()
            return Response(ShortURLSerializer(short_url).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, namespace_name, short_code):
        """
        Update a short URL (Admin or Editor)
        """
        user = request.user
        try:
            namespace = Namespace.objects.get(name=namespace_name)
            short_url = ShortURL.objects.get(namespace=namespace, short_code=short_code)
        except (Namespace.DoesNotExist, ShortURL.DoesNotExist):
            return Response({"error": "Short URL not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check role
        membership = Membership.objects.filter(
            user=user, 
            organization=namespace.organization,
            role__in=["Admin", "Editor"]
        ).first()
        if not membership:
            return Response({"error": "Only Admins or Editors can update this short URL."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ShortURLSerializer(short_url, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, namespace_name, short_code):
        """
        Delete a short URL (Admin or Editor)
        """
        user = request.user
        try:
            namespace = Namespace.objects.get(name=namespace_name)
            short_url = ShortURL.objects.get(namespace=namespace, short_code=short_code)
        except (Namespace.DoesNotExist, ShortURL.DoesNotExist):
            return Response({"error": "Short URL not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check role
        membership = Membership.objects.filter(
            user=user,
            organization=namespace.organization,
            role__in=["Admin", "Editor"]
        ).first()
        if not membership:
            return Response({"error": "Only Admins or Editors can delete this short URL."}, status=status.HTTP_403_FORBIDDEN)

        short_url.delete()
        return Response({"success": "Short URL deleted."}, status=status.HTTP_200_OK)
