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

#Imports current sectors to have labels available
print gscript.read_command('v.in.ogr', output='sectors_group', input=DATAPATH+'/pracovni', layer='sektory_group', overwrite=True, flags="o")