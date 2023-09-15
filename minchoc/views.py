from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import logging
import re
import zipfile

from defusedxml.ElementTree import parse as parse_xml
from django.conf import settings
from django.core.files import File
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, JsonResponse
from django.http.multipartparser import MultiPartParserError
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .constants import FEED_XML_POST, FEED_XML_PRE
from .filteryacc import parser as filter_parser
from .models import Author, NugetUser, Package, Tag
from .utils import make_entry

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
PACKAGE_FIELDS = {f.name: f for f in Package._meta.get_fields()}

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def home(_request: HttpRequest) -> HttpResponse:
    """Static homepage."""
    return JsonResponse({})


@require_http_methods(['GET'])
def metadata(_request: HttpRequest) -> HttpResponse:
    """Static page at ``/$metadata`` and at ``/api/v2/$metadata``."""
    return HttpResponse('''<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<service xml:base="http://fixme/api/v2/"
                        xmlns:atom="http://www.w3.org/2005/Atom"
                        xmlns:app="http://www.w3.org/2007/app"
                        xmlns="http://www.w3.org/2007/app">
    <workspace>
        <atom:title>Default</atom:title>
        <collection href="Packages"><atom:title>Packages</atom:title></collection>
    </workspace>
</service>\n''',
                        content_type='application/xml')


@require_http_methods(['GET'])
def find_packages_by_id(request: HttpRequest) -> HttpResponse:
    """
    Takes a ``GET`` request to find packages.

    Sample URL: ``/FindPackagesById()?id=package-name``
    """
    if (sem_ver_level := request.GET.get('semVerLevel')):
        logger.warning('Ignoring semVerLevel=%s', sem_ver_level)
    proto = 'https' if request.is_secure() else 'http'
    proto_host = f'{proto}://{request.get_host()}'
    try:
        content = '\n'.join(
            make_entry(proto_host, x)
            for x in Package.objects.filter(nuget_id=request.GET['id'].replace('\'', '')))
        return HttpResponse(f'{FEED_XML_PRE}{content}{FEED_XML_POST}\n' % {
            'BASEURL': proto_host,
            'UPDATED': datetime.now().isoformat()
        },
                            content_type='application/xml')
    except KeyError:
        return HttpResponse(status=400)


@require_http_methods(['GET'])
def packages(request: HttpRequest) -> HttpResponse:
    """
    Takes a ``GET`` request to find packages. Query parameters ``$skip``, ``$top`` and
    ``semVerLevel`` are ignored. This means pagination is currently not supported.

    Sample URL: ``/Packages()?$orderby=id&$filter=(tolower(Id) eq 'package-name') and IsLatestVersion&$skip=0&$top=1``
    """  # noqa: E501
    filter_ = request.GET.get('$filter')
    order_by = request.GET.get('$orderby') or 'id'
    if (sem_ver_level := request.GET.get('semVerLevel')):
        logger.warning('Ignoring semVerLevel=%s', sem_ver_level)
    if (skip := request.GET.get('$skip')):
        logger.warning('Ignoring $skip=%s', skip)
    if (top := request.GET.get('$top')):
        logger.warning('Ignoring $top=%s', top)
    try:
        filters = filter_parser.parse(filter_) if filter_ else {}
    except SyntaxError:
        return JsonResponse({'error': 'Invalid syntax in filter'}, status=400)
    proto = 'https' if request.is_secure() else 'http'
    proto_host = f'{proto}://{request.get_host()}'
    content = '\n'.join(
        make_entry(proto_host, x)
        for x in Package.objects.order_by(order_by).filter(**filters)[0:20])
    return HttpResponse(f'{FEED_XML_PRE}\n{content}{FEED_XML_POST}\n' % {
        'BASEURL': proto_host,
        'UPDATED': datetime.now().isoformat()
    },
                        content_type='application/xml')


@require_http_methods(['GET'])
def packages_with_args(request: HttpRequest, name: str, version: str) -> HttpResponse:
    """
    Alternate ``Packages()`` with arguments to find a single package instance.

    Sample URL: ``/Packages(Id='name',Version='123.0.0')``
    """
    if (package := Package.objects.filter(nuget_id=name, version=version).first()):
        proto = 'https' if request.is_secure() else 'http'
        proto_host = f'{proto}://{request.get_host()}'
        content = make_entry(proto_host, package)
        return HttpResponse(f'{FEED_XML_PRE}\n{content}{FEED_XML_POST}\n' % {
            'BASEURL': proto_host,
            'UPDATED': datetime.now().isoformat()
        },
                            content_type='application/xml')
    return HttpResponseNotFound()


