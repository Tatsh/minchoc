# pylint: disable=no-member
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import re
import zipfile

from defusedxml.ElementTree import parse as parse_xml
from django.conf import settings
from django.core.files import File
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from loguru import logger

from .constants import FEED_XML_POST, FEED_XML_PRE
from .filteryacc import parser as filter_parser
from .models import Author, NugetUser, Package, PackageVersionDownloadCount, Tag

NUSPEC_XSD_URI_PREFIX = '{http://schemas.microsoft.com/packaging/2010/07/nuspec.xsd}'
NUSPEC_FIELD_AUTHORS = f'{NUSPEC_XSD_URI_PREFIX}authors'
NUSPEC_FIELD_DESCRIPTION = f'{NUSPEC_XSD_URI_PREFIX}description'
NUSPEC_FIELD_ID = f'{NUSPEC_XSD_URI_PREFIX}id'
NUSPEC_FIELD_PROJECT_URL = f'{NUSPEC_XSD_URI_PREFIX}projectUrl'
NUSPEC_FIELD_REQUIRE_LICENSE_ACCEPTANCE = f'{NUSPEC_XSD_URI_PREFIX}requireLicenseAcceptance'
NUSPEC_FIELD_SOURCE_URL = f'{NUSPEC_XSD_URI_PREFIX}packageSourceUrl'
NUSPEC_FIELD_SUMMARY = f'{NUSPEC_XSD_URI_PREFIX}summary'
NUSPEC_FIELD_TAGS = f'{NUSPEC_XSD_URI_PREFIX}tags'
NUSPEC_FIELD_TITLE = f'{NUSPEC_XSD_URI_PREFIX}title'
NUSPEC_FIELD_VERSION = f'{NUSPEC_XSD_URI_PREFIX}version'
NUSPEC_FIELD_MAPPINGS = {
    NUSPEC_FIELD_AUTHORS: 'authors',
    NUSPEC_FIELD_DESCRIPTION: 'description',
    NUSPEC_FIELD_ID: 'nuget_id',
    NUSPEC_FIELD_PROJECT_URL: 'project_url',
    NUSPEC_FIELD_REQUIRE_LICENSE_ACCEPTANCE: 'require_license_acceptance',
    NUSPEC_FIELD_SOURCE_URL: 'source_url',
    NUSPEC_FIELD_SUMMARY: 'summary',
    NUSPEC_FIELD_TAGS: 'tags',
    NUSPEC_FIELD_TITLE: 'title',
    NUSPEC_FIELD_VERSION: 'version'
}
PACKAGE_FIELDS = {f.name: f for f in Package._meta.get_fields()}  # pylint: disable=protected-access


@require_http_methods(['GET'])
def home(_request: HttpRequest) -> HttpResponse:
    return HttpResponse('{}', content_type='application/json')


@require_http_methods(['GET'])
def metadata(_request: HttpRequest, ending: str = '\n') -> HttpResponse:
    return HttpResponse(f'''
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<service xml:base="http://fixme/api/v2/"
                        xmlns:atom="http://www.w3.org/2005/Atom"
                        xmlns:app="http://www.w3.org/2007/app"
                        xmlns="http://www.w3.org/2007/app">
    <workspace>
        <atom:title>Default</atom:title>
        <collection href="Packages"><atom:title>Packages</atom:title></collection>
    </workspace>
</service>{ending}''',
                        content_type='application/xml')


def make_entry(host: str, package: Package, ending: str = '\n') -> str:
    return f'''<entry>
    <id>{host}/api/v2/Packages(Id='{package.nuget_id}',Version='{package.version}')</id>
    <category term="NuGetGallery.V2FeedPackage" scheme="http://schemas.microsoft.com/ado/2007/08/dataservices/scheme" />
    <link rel="edit" title="V2FeedPackage" href="Packages(Id='{package.nuget_id}',Version='{package.version}')" />
    <title type="text">{package.nuget_id}</title>
    <summary type="text">{package.nuget_id}</summary>
    <updated>{package.published.isoformat()}</updated>
    <author><name>{package.authors.first() or ''}</name></author>
    <link rel="edit-media" title="V2FeedPackage" href="Packages(Id='{package.nuget_id}',Version='{package.version}')/$value" />
    <content type="application/zip" src="{host}/api/v2/package/{package.nuget_id}/{package.version}" />
    <m:properties xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
                  xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices">
        <d:Copyright>{package.copyright or ''}</d:Copyright>
        <d:Dependencies></d:Dependencies>
        <d:Description>{package.description or ''}</d:Description>
        <d:DownloadCount m:type="Edm.Int32">{package.download_count}</d:DownloadCount>
        <d:GalleryDetailsUrl>{host}/package/{package.nuget_id}/{package.version}</d:GalleryDetailsUrl>
        <d:IconUrl>{package.icon_url or ''}</d:IconUrl>
        <d:IsAbsoluteLatestVersion m:type="Edm.Boolean">{'true' if package.is_absolute_latest_version else 'false'}</d:IsAbsoluteLatestVersion>
        <d:IsApproved m:type="Edm.Boolean">true</d:IsApproved>
        <d:IsLatestVersion m:type="Edm.Boolean">{'true' if package.is_latest_version else 'false'}</d:IsLatestVersion>
        <d:IsPrerelease m:type="Edm.Boolean">{'true' if package.is_prerelease else 'false'}</d:IsPrerelease>
        <d:Language m:null="true" />
        <d:LastEdited m:type="Edm.DateTime" m:null="true" />
        <d:LicenseNames m:null="true" />
        <d:LicenseReportUrl m:null="true" />
        <d:LicenseUrl>{package.license_url or ''}</d:LicenseUrl>
        <d:PackageHash>{package.hash or ''}</d:PackageHash>
        <d:PackageHashAlgorithm>{package.hash_algorithm or ''}</d:PackageHashAlgorithm>
        <d:PackageSize m:type="Edm.Int64">{package.size}</d:PackageSize>
        <d:ProjectUrl>{package.project_url}</d:ProjectUrl>
        <d:Published m:type="Edm.DateTime">{package.published.isoformat()}</d:Published>
        <d:ReleaseNotes>{package.release_notes or ''}</d:ReleaseNotes>
        <d:RequireLicenseAcceptance m:type="Edm.Boolean">{'true' if package.require_license_acceptance else 'false'}</d:RequireLicenseAcceptance>
        <d:Summary>{package.summary or ''}</d:Summary>
        <d:Tags xml:space="preserve"> {' '.join(x.name for x in package.tags.all())} </d:Tags>
        <d:Title>{package.title}</d:Title>
        <d:Version>{package.version}</d:Version>
        <d:VersionDownloadCount m:type="Edm.Int32">{package.version_download_count.count}</d:VersionDownloadCount>
    </m:properties>
</entry>{ending}'''


@require_http_methods(['GET'])
def find_packages_by_id(request: HttpRequest) -> HttpResponse:
    if (sem_ver_level := request.GET.get('semVerLevel')):
        logger.warning(f'Ignoring semVerLevel={sem_ver_level}')
    proto = 'https' if request.is_secure() else 'http'
    try:
        return HttpResponse('\n'.join(
            make_entry(f'{proto}://{request.get_host()}', x)
            for x in Package.objects.filter(nuget_id=request.GET['id'].replace('\'', ''))),
                            content_type='application/xml')
    except KeyError:
        return HttpResponse(status=400)


@require_http_methods(['GET'])
def packages(request: HttpRequest, ending: str = '\n') -> HttpResponse:
    filter_ = request.GET.get('$filter')
    order_by = request.GET.get('$orderby') or 'id'
    if (sem_ver_level := request.GET.get('semVerLevel')):
        logger.warning(f'Ignoring semVerLevel={sem_ver_level}')
    if (skip := request.GET.get('$skip')):
        logger.warning(f'Ignoring $skip={skip}')
    if (top := request.GET.get('$top')):
        logger.warning(f'Ignoring $top={top}')
    filters = filter_parser.parse(filter_) if filter_ else {}
    proto = 'https' if request.is_secure() else 'http'
    content = '\n'.join(
        make_entry(f'{proto}://{request.get_host()}', x)
        for x in Package.objects.order_by(order_by).filter(**filters)[0:20])
    return HttpResponse(f'{FEED_XML_PRE}\n{content}{FEED_XML_POST}{ending}',
                        content_type='application/xml')


@require_http_methods(['GET'])
def packages_with_args(request: HttpRequest, name: str, version: str) -> HttpResponse:
    if (package := Package.objects.filter(nuget_id=name, version=version).first()):
        proto = 'https' if request.is_secure() else 'http'
        content = make_entry(f'{proto}://{request.get_host()}', package)
        return HttpResponse(f'{FEED_XML_PRE}\n{content}{FEED_XML_POST}\n',
                            content_type='application/xml')
    return HttpResponseNotFound()


def is_authorized(request: HttpRequest) -> bool:
    try:
        return NugetUser.objects.filter(token=request.headers['X-NuGet-ApiKey']).exists()
    except KeyError:
        return False


@require_http_methods(['GET', 'DELETE'])
@csrf_exempt
def fetch_package_file(request: HttpRequest, name: str, version: str) -> HttpResponse:
    if (package := Package.objects.filter(nuget_id=name, version=version).first()):
        if request.method == 'GET':
            with package.file.open('rb') as f:
                package.download_count += 1
                version_count = package.version_download_count.filter(version=version).first()
                assert version_count is not None
                version_count.count += 1
                version_count.save()
                package.save()
                return HttpResponse(f.read(), content_type='application/zip')
        if request.method == 'DELETE' and settings.ALLOW_PACKAGE_DELETION:
            if not is_authorized(request):
                return HttpResponse(status=403)
            package.file.delete()
            package.delete()
            return HttpResponse(status=204)
    return HttpResponseNotFound()


@method_decorator(csrf_exempt, name='dispatch')
class APIV2PackageView(View):
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not is_authorized(request):
            return HttpResponse(status=403)
        return super().dispatch(request, *args, **kwargs)

    def put(self, request: HttpRequest) -> HttpResponse:
        if not request.content_type or not request.content_type.startswith('multipart'):
            logger.error(f'Invalid content type: {request.content_type}')
            return HttpResponse(status=400)
        # These 2 lines must exist. Combining into 1 does not work
        _, files = request.parse_file_upload(request.META, request)
        request.FILES.update(files)
        if len(request.FILES) == 0:
            logger.error('No files sent')
            return HttpResponse(status=400)
        if len(request.FILES) > 1:
            logger.error('More than file sent')
            return HttpResponse(status=400)
        nuget_file = list(request.FILES.values())[0]
        if not zipfile.is_zipfile(nuget_file):
            logger.error('Not a zip file')
            return HttpResponse(status=400)
        with zipfile.ZipFile(nuget_file) as z:
            nuspecs = [x for x in z.filelist if x.filename.endswith('.nuspec')]
            if len(nuspecs) > 1 or not nuspecs:
                return HttpResponse(status=400)
            with TemporaryDirectory(suffix='.nuget-parse') as temp_dir:
                z.extract(nuspecs[0], temp_dir)
                root = parse_xml(Path(temp_dir) / nuspecs[0].filename).getroot()
        new_package = Package()
        add_tags = []
        add_authors = []
        for key, column_name in NUSPEC_FIELD_MAPPINGS.items():
            value = root[0].find(key)
            assert value is not None
            if not value.text:
                logger.warning(f'No value for key {key}')
                continue
            column_type = (None if column_name not in PACKAGE_FIELDS else
                           PACKAGE_FIELDS[column_name].get_internal_type())
            if not column_type or column_type == 'ManyToManyField':
                if column_name == 'tags':
                    assert value is not None
                    tags = [x.strip() for x in re.split(r'\s+', value.text)]
                    for name in tags:
                        new_tag, _ = Tag.objects.filter(name=name).get_or_create(name=name)
                        new_tag.save()
                        add_tags.append(new_tag)
                elif column_name == 'authors':
                    authors = [x.strip() for x in re.split(',', value.text)]
                    for name in authors:
                        new_author, _ = Author.objects.get_or_create(name=name)
                        new_author.save()
                        add_authors.append(new_author)
                else:
                    logger.warning(f'Did not set {column_name}')
            elif column_type == 'BooleanField':
                setattr(new_package, column_name, value.text.lower() == 'true')
            else:
                setattr(new_package, column_name, value.text)
        version_split = new_package.version.split('.')
        new_package.version0 = int(version_split[0])
        new_package.version1 = int(version_split[1])
        try:
            new_package.version2 = int(version_split[2])
            new_package.version3 = int(version_split[3])
        except IndexError:
            pass
        version_download_count = PackageVersionDownloadCount(count=0, version=new_package.version)
        version_download_count.save()
        new_package.size = nuget_file.size
        new_package.file = File(nuget_file, nuget_file.name)  # type: ignore[assignment]
        uploader = NugetUser.objects.filter(token=request.headers['x-nuget-apikey']).first()
        assert uploader is not None
        new_package.uploader = uploader
        try:
            new_package.save()
        except IntegrityError:
            return HttpResponse(status=400)
        new_package.tags.add(*add_tags)
        new_package.authors.add(*add_authors)
        new_package.version_download_count.add(version_download_count)
        return HttpResponse(status=201)

    def post(self, request: HttpRequest) -> HttpResponse:
        return self.put(request)
