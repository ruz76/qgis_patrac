
#!/usr/bin/env python

import glob, os
import sys
import subprocess
import csv
import io
from shutil import copyfile

#Jen test zda to bezi
#f = open('/tmp/test.txt', 'w')
#f.write('This is a test\n')
#f.close()

#Pridani cest k qgis, to nefungovalo, ale pres bat ano
#sys.path.append("C:\\Program Files\\QGIS 2.16.1\\bin")
#sys.path.append("C:\\Program Files\\QGIS 2.16.1\\apps\\Python27\\Scripts")
#sys.path.append("C:\\Windows\\system32")
#sys.path.append("C:\\Windows")
#sys.path.append("C:\\Windows\\WBem")
#print sys.path

#Zkusime jeste linux
sys.path.append("/usr/local/sbin")
sys.path.append("/usr/local/bin")
sys.path.append("/usr/sbin")
sys.path.append("/usr/bin")
sys.path.append("/sbin")
sys.path.append("/bin")
sys.path.append("/usr/games")
sys.path.append("/usr/local/games")

# path to the GRASS GIS launch script
# MS Windows
# grass7bin_win = r'C:\OSGeo4W\bin\grass70svn.bat'
# uncomment when using standalone WinGRASS installer
grass7bin_win = r'C:\OSGeo4W64\bin\grass72.bat'
# Linux
grass7bin_lin = 'grass72'
# Mac OS X
# this is TODO
grass7bin_mac = '/Applications/GRASS/GRASS-7.0.app/'

# DATA
# define GRASS DATABASE
# add your path to grassdata (GRASS GIS database) directory
DATAPATH=str(sys.argv[1])
PLUGINPATH=str(sys.argv[2]) 
gisdb = DATAPATH + "/grassdata"
# the following path is the default path on MS Windows
# gisdb = os.path.join(os.path.expanduser("~"), "Documents/grassdata")

# specify (existing) location and mapset
location = "wgs84"
mapset   = "PERMANENT"


########### SOFTWARE
if sys.platform.startswith('linux'):
    # we assume that the GRASS GIS start script is available and in the PATH
    # query GRASS 7 itself for its GISBASE
    grass7bin = grass7bin_lin
elif sys.platform.startswith('win'):
    grass7bin = grass7bin_win
else:
    raise OSError('Platform not configured.')

# query GRASS 7 itself for its GISBASE
startcmd = [grass7bin, '--config', 'path']

p = subprocess.Popen(startcmd, shell=False,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()
if p.returncode != 0:
    print >>sys.stderr, "ERROR: Cannot find GRASS GIS 7 start script (%s)" % startcmd
    sys.exit(-1)
gisbase = out.strip('\n\r')

# Set GISBASE environment variable
os.environ['GISBASE'] = gisbase
# the following not needed with trunk
os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
# add path to GRASS addons
home = os.path.expanduser("~")
os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')

# define GRASS-Python environment
gpydir = os.path.join(gisbase, "etc", "python")
sys.path.append(gpydir)

########### DATA
# Set GISDBASE environment variable
os.environ['GISDBASE'] = gisdb
 
# import GRASS Python bindings (see also pygrass)
import grass.script as gscript
import grass.script.setup as gsetup
#from grass.pygrass.modules.shortcuts import raster as r
 
###########
# launch session
gsetup.init(gisbase,
            gisdb, location, mapset)
 
#gscript.message('Current GRASS GIS 7 environment:')
#print gscript.gisenv()

INPUT=str(sys.argv[3])
SECTOR=str(sys.argv[4])

#Converts GPX named by SECTOR to SHP
if not os.path.exists(DATAPATH + '/search/gpx/' + SECTOR):
    os.makedirs(DATAPATH + '/search/gpx/' + SECTOR)

#Reads header of GML
header = io.open(PLUGINPATH + '/xslt/gml_header.gml', encoding='utf-8', mode='r').read()
#Writes header to out_polyline.gml
f = io.open(DATAPATH + '/search/temp/out_polyline.gml', encoding='utf-8', mode='w')
f.write(header)
f.write(u'<gml:featureMember>\n')
f.write(u'<ogr:sample fid="sample.0">\n')
f.write(u'<ogr:geometryProperty><gml:LineString><gml:coordinates>\n')
        
#Reads CVS created by XSTL
with open(INPUT) as csvDataFile:
    csvReader = csv.reader(csvDataFile, delimiter=';')
    for row in csvReader:
        ##print(row)
        #For each row creates one point in polyline
        f.write(row[1] + u',' + row[0] + u' ')

#Finished the polyline
f.write(u'</gml:coordinates></gml:LineString></ogr:geometryProperty>\n')
#Finishes the feature
f.write(u'<ogr:cat>13</ogr:cat>\n')
f.write(u'</ogr:sample>\n')
f.write(u'</gml:featureMember>\n')
#Finished the GML
f.write(u'</ogr:FeatureCollection>')
f.close()

#Imports GML to GRASSS
print gscript.read_command('v.in.ogr', input=DATAPATH + '/search/temp/out_polyline.gml', output='out_polyline', flags='o', overwrite=True)
#Exports SHP from imported GML
print gscript.read_command('v.out.ogr', input='out_polyline', output=DATAPATH + '/search/shp/' + SECTOR + '.shp', overwrite=True)
