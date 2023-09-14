# Generated by Django 4.2.4 on 2023-08-20 02:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True,
                                     primary_key=True,
                                     serialize=False,
                                     verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True,
                                     primary_key=True,
                                     serialize=False,
                                     verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='NugetUser',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True,
                                     primary_key=True,
                                     serialize=False,
                                     verbose_name='ID')),
                ('token', models.UUIDField()),
                ('base',
                 models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                      to=settings.AUTH_USER_MODEL)),
                ('company',
                 models.ForeignKey(null=True,
                                   on_delete=django.db.models.deletion.CASCADE,
                                   to='minchoc.company')),
            ],
        ),
        migrations.CreateModel(
            name='PackageVersionDownloadCount',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True,
                                     primary_key=True,
                                     serialize=False,
                                     verbose_name='ID')),
                ('count', models.PositiveBigIntegerField()),
                ('version', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True,
                                     primary_key=True,
                                     serialize=False,
                                     verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True,
                                     primary_key=True,
                                     serialize=False,
                                     verbose_name='ID')),
                ('copyright', models.TextField(null=True)),
                ('dependencies', models.JSONField(null=True)),
                ('description', models.TextField(null=True)),
                ('download_count', models.PositiveBigIntegerField(default=0)),
                ('file', models.FileField(upload_to='packages')),
                ('hash', models.TextField(null=True)),
                ('hash_algorithm', models.CharField(max_length=32, null=True)),
                ('icon_url', models.URLField(null=True)),
                ('is_absolute_latest_version', models.BooleanField(default=True)),
                ('is_latest_version', models.BooleanField(default=True)),
                ('is_prerelease', models.BooleanField(default=False)),
                ('license_url', models.URLField(null=True)),
                ('listed', models.BooleanField(default=True)),
                ('nuget_id', models.CharField(max_length=128)),
                ('project_url', models.URLField()),
                ('published', models.DateTimeField(auto_now_add=True)),
                ('references', models.JSONField(default=dict)),
                ('release_notes', models.TextField(null=True)),
                ('require_license_acceptance', models.BooleanField(default=False)),
                ('size', models.PositiveIntegerField()),
                ('source_url', models.URLField(null=True)),
                ('summary', models.TextField(null=True)),
                ('title', models.CharField(max_length=255)),
                ('version', models.CharField(max_length=128)),
                ('version0', models.PositiveIntegerField()),
                ('version1', models.PositiveIntegerField()),
                ('version2', models.PositiveIntegerField(null=True)),
                ('version3', models.PositiveIntegerField(null=True)),
                ('version_beta', models.CharField(max_length=128, null=True)),
                ('authors', models.ManyToManyField(to='minchoc.author')),
                ('tags', models.ManyToManyField(to='minchoc.tag')),
                ('uploader',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                   to='minchoc.nugetuser')),
                ('version_download_count',
                 models.ManyToManyField(to='minchoc.packageversiondownloadcount')),
            ],
            options={
                'unique_together': {('nuget_id', 'version')},
            },
        ),
    ]