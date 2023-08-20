from django.conf import settings
from django.urls import path

from . import views

__all__ = ('urlpatterns',)

urlpatterns = [
    path('$metadata', views.metadata),
    path('FindPackagesById()', views.find_packages_by_id),
    path('Packages()', views.packages),
    path("Packages(Id='<name>',Version='<version>')", views.packages_with_args),
    path('api/v2/$metadata', views.metadata),
    path('api/v2/package/<name>/<version>', views.fetch_package_file),
    path('api/v2/package/', views.APIV2PackageView.as_view()),
]

if settings.WANT_NUGET_HOME:
    urlpatterns.append(path('', views.home))
