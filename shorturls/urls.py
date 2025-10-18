    # urls.py
from django.urls import path
from .views import NamespaceView, ShortURLView

urlpatterns = [
        # Namespace routes
        path('namespaces/', NamespaceView.as_view(), name='namespace_list'),  # GET all namespaces for all orgs user belongs to
        path('namespaces/<int:organization_id>/', NamespaceView.as_view(), name='namespace_list_create'),  # GET namespaces of org / POST create namespace
        path('namespaces/<str:name>/update/', NamespaceView.as_view(), name='namespace_update'),  # PUT update namespace
        path('namespaces/<str:name>/delete/', NamespaceView.as_view(), name='namespace_delete'),  # DELETE namespace

        # ShortURL routes
        path('shorturls/<str:namespace_name>/', ShortURLView.as_view(), name='shorturl_list_create'),  # GET all URLs / POST create URL
        path('shorturls/<str:namespace_name>/<str:short_code>/update/', ShortURLView.as_view(), name='shorturl_update'),  # PUT update URL
        path('shorturls/<str:namespace_name>/<str:short_code>/delete/', ShortURLView.as_view(), name='shorturl_delete'),  # DELETE URL
]
