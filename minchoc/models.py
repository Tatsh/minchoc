# pylint: disable=invalid-str-returned,no-member
from typing import Any
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
import django_stubs_ext

django_stubs_ext.monkeypatch()

__all__ = ('Author', 'Company', 'NugetUser', 'Package', 'PackageVersionDownloadCount')


class Company(models.Model):
    class Meta:
        verbose_name = 'company'
        verbose_name_plural = 'companies'

    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class NugetUser(models.Model):
    """Can be owners of the nuget spec."""
    base = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)  # type: ignore[var-annotated]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    token = models.UUIDField()

    def __str__(self):
        return self.base.username


def post_save_receiver(
        sender: AbstractUser,  # pylint: disable=unused-argument
        instance: AbstractUser,
        **kwargs: Any) -> None:
    if not NugetUser.objects.filter(base=instance).exists():
        nuget_user = NugetUser()
        nuget_user.base = instance
        nuget_user.token = uuid.uuid4()
        nuget_user.save()


post_save.connect(post_save_receiver, sender=settings.AUTH_USER_MODEL)


class PackageVersionDownloadCount(models.Model):
    count = models.PositiveBigIntegerField()
    version = models.CharField(max_length=128)

    def __str__(self):
        s = '1 download' if self.count == 1 else f'{self.count} downloads'
        return f'{self.version}: {s}'


class Author(models.Model):
    """Author of the software, not the nuget spec."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self) -> str:
        return self.name


class Package(models.Model):
    class Meta:
        unique_together = (('nuget_id', 'version'))

    authors = models.ManyToManyField(Author)  # type: ignore[var-annotated]
    copyright = models.TextField(null=True)
    dependencies = models.JSONField(null=True)
    description = models.TextField(null=True)
    download_count = models.PositiveBigIntegerField(default=0)
    file = models.FileField(upload_to='packages')
    hash = models.TextField(null=True)
    hash_algorithm = models.CharField(max_length=32, null=True)
    icon_url = models.URLField(null=True)
    is_absolute_latest_version = models.BooleanField(default=True)
    is_latest_version = models.BooleanField(default=True)
    is_prerelease = models.BooleanField(default=False)
    license_url = models.URLField(null=True)
    listed = models.BooleanField(default=True)
    nuget_id = models.CharField(max_length=128)
    project_url = models.URLField()
    published = models.DateTimeField(auto_now_add=True, blank=True)
    references = models.JSONField(default=dict)  # type: ignore[var-annotated]
    release_notes = models.TextField(null=True)
    require_license_acceptance = models.BooleanField(default=False)
    size = models.PositiveIntegerField()
    source_url = models.URLField(null=True)
    summary = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)  # type: ignore[var-annotated]
    title = models.CharField(max_length=255)
    uploader = models.ForeignKey(NugetUser, on_delete=models.CASCADE)
    version = models.CharField(max_length=128)
    version0 = models.PositiveIntegerField()
    version1 = models.PositiveIntegerField()
    version2 = models.PositiveIntegerField(null=True)
    version3 = models.PositiveIntegerField(null=True)
    version_beta = models.CharField(max_length=128, null=True)
    version_download_count = models.ManyToManyField(PackageVersionDownloadCount)

    def __str__(self) -> str:
        return f'{self.title} {self.version}'
