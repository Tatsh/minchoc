from django.db.models import Sum

from .models import Package

__all__ = ('make_entry',)


def make_entry(host: str, package: Package, ending: str = '\n') -> str:
    """Creates a package ``<entry>`` element for a package XML feed."""
    total_downloads = Package.objects.filter(nuget_id=package.nuget_id).aggregate(
        total_downloads=Sum('download_count'))['total_downloads']
    return f'''<entry>
    <id>{host}/api/v2/Packages(Id='{package.nuget_id}',Version='{package.version}')</id>
    <category term="NuGetGallery.V2FeedPackage"
        scheme="http://schemas.microsoft.com/ado/2007/08/dataservices/scheme" />
    <link rel="edit" title="V2FeedPackage"
        href="Packages(Id='{package.nuget_id}',Version='{package.version}')" />
    <title type="text">{package.nuget_id}</title>
    <summary type="text">{package.nuget_id}</summary>
    <updated>{package.published.isoformat()}</updated>
    <author><name>{package.authors.first() or ''}</name></author>
    <link rel="edit-media" title="V2FeedPackage"
        href="Packages(Id='{package.nuget_id}',Version='{package.version}')/$value" />
    <content type="application/zip"
        src="{host}/api/v2/package/{package.nuget_id}/{package.version}" />
    <m:properties xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
                  xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices">
        <d:Copyright>{package.copyright or ''}</d:Copyright>
        <d:Dependencies></d:Dependencies>
        <d:Description>{package.description or ''}</d:Description>
        <d:DownloadCount m:type="Edm.Int32">{total_downloads}</d:DownloadCount>
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
        <d:VersionDownloadCount m:type="Edm.Int32">{package.download_count}</d:VersionDownloadCount>
    </m:properties>
</entry>{ending}'''  # noqa: E501
