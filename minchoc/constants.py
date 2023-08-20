__all__ = ('FEED_XML_POST', 'FEED_XML_PRE')

FEED_XML_PRE = '''<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<feed xml:base="%(BASEURL)s/api/v1/"
    xmlns="http://www.w3.org/2005/Atom"
    xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
    xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
    <id>%(BASEURL)s/api/v1/Packages</id>
    <title type="text">Packages</title>
    <updated>%(UPDATED)s</updated>
    <link rel="self" title="Packages" href="Packages" />'''
FEED_XML_POST = '</feed>'