@require_http_methods(['GET', 'DELETE'])
@csrf_exempt
def fetch_package_file(request: HttpRequest, name: str, version: str) -> HttpResponse:
    """
    Get the file for a package instance.

    Sample URL: ``/api/package/name/123.0.0``

    This also handles deletions. Deletions will only be allowed with authentication and with
    ``settings.ALLOW_PACKAGE_DELETION`` set to ``True``.
    """
    if (package := Package.objects.filter(nuget_id=name, version=version).first()):
        if request.method == 'GET':
            with package.file.open('rb') as f:
                package.download_count += 1
                package.save()
                return HttpResponse(f.read(), content_type='application/zip')
        if request.method == 'DELETE' and settings.ALLOW_PACKAGE_DELETION:
            if not NugetUser.request_has_valid_token(request):
                return JsonResponse({'error': 'Not authorized'}, status=403)
            package.file.delete()
            package.delete()
            return HttpResponse(status=204)
        else:
            return HttpResponse(status=405)
    return HttpResponseNotFound()


@method_decorator(csrf_exempt, name='dispatch')
class APIV2PackageView(View):
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Checks if a user is authorised before allowing the request to continue."""
        if not NugetUser.request_has_valid_token(request):
            return JsonResponse({'error': 'Not authorized'}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def put(self, request: HttpRequest) -> HttpResponse:
        """Upload a package. This must be a multipart upload with a single valid NuGet file."""
        if not request.content_type or not request.content_type.startswith('multipart/'):
            return JsonResponse(
                {'error': f'Invalid content type: {request.content_type or "unknown"}'}, status=400)
        try:
            _, files = request.parse_file_upload(request.META, request)
        except MultiPartParserError:
            return JsonResponse({'error': 'Invalid upload'}, status=400)
        request.FILES.update(files)
        if len(request.FILES) == 0:
            return JsonResponse({'error': 'No files sent'}, status=400)
        if len(request.FILES) > 1:
            return JsonResponse({'error': 'More than one file sent'}, status=400)
        nuget_file = list(request.FILES.values())[0]
        if not zipfile.is_zipfile(nuget_file):
            return JsonResponse({'error': 'Not a zip file'}, status=400)
        with zipfile.ZipFile(nuget_file) as z:
            nuspecs = [x for x in z.filelist if x.filename.endswith('.nuspec')]
            if len(nuspecs) > 1 or not nuspecs:
                return JsonResponse(
                    {
                        'error':
                            'There should be exactly 1 nuspec file present. 0 or more than 1 were '
                            'found.'
                    },
                    status=400)
            with TemporaryDirectory(suffix='.nuget-parse') as temp_dir:
                z.extract(nuspecs[0], temp_dir)
                root = parse_xml(Path(temp_dir) / nuspecs[0].filename).getroot()
        new_package = Package()
        add_tags = []
        add_authors = []
        for key, column_name in NUSPEC_FIELD_MAPPINGS.items():
            value = root[0].find(key)
            assert value is not None
            if not value.text:  # pragma no cover
                logger.warning('No value for key %s', key)
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
                else:  # pragma no cover
                    logger.warning('Did not set %s', column_name)
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
        new_package.size = nuget_file.size
        new_package.file = File(nuget_file, nuget_file.name)  # type: ignore[assignment]
        uploader = NugetUser.objects.filter(token=request.headers['x-nuget-apikey']).first()
        assert uploader is not None
        new_package.uploader = uploader
        try:
            new_package.save()
        except IntegrityError:
            return JsonResponse({'error': 'Integrity error (has this already been uploaded?)'},
                                status=400)
        new_package.tags.add(*add_tags)
        new_package.authors.add(*add_authors)
        return HttpResponse(status=201)

    def post(self, request: HttpRequest) -> HttpResponse:
        """A ``POST`` request is treated the same as ``PUT``."""
        return self.put(request)
