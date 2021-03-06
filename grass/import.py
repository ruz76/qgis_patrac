#!/usr/bin/env python

import os
import sys
import subprocess

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
grass7bin_lin = 'grass74'
# Mac OS X
# this is TODO
grass7bin_mac = '/Applications/GRASS/GRASS-7.0.app/'

# DATA
# define GRASS DATABASE
# add your path to grassdata (GRASS GIS database) directory
DATAPATH=str(sys.argv[1]) 
gisdb = DATAPATH + "/grassdata"
# the following path is the default path on MS Windows
# gisdb = os.path.join(os.path.expanduser("~"), "Documents/grassdata")

# specify (existing) location and mapset
location = "jtsk"
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

PLUGIN_PATH=str(sys.argv[2]) 
XMIN=float(sys.argv[3])
YMIN=float(sys.argv[4])
XMAX=float(sys.argv[5])
YMAX=float(sys.argv[6])
DATAINPUTPATH=str(sys.argv[7])

#Sets the region for export
#g.region e=-641060.857143 w=-658275.142857 n=-1036549.0 s=-1046549.0
print gscript.read_command('g.region', e=XMAX, w=XMIN, n=YMAX, s=YMIN, res='5')
#Imports landuse
#Bin would be better (size is smaller, export is faster), but there are some problems with import
print gscript.read_command('r.in.ascii', output='landuse', input=DATAPATH+'/grassdata/landuse.ascii', overwrite=True)
#Imports friction_slope
#Bin would be better (size is smaller, export is faster), but there are some problems with import
print gscript.read_command('r.in.ascii', output='friction_slope', input=DATAPATH+'/grassdata/friction_slope.ascii', overwrite=True)
#Problem with null data - set to 10000
# print gscript.read_command('r.null', map='friction_slope', null='10000')
#Imports sectors and select them according to Extent
#Bin would be better (size is smaller, export is faster), but there are some problems with import
#Imports friction
print gscript.read_command('r.in.ascii', output='friction', input=DATAPATH+'/grassdata/friction.ascii', overwrite=True)
#Imports dem
print gscript.read_command('r.in.ascii', output='dem', input=DATAPATH+'/grassdata/dem.ascii', overwrite=True)

#If the data are from ZABAGED
if os.path.isfile(DATAINPUTPATH+'/vektor/ZABAGED/line_x/merged_polygons_groupped.shp'):
    print gscript.read_command('v.in.ogr', output='sectors_group', input=DATAINPUTPATH+'/vektor/ZABAGED/line_x', snap=1, layer='merged_polygons_groupped', spatial=str(XMIN)+','+str(YMIN)+','+str(XMAX)+','+str(YMAX), overwrite=True, flags="o")
    print gscript.read_command('r.reclass', input='landuse', output='landuse_type', rules=PLUGIN_PATH+'/grass/landuse_type_zbg.rules')

#If the data are from OSM
if os.path.isfile(DATAINPUTPATH+'/vektor/OSM/line_x/merged_polygons_groupped.shp'):
    print gscript.read_command('v.in.ogr', output='sectors_group', input=DATAINPUTPATH+'/vektor/OSM/line_x', snap=1, layer='merged_polygons_groupped', spatial=str(XMIN)+','+str(YMIN)+','+str(XMAX)+','+str(YMAX), overwrite=True, flags="o")
    print gscript.read_command('r.reclass', input='landuse', output='landuse_type', rules=PLUGIN_PATH+'/grass/landuse_type_osm.rules')

#Computes areas
print gscript.read_command('v.db.addcolumn', map='sectors_group', layer='1', columns='area_ha DOUBLE PRECISION')
print gscript.read_command('v.to.db', map='sectors_group', layer='1', option='area', units='hectares', columns='area_ha')
#Adds label column
print gscript.read_command('v.db.addcolumn', map='sectors_group', layer='1', columns='label VARCHAR(50)')
#Exports sectors with comuted areas
print gscript.read_command('v.out.ogr', format='ESRI_Shapefile', input='sectors_group', output=DATAPATH +'/pracovni/sektory_group_selected.shp', overwrite=True)
print gscript.read_command('v.out.ogr', format='ESRI_Shapefile', input='sectors_group', output=DATAPATH +'/pracovni/sektory_group.shp', overwrite=True)