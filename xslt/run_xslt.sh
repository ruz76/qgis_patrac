cd $1/xslt/
java -jar saxon9he.jar $2 gpx.xsl start=$4 end=$5 >> $3
