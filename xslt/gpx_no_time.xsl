<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:gpx="http://www.topografix.com/GPX/1/1"
xmlns:gpxx="http://www.garmin.com/xmlschemas/WaypointExtension/v1"
xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
>
<xsl:output method="text"/>
<xsl:template match="/">
    <!--<xsl:for-each select="//gpx:trkpt[./gpx:time &gt; '2017-06-07T15:11:07Z']">-->
    <xsl:for-each select="//gpx:trkseg">
	 <xsl:for-each select="gpx:trkpt">
		<xsl:value-of select="@lat"/>
		<xsl:text>;</xsl:text>
		<xsl:value-of select="@lon"/>
		<xsl:text>;</xsl:text>
		<xsl:value-of select="gpx:time"/>
        <xsl:text>|</xsl:text>
     </xsl:for-each>
     <xsl:text>&#xa;</xsl:text>
    </xsl:for-each>
</xsl:template>
</xsl:stylesheet>
