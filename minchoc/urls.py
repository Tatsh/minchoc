"""URL patterns."""
from __future__ import annotations

from django.urls import path

from . import views

__all__ = ('urlpatterns',)

# https://learn.microsoft.com/en-us/nuget/api/package-publish-resource
urlpatterns = [
    path('$metadata', views.metadata),
    path('FindPackagesById()', views.find_packages_by_id),
    path('Packages()', views.packages),
    path("Packages(Id='<name>',Version='<version>')", views.packages_with_args),
    path('package/<name>/<version>', views.fetch_package_file),
    path('package/', views.APIV2PackageView.as_view()),
    path('', views.home)
]
