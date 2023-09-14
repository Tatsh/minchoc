from django.urls import path

from . import views

__all__ = ('urlpatterns',)

# https://learn.microsoft.com/en-us/nuget/api/package-publish-resource
urlpatterns = [
    path('$metadata', views.metadata),
    path('FindPackagesById()', views.find_packages_by_id),
    path('Packages()', views.packages),
    path("Packages(Id='<name>',Version='<version>')", views.packages_with_args),
    path('api/v2/$metadata', views.metadata),
    path('api/v2/package/<name>/<version>', views.fetch_package_file),
    path('api/v2/package/', views.APIV2PackageView.as_view()),
    path('', views.home)
]
