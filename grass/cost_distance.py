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
grass7bin_lin = 'grass72'
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
PLACE_ID=sys.argv[3]
TYPE=int(sys.argv[4])

#print gscript.read_command('r.mask', flags="r")

print gscript.read_command('v.in.ascii', input=PLUGIN_PATH + '/grass/coords.txt', output='coords', separator='comma' , overwrite=True)
print gscript.read_command('v.to.rast', input='coords', output='coords', use='cat' , overwrite=True)
print gscript.read_command('v.in.ogr', input=PLUGIN_PATH + '/grass/radial.csv', output='radial', flags='o' , overwrite=True)
print gscript.read_command('v.to.rast', input='radial', output='radial', use='cat', overwrite=True)
print gscript.read_command('r.reclass', input='radial', output='radial' + PLACE_ID, rules=PLUGIN_PATH + '/grass/azimuth_reclass.rules', overwrite=True)
print gscript.read_command('r.mapcalc', expression='friction_slope_radial' + PLACE_ID + ' = friction_slope + radial' + PLACE_ID, overwrite=True)

distances_f=open(PLUGIN_PATH + "/grass/distances.txt")
lines=distances_f.readlines()
DISTANCES=lines[TYPE]

#Metodika Hill
print gscript.read_command('r.buffer', input='coords', output='distances' + PLACE_ID, distances=DISTANCES , overwrite=True)
#Metodika Pastorkova
print gscript.read_command('r.cost', input='friction_slope_radial' + PLACE_ID, output='cost' + PLACE_ID, start_points='coords' , overwrite=True)

os.remove(PLUGIN_PATH + '/grass/rules_percentage.txt')
rules_percentage_f = open(PLUGIN_PATH + '/grass/rules_percentage.txt', 'w')
print gscript.read_command('r.mapcalc', expression='distances' + PLACE_ID + '_costed = 0', overwrite=True)

cat=2
variables = [10, 20, 30, 40, 50, 60, 70, 80, 95]
for i in variables:
    print i
    f = open(PLUGIN_PATH + '/grass/rules.txt', 'w')
    f.write(str(cat) + ' = 1\n')
    f.write('end')
    f.close()
    print gscript.read_command('r.reclass', input='distances' + PLACE_ID, output='distances' + PLACE_ID + '_' + str(i), rules=PLUGIN_PATH + '/grass/rules.txt', overwrite=True)
    print gscript.read_command('r.mapcalc', expression='cost' + PLACE_ID + '_distances_' + str(i) + ' = distances' + PLACE_ID + '_' + str(i) + ' * cost' + PLACE_ID, overwrite=True)
    stats = gscript.parse_command('r.univar', map='cost' + PLACE_ID + '_distances_' + str(i), flags='g')
    MIN = float(stats['min'])
    print str(MIN)
    MAX = float(stats['max'])
    print str(MAX)
    rules_percentage_f.write(str(MIN) + ' thru ' + str(MAX) + ' = ' + str(i) + '\n')
    cat = cat + 1

rules_percentage_f.write('end')
rules_percentage_f.close()

print gscript.read_command('r.reclass', input='cost' + PLACE_ID, output='distances' + PLACE_ID + '_costed', rules=PLUGIN_PATH + '/grass/rules_percentage.txt', overwrite=True)


