"""Views."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, cast
import logging
import re
import zipfile

from asgiref.sync import sync_to_async
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
from typing_extensions import override

from .constants import FEED_XML_POST, FEED_XML_PRE
from .filteryacc import FIELD_MAPPING, parser as filter_parser
from .models import Author, NugetUser, Package, Tag
from .utils import make_entry, tag_text_or

if TYPE_CHECKING:  # pragma: no cover
    from xml.etree.ElementTree import Element

    from _typeshed import SupportsKeysAndGetItem
    from django.core.files.uploadedfile import UploadedFile

NUSPEC_NAMESPACES = {'': 'http://schemas.microsoft.com/packaging/2010/07/nuspec.xsd'}
NUSPEC_FIELD_AUTHORS = 'authors'
NUSPEC_FIELD_DESCRIPTION = 'description'
NUSPEC_FIELD_ID = 'id'
NUSPEC_FIELD_PROJECT_URL = 'projectUrl'
NUSPEC_FIELD_REQUIRE_LICENSE_ACCEPTANCE = 'requireLicenseAcceptance'
NUSPEC_FIELD_SOURCE_URL = 'packageSourceUrl'
NUSPEC_FIELD_SUMMARY = 'summary'
NUSPEC_FIELD_TAGS = 'tags'
NUSPEC_FIELD_TITLE = 'title'
NUSPEC_FIELD_VERSION = 'version'
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
_TAG_SEPARATOR_RE = re.compile(r'\s+')

logger = logging.getLogger(__name__)


def _read_package_file(package: Package) -> bytes:
    with package.file.open('rb') as f:
        return cast('bytes', f.read())


@require_http_methods(['GET'])
def home(_request: HttpRequest) -> HttpResponse:
    """
    Get the content for the static homepage.

    Parameters
    ----------
    _request : HttpRequest
        The incoming request (unused).

    Returns
    -------
    HttpResponse
        JSON response with an empty object.
    """
    return JsonResponse({})


@require_http_methods(['GET'])
def metadata(_request: HttpRequest) -> HttpResponse:
    """
    Get content for static page at ``/$metadata`` and at ``/api/v2/$metadata``.

    Parameters
    ----------
    _request : HttpRequest
        The incoming request (unused).

    Returns
    -------
    HttpResponse
        Service document XML for the NuGet v2 API.
    """
    return HttpResponse("""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<service xml:base="http://fixme/api/v2/"
                        xmlns:atom="http://www.w3.org/2005/Atom"
                        xmlns:app="http://www.w3.org/2007/app"
                        xmlns="http://www.w3.org/2007/app">
    <workspace>
        <atom:title>Default</atom:title>
        <collection href="Packages"><atom:title>Packages</atom:title></collection>
    </workspace>
</service>\n""",
                        content_type='application/xml')


async def _find_packages_by_id_feed(request: HttpRequest, proto_host: str) -> HttpResponse:
    """
    Build the Atom feed for :py:func:`find_packages_by_id`.

    Parameters
    ----------
    request : HttpRequest
        The incoming ``GET`` request.
    proto_host : str
        The scheme and host prefix used when building entry URLs.

    Returns
    -------
    HttpResponse
        Atom feed XML for the requested package identifier.
    """
    nuget_id = request.GET['id'].replace("'", '')
    queryset = Package._default_manager.filter(nuget_id=nuget_id)
    if skiptoken := request.GET.get('$skiptoken'):
        # Parse skiptoken format: `'PackageName','Version'`.
        # Remove quotes and split by comma.
        parts = [part.strip().strip('\'"') for part in skiptoken.split(',')]
        expected_parts = 2
        if len(parts) == expected_parts:
            skip_id, skip_version = parts
            queryset = queryset.order_by('version')
            all_packages: list[Package] = [p async for p in queryset]
            skip_index = -1
            for i, pkg in enumerate(all_packages):
                if pkg.nuget_id == skip_id and pkg.version == skip_version:
                    skip_index = i
                    break
            selected = (all_packages[skip_index + 1:] if skip_index >= 0 else all_packages)
            content = '\n'.join([await make_entry(proto_host, x) for x in selected])
            feed_xml = f'{FEED_XML_PRE}{content}{FEED_XML_POST}\n'
            return HttpResponse(feed_xml % {
                'BASEURL': proto_host,
                'UPDATED': datetime.now(timezone.utc).isoformat()
            },
                                content_type='application/xml')
        logger.warning('Invalid $skiptoken format: %s', skiptoken)  # pragma: no cover
    content = '\n'.join([await make_entry(proto_host, x) async for x in queryset])
    feed_xml = f'{FEED_XML_PRE}{content}{FEED_XML_POST}\n'
    return HttpResponse(feed_xml % {
        'BASEURL': proto_host,
        'UPDATED': datetime.now(timezone.utc).isoformat()
    },
                        content_type='application/xml')


@require_http_methods(['GET'])
async def find_packages_by_id(request: HttpRequest) -> HttpResponse:
    """
    Take a ``GET`` request to find packages.

    Sample URL: ``/FindPackagesById()?id=package-name``

    Supports ``$skiptoken`` parameter for pagination in the format:
    ``$skiptoken='PackageName','Version'``.

    Parameters
    ----------
    request : HttpRequest
        The incoming ``GET`` request.

    Returns
    -------
    HttpResponse
        Atom feed XML, or ``400`` if required query parameters are missing.
    """
    if sem_ver_level := request.GET.get('semVerLevel'):
        logger.warning('Ignoring semVerLevel=%s', sem_ver_level)
    proto = 'https' if request.is_secure() else 'http'
    proto_host = f'{proto}://{request.get_host()}'
    try:
        return await _find_packages_by_id_feed(request, proto_host)
    except KeyError:
        return HttpResponse(status=400)


@require_http_methods(['GET'])
async def packages(request: HttpRequest) -> HttpResponse:
    """
    Take a ``GET`` request to find packages.

    Query parameters ``$skip``, ``$top`` and ``semVerLevel`` are ignored. This means pagination is
    currently not supported.

    Sample URL: ``/Packages()?$orderby=id&$filter=(tolower(Id) eq 'package-name') and IsLatestVersion&$skip=0&$top=1``

    Parameters
    ----------
    request : HttpRequest
        The incoming ``GET`` request.

    Returns
    -------
    HttpResponse
        Atom feed XML, or JSON error if the ``$filter`` expression is invalid.
    """  # ruff:ignore[line-too-long]
    filter_ = request.GET.get('$filter')
    req_order_by = request.GET.get('$orderby')
    order_by = (FIELD_MAPPING[req_order_by]
                if req_order_by and req_order_by in FIELD_MAPPING else 'nuget_id')
    if sem_ver_level := request.GET.get('semVerLevel'):
        logger.warning('Ignoring semVerLevel=%s', sem_ver_level)
    if skip := request.GET.get('$skip'):
        logger.warning('Ignoring $skip=%s', skip)
    if top := request.GET.get('$top'):
        logger.warning('Ignoring $top=%s', top)
    try:
        filters = filter_parser.parse(filter_) if filter_ else {}
    except SyntaxError:
        return JsonResponse({'error': 'Invalid syntax in filter.'}, status=400)
    proto = 'https' if request.is_secure() else 'http'
    proto_host = f'{proto}://{request.get_host()}'
    qs = Package._default_manager.order_by(order_by).filter(filters)[0:20]
    content = '\n'.join([await make_entry(proto_host, x) async for x in qs])
    feed_xml = f'{FEED_XML_PRE}\n{content}{FEED_XML_POST}\n'
    return HttpResponse(feed_xml % {
        'BASEURL': proto_host,
        'UPDATED': datetime.now(timezone.utc).isoformat()
    },
                        content_type='application/xml')


@require_http_methods(['GET'])
async def packages_with_args(request: HttpRequest, name: str, version: str) -> HttpResponse:
    """
    Alternate ``Packages()`` with arguments to find a single package instance.

    Sample URL: ``/Packages(Id='name',Version='123.0.0')``

    Parameters
    ----------
    request : HttpRequest
        The incoming ``GET`` request.
    name : str
        NuGet package identifier.
    version : str
        Package version string.

    Returns
    -------
    HttpResponse
        Atom entry XML if found, or ``404`` if the package does not exist.
    """
    if package := await Package._default_manager.filter(nuget_id=name, version=version).afirst():
        proto = 'https' if request.is_secure() else 'http'
        proto_host = f'{proto}://{request.get_host()}'
        content = await make_entry(proto_host, package)
        feed_xml = f'{FEED_XML_PRE}\n{content}{FEED_XML_POST}\n'
        return HttpResponse(feed_xml % {
            'BASEURL': proto_host,
            'UPDATED': datetime.now(timezone.utc).isoformat()
        },
                            content_type='application/xml')
    return HttpResponseNotFound()


@require_http_methods(['GET', 'DELETE'])
@csrf_exempt
async def fetch_package_file(request: HttpRequest, name: str, version: str) -> HttpResponse:
    """
    Get the file for a package instance.

    Sample URL: ``/api/package/name/123.0.0``

    This also handles deletions. Deletions will only be allowed with authentication and with
    ``settings.ALLOW_PACKAGE_DELETION`` set to ``True``.

    Parameters
    ----------
    request : HttpRequest
        The incoming ``GET`` or ``DELETE`` request.
    name : str
        NuGet package identifier.
    version : str
        Package version string.

    Returns
    -------
    HttpResponse
        Zip payload, ``204`` on authorised delete, error JSON, ``404``, or ``405``.
    """
    if package := await Package._default_manager.filter(nuget_id=name, version=version).afirst():
        match request.method:
            case 'GET':
                data = await sync_to_async(_read_package_file)(package)
                package.download_count += 1
                await package.asave()
                return HttpResponse(data, content_type='application/zip')
            case 'DELETE' if settings.ALLOW_PACKAGE_DELETION:  # type: ignore[misc]
                if not await NugetUser.arequest_has_valid_token(request):
                    return JsonResponse({'error': 'Not authorized'}, status=403)
                await sync_to_async(package.file.delete)()
                await package.adelete()
                return HttpResponse(status=204)
            case _:
                return HttpResponse(status=405)
    return HttpResponseNotFound()


class _UploadError(Exception):
    """Raised when an uploaded package cannot be accepted."""
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def _uploaded_nuget_file(request: HttpRequest) -> UploadedFile:
    """
    Get the single uploaded NuGet file from a multipart request.

    Parameters
    ----------
    request : HttpRequest
        The upload request.

    Returns
    -------
    UploadedFile
        The uploaded file.

    Raises
    ------
    _UploadError
        If the request is not a multipart upload carrying exactly one zip file.
    """
    if not request.content_type or not request.content_type.startswith('multipart/'):
        msg = f'Invalid content type: {request.content_type or "unknown"}'
        raise _UploadError(msg)
    try:
        _, files = request.parse_file_upload(request.META, BytesIO(request.body))
    except MultiPartParserError as e:
        msg = 'Invalid upload'
        raise _UploadError(msg) from e
    request.FILES.update(cast('SupportsKeysAndGetItem[str, UploadedFile]', files))
    if len(request.FILES) == 0:
        msg = 'No files sent'
        raise _UploadError(msg)
    if len(request.FILES) > 1:
        msg = 'More than one file sent'
        raise _UploadError(msg)
    nuget_file = next(iter(request.FILES.values()))
    if isinstance(nuget_file, list):
        msg = 'More than one file sent'
        raise _UploadError(msg)
    if not zipfile.is_zipfile(nuget_file):
        msg = 'Not a zip file'
        raise _UploadError(msg)
    return nuget_file


def _parse_nuspec_metadata(nuget_file: UploadedFile) -> Element:
    """
    Extract and parse the nuspec file contained in an uploaded package.

    Parameters
    ----------
    nuget_file : UploadedFile
        The uploaded package.

    Returns
    -------
    Element
        The ``metadata`` element of the nuspec file.

    Raises
    ------
    _UploadError
        If the package does not contain exactly one nuspec file, or the nuspec is not valid XML.
    """
    with zipfile.ZipFile(nuget_file) as z:
        nuspecs = [x for x in z.filelist if x.filename.endswith('.nuspec')]
        if len(nuspecs) > 1 or not nuspecs:
            msg = 'There should be exactly 1 nuspec file present. 0 or more than 1 were found.'
            raise _UploadError(msg)
        with TemporaryDirectory(suffix='.nuget-parse') as temp_dir:
            z.extract(nuspecs[0], temp_dir)
            root = parse_xml(Path(temp_dir) / nuspecs[0].filename).getroot()
    if root is None:
        msg = 'Invalid nuspec'
        raise _UploadError(msg)
    return root[0]


async def _get_or_create_tags(value: str) -> list[Tag]:
    """
    Get or create every tag named in a nuspec ``tags`` value.

    Parameters
    ----------
    value : str
        Whitespace-separated tag names.

    Returns
    -------
    list[Tag]
        The tags, in the order they appear in the value.
    """
    return [(await Tag._default_manager.aget_or_create(name=name.strip()))[0]
            for name in _TAG_SEPARATOR_RE.split(value)]


async def _get_or_create_authors(value: str) -> list[Author]:
    """
    Get or create every author named in a nuspec ``authors`` value.

    Parameters
    ----------
    value : str
        Comma-separated author names.

    Returns
    -------
    list[Author]
        The authors, in the order they appear in the value.
    """
    return [(await Author._default_manager.aget_or_create(name=name.strip()))[0]
            for name in value.split(',')]


async def _apply_nuspec_fields(package: Package,
                               nuspec_metadata: Element) -> tuple[list[Tag], list[Author]]:
    """
    Copy the supported nuspec fields on to an unsaved package.

    Parameters
    ----------
    package : Package
        The package to populate.
    nuspec_metadata : Element
        The ``metadata`` element of the nuspec file.

    Returns
    -------
    tuple[list[Tag], list[Author]]
        The tags and authors to attach once the package has been saved.
    """
    add_tags: list[Tag] = []
    add_authors: list[Author] = []
    for key, column_name in NUSPEC_FIELD_MAPPINGS.items():
        value = tag_text_or(nuspec_metadata.find(key, NUSPEC_NAMESPACES))
        if not value:  # pragma no cover
            logger.warning('No value for key %s', key)
            continue
        column_type = (None if column_name not in PACKAGE_FIELDS else
                       PACKAGE_FIELDS[column_name].get_internal_type())
        if not column_type or column_type == 'ManyToManyField':
            if column_name == 'tags':
                add_tags.extend(await _get_or_create_tags(value))
            elif column_name == 'authors':
                add_authors.extend(await _get_or_create_authors(value))
            else:  # pragma no cover
                logger.warning('Did not set %s', column_name)
        elif column_type == 'BooleanField':
            setattr(package, column_name, value.lower() == 'true')
        else:
            setattr(package, column_name, value)
    return add_tags, add_authors


def _apply_version_fields(package: Package) -> None:
    """
    Split the package version string on to the sortable numeric version columns.

    Parameters
    ----------
    package : Package
        The package to populate.
    """
    version_split = package.version.split('.')
    package.version0 = int(version_split[0])
    package.version1 = int(version_split[1])
    try:
        package.version2 = int(version_split[2])
        package.version3 = int(version_split[3])
    except IndexError:
        pass


async def _uploader_from_request(request: HttpRequest) -> NugetUser:
    """
    Get the user identified by the API key header of a request.

    Parameters
    ----------
    request : HttpRequest
        The upload request.

    Returns
    -------
    NugetUser
        The uploading user.

    Raises
    ------
    _UploadError
        If no user has the token given in the request.
    """
    if (uploader := await NugetUser._default_manager.filter(token=request.headers['x-nuget-apikey']
                                                            ).afirst()) is None:
        msg = 'Uploader not found'
        raise _UploadError(msg, 500)
    return uploader


async def _asave_new_package(package: Package) -> None:
    """
    Save a newly uploaded package.

    Parameters
    ----------
    package : Package
        The package to save.

    Raises
    ------
    _UploadError
        If the package conflicts with one that already exists.
    """
    try:
        await package.asave()
    except IntegrityError as e:
        msg = 'Integrity error (has this already been uploaded?)'
        raise _UploadError(msg) from e


async def _asave_uploaded_package(request: HttpRequest) -> None:
    """
    Store the package sent in an upload request.

    The helpers called here raise ``_UploadError`` when the upload has to be rejected.

    Parameters
    ----------
    request : HttpRequest
        The upload request.
    """
    nuget_file = _uploaded_nuget_file(request)
    nuspec_metadata = _parse_nuspec_metadata(nuget_file)
    new_package = Package()
    add_tags, add_authors = await _apply_nuspec_fields(new_package, nuspec_metadata)
    _apply_version_fields(new_package)
    new_package.size = cast('int', nuget_file.size)
    new_package.file = File(nuget_file, nuget_file.name)
    new_package.uploader = await _uploader_from_request(request)
    await _asave_new_package(new_package)
    await new_package.tags.aadd(*add_tags)
    await new_package.authors.aadd(*add_authors)


@method_decorator(csrf_exempt, name='dispatch')
class APIV2PackageView(View):
    """API V2 package upload view."""
    @override
    async def dispatch(  # type: ignore[override]  # ty: ignore[invalid-method-override]
            self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Check if a user is authorised before allowing the request to continue.

        Parameters
        ----------
        request : HttpRequest
            The incoming request.
        *args : Any
            Positional arguments forwarded to the parent view.
        **kwargs : Any
            Keyword arguments forwarded to the parent view.

        Returns
        -------
        HttpResponse
            Forbidden JSON if unauthorised; otherwise the parent dispatch result.
        """
        if not await NugetUser.arequest_has_valid_token(request):
            return JsonResponse({'error': 'Not authorized'}, status=403)
        # Django typing stubs treat ``View.dispatch`` as sync, but it awaits async handlers.
        result = await super().dispatch(  # type: ignore[misc]  # ty: ignore[invalid-await]
            request, *args, **kwargs)
        return cast('HttpResponse', result)

    @staticmethod
    async def put(request: HttpRequest) -> HttpResponse:
        """
        Upload a package. This must be a multipart upload with a single valid NuGet file.

        Parameters
        ----------
        request : HttpRequest
            The upload request.

        Returns
        -------
        HttpResponse
            ``201`` on success, or JSON error with an appropriate status code.
        """
        try:
            await _asave_uploaded_package(request)
        except _UploadError as e:
            return JsonResponse({'error': e.message}, status=e.status)
        return HttpResponse(status=201)

    async def post(self, request: HttpRequest) -> HttpResponse:
        """
        Treat ``POST`` requests the same as ``PUT``.

        Parameters
        ----------
        request : HttpRequest
            The incoming request.

        Returns
        -------
        HttpResponse
            Result of :py:meth:`put`.
        """
        return await self.put(request)
