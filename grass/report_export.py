# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys
import subprocess
import math
import io
import csv

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
COUNT=int(sys.argv[3])
print "COUNT: " + str(COUNT)
AREAS=str(sys.argv[4])
AREASITEMS=AREAS.split('!')

#Imports sektory_group_selected.shp to grass layer sektory_group_selected_modified (may be modified by user)
print gscript.read_command('v.import', input=DATAPATH + '/pracovni/sektory_group_selected.shp', layer='sektory_group_selected', output='sektory_group_selected_modified', overwrite=True)

#Sets area of areas to zero
SUM_P1 = 0
SUM_P2 = 0
SUM_P3 = 0
SUM_P4 = 0
SUM_P5 = 0
SUM_P6 = 0
SUM_P7 = 0
SUM_P8 = 0
SUM_P9 = 0
SUM_P10 = 0

#Loops via all selected search sectors based on number of sectors
for i in xrange(1, COUNT+1):
    print i
    f = io.open(DATAPATH + '/pracovni/report.html.' + str(i), encoding='utf-8', mode='w')
    #vybrani jednoho sektoru dle poradi
    #Selects one sector based on order (attribute cats is from 1 to number of items)
    #print gscript.read_command('v.extract', input='sektory_group_selected_modified', output='sektory_group_selected_modified_' + str(i), where="cat='"+str(i)+"'", overwrite=True)
    #ziskani atributu plocha a label
    #Gets attribute plocha (area) and label
    #VALUES=gscript.read_command('v.db.select', map='sektory_group_selected_modified_' + str(i), columns='label,area_ha', flags="c")
    #Pipe is delimiter of v.db.select output
    #VALUESITEMS=VALUES.split('|')

    #zamaskovani rastru s vyuzitim polygonu sektoru
    #Mask working area based on are of current sector
    print gscript.read_command('r.mask', vector='sektory_group_selected_modified', where="cat='"+str(i)+"'", overwrite=True)

    #ziskani reportu - procenta ploch v sektoru
    #Gets stats for landuse areas in masked region
    REPORT=gscript.read_command('r.stats', input='landuse_type', separator='pipe', flags='plna')
    #Sets areas of types of areas to zero
    #TODO - vyjasnit zarazeni typu + mozna pouzit i letecke snimky - nejaká jednoduchá automaticka rizena klasifikace
    P1=0 #volny schudny bez porostu (louky, pole ) - nejsem schopen zatim z dat identifikovat, mozna dle data patrani, v zime bude pole bez porostu a louka asi taky
    P2=0 #volny schudny s porostem (louky, pole ) - zatim tedy bude vse s porostem
    P3=0 #volny obtizne schudny (hory, skaly, lomy) - v prostoru mam lomy, skaly asi taky nejsem zatim schopen identifikovat
    P4=0 #porost lehce pruchozi (les bez prekazek) - asi vsechn les, kde neni krovi
    P5=0 #porost obtizne pruchozi (houstiny, skaly) - asi les s krovinami
    P6=0 #zastavene uzemi mest a obci
    P7=0 #mestske parky a hriste s pohybem osob - pohyb osob nejsem schopen posoudit, tedy asi co je zahrada bude bez pohybu a co je park bude s pohybem
    P8=0 #mestske parky a hriste bez osob
    P9=0 #vodni plocha
    P10=0 #ostatni

    REPORTITEMS = REPORT.splitlines(False)

    #Decides for each type of area from REPORT in which category belongs
    for REPORTITEM in REPORTITEMS:
        REPORTITEMVALUES = REPORTITEM.split('|')
        if REPORTITEMVALUES[0] == '1':
            P1 = P1 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P1 = SUM_P1 + float(REPORTITEMVALUES[2])
        if REPORTITEMVALUES[0] == '2':
            P2 = P2 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P2 = SUM_P2 + float(REPORTITEMVALUES[2])
        if REPORTITEMVALUES[0] == '3':
            P3 = P3 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P3 = SUM_P3 + float(REPORTITEMVALUES[2])
        if REPORTITEMVALUES[0] == '4':
            P4 = P4 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P4 = SUM_P4 + float(REPORTITEMVALUES[2])
        if REPORTITEMVALUES[0] == '5':
            P5 = P5 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P5 = SUM_P5 + float(REPORTITEMVALUES[2])
        if REPORTITEMVALUES[0] == '6':
            P6 = P6 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P6 = SUM_P6 + float(REPORTITEMVALUES[2])
        if REPORTITEMVALUES[0] == '7':
            P7 = P7 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P7 = SUM_P7 + float(REPORTITEMVALUES[2])
        if REPORTITEMVALUES[0] == '8':
            P8 = P8 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P8 = SUM_P8 + float(REPORTITEMVALUES[2])
        if REPORTITEMVALUES[0] == '9':
            P9 = P9 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P9 = SUM_P9 + float(REPORTITEMVALUES[2])
        if REPORTITEMVALUES[0] == '10':
            P10 = P10 + float(REPORTITEMVALUES[3].split('%')[0])
            SUM_P10 = SUM_P10 + float(REPORTITEMVALUES[2])

    #Corect 100%
    if P1 > 100:
        P1 = 100
    if P2 > 100:
        P2 = 100
    if P3 > 100:
        P3 = 100
    if P4 > 100:
        P4 = 100
    if P5 > 100:
        P5 = 100
    if P6 > 100:
        P6 = 100
    if P7 > 100:
        P7 = 100
    if P8 > 100:
        P8 = 100
    if P9 > 100:
        P9 = 100
    if P10 > 100:
        P10 = 100

    #Writes output to the report
    f.write(u'<div id="a' + str(i) + 's">\n')
    f.write(u"<ul>\n")
    f.write(u"<li>volný schůdný bez porostu: " + str(P1) + " %</li>\n")
    f.write(u"<li>volný schůdný s porostem: " + str(P2) + " %</li>\n")
    f.write(u"<li>volný obtížně schůdný: " + str(P3) + " %</li>\n")
    f.write(u"<li>porost lehce průchozí: " + str(P4) + " %</li>\n")
    f.write(u"<li>porost obtížně průchozí: " + str(P5) + " %</li>\n")
    f.write(u"<li>zastavěné území měst a obcí: " + str(P6) + " %</li>\n")
    f.write(u"<li>městské parky a hřiště s pohybem osob: " + str(P7) + " %</li>\n")
    f.write(u"<li>městské parky a hřiště bez osob: " + str(P8) + " %</li>\n")
    f.write(u"<li>vodní plocha: " + str(P9) + " %</li>\n")
    f.write(u"<li>ostatní plochy: " + str(P10) + " %</li>\n")
    f.write(u"</ul>\n")
    f.write(u"</div>\n")

    # #Sets current number of units to zero
    # POCET_KPT = 0
    # POCET_PT = 0
    # POCET_PT_ALT = 0
    # POCET_KPT_ALT = 0
    #
    # #For each type of area is counted number of necessary search units
    # POCET_KPT = POCET_KPT + (((float(AREASITEMS[i]) / 100.0) * P1) / 45.0) #45 je plocha pro hledani jednim tymem
    # POCET_KPT_ALT = POCET_KPT_ALT + (((float(AREASITEMS[i]) / 100.0) * P1) / 45.0) #45 je plocha pro hledani jednim tymem
    # POCET_PT_ALT = POCET_PT_ALT + (((float(AREASITEMS[i]) / 100.0) * P1) / 30.0) #30 je plocha pro hledani jednim tymem
    #
    # POCET_KPT = POCET_KPT + (((float(AREASITEMS[i]) / 100.0) * P2) / 30.0) #30 je plocha pro hledani jednim tymem
    #
    # POCET_KPT = POCET_KPT + (((float(AREASITEMS[i]) / 100.0) * P3) / 20.0) #20 je plocha pro hledani jednim tymem
    #
    # POCET_KPT = POCET_KPT + (((float(AREASITEMS[i]) / 100.0) * P4) / 30.0) #30 je plocha pro hledani jednim tymem
    # POCET_PT_ALT = POCET_PT_ALT + (((float(AREASITEMS[i]) / 100.0) * P4) / 30.0) #30 je plocha pro hledani jednim tymem
    # POCET_KPT_ALT = POCET_KPT_ALT + (((float(AREASITEMS[i]) / 100.0) * P4) / 30.0) #30 je plocha pro hledani jednim tymem
    #
    # POCET_KPT = POCET_KPT + (((float(AREASITEMS[i]) / 100.0) * P5) / 20.0) #20 je plocha pro hledani jednim tymem
    #
    # POCET_PT = POCET_PT + (((float(AREASITEMS[i]) / 100.0) * P6) / 5.0) #5 je plocha pro hledani jednim tymem
    #
    # POCET_PT = POCET_PT + (((float(AREASITEMS[i]) / 100.0) * P7) / 15.0) #15 je plocha pro hledani jednim tymem
    #
    # POCET_PT = POCET_PT + (((float(AREASITEMS[i]) / 100.0) * P10) / 15.0)  # 15 je plocha pro hledani jednim tymem
    #
    # POCET_KPT = POCET_KPT + (((float(AREASITEMS[i]) / 100.0) * P8) / 20.0) #20 je plocha pro hledani jednim tymem
    # POCET_KPT_ALT = POCET_KPT_ALT + (((float(AREASITEMS[i]) / 100.0) * P8) / 20.0) #20 je plocha pro hledani jednim tymem
    # POCET_PT_ALT = POCET_PT_ALT + (((float(AREASITEMS[i]) / 100.0) * P8) / 15.0) #15 je plocha pro hledani jednim tymem
    #
    # POCET_VPT = 0
    # if P9 > 0:
    #     POCET_VPT = 1 #jeden tym pro vodni plochu
    #
    # POCET_APT = 0
    # if P1 > 0 or P2 > 0:
    #     POCET_APT = 1
    #
    # #Writes to the report
    # f.write(u"\n<p>Nasazení <strong>"
    #         + str(int(math.ceil(POCET_KPT))) + u" KPT, "
    #         + str(int(math.ceil(POCET_PT))) + u" PT, "
    #         + str(int(math.ceil(POCET_VPT))) + u" VPT, "
    #         + str(int(math.ceil(POCET_VPT))) + u" APT</strong> "
    #         + '<label class="rolldown" for ="a' + str(i) + 'nc">Podrobnosti</label>'
    #         + "</p>\n");
    # f.write(u'<input id="a' + str(i) + u'nc" type = "checkbox" style = "display: none" >\n')
    # f.write(u'<div id="a' + str(i) + 'n\">\n')
    # f.write(u"<ul>")
    # if math.ceil(POCET_KPT) > 0:
    #     f.write(u"<li>Vhodné nasadit " + str(int(
    #         math.ceil(POCET_KPT))) + u" Kynologických pátracích týmů (KPT) k propátraní do 3 hodin</li>\n");
    #     if math.ceil(POCET_KPT_ALT) > 0:
    #         f.write(u"<li>Je možné nahradit " + str(int(math.ceil(POCET_KPT_ALT))) + u" KPT " + str(
    #             math.ceil(POCET_PT_ALT)) + u" PT</li>\n");
    # if math.ceil(POCET_PT) > 0:
    #     f.write(u"<li>Vhodné nasadit " + str(int(
    #         math.ceil(POCET_PT))) + u" Pátracích týmů (PT) s dvaceti členy k propátraní do 3 hodin</li>\n");
    # if math.ceil(POCET_VPT) > 0:
    #     f.write(u"<li>Vhodné nasadit " + str(int(
    #         math.ceil(POCET_VPT))) + u" Vodních pátracích týmů (VPT) k propátraní do 3 hodin</li>\n");
    # if math.ceil(POCET_VPT) > 0:
    #     f.write(u"<li>Vhodné nasadit " + str(int(
    #         math.ceil(POCET_VPT))) + u" Vzdušný pátrací tým (APT). Helikoptéru nebo dron. Prostor obsahuje volné plochy bez porostu.</li>\n");
    # f.write(u"</ul>")
    # f.write(u"</div>")

    #export do SHP s nazvem dle atributu label
    #print gscript.read_command('v.out.ogr', input='sektory_group_selected_modified_' + str(i), output=DATAPATH +'/sektory/shp/', output_layer=str(VALUESITEMS[0]), output_type='line' overwrite=True)
    #Adds information from report to attribute of the layer
    #print gscript.read_command('v.db.addcolumn', map='sektory_group_selected_modified_' + str(i), columns='report varchar(255)')
    #print gscript.read_command('v.db.update', map='sektory_group_selected_modified_' + str(i), layer='1', column='report', value='KPT=' + str(math.ceil(POCET_KPT)) + ', PT='+ str(math.ceil(POCET_PT)) + ', VPT=' + str(math.ceil(POCET_VPT)) + ', APT=' + str(math.ceil(POCET_PT_ALT)))
    # funits = io.open(DATAPATH + '/pracovni/report.html.units.' + str(i), encoding='utf-8', mode='w')
    # funits.write(u'KPT=' + str(math.ceil(POCET_KPT)) + u', PT='+ str(math.ceil(POCET_PT)) + u', VPT=' + str(math.ceil(POCET_VPT)) + u', APT=' + str(math.ceil(POCET_PT_ALT)))
    # funits.close()
    # #Exports sector to the SHP
    # #print gscript.read_command('v.out.ogr', input='sektory_group_selected_modified_' + str(i), output=DATAPATH +'/sektory/shp/'+str(VALUESITEMS[0])+'.shp', output_layer=str(VALUESITEMS[0]), output_type='line', overwrite=True)
    #
    # #Increase the sums of number of units
    # SUM_POCET_KPT += math.ceil(POCET_KPT)
    # SUM_POCET_PT += math.ceil(POCET_PT)
    # SUM_POCET_VPT += math.ceil(POCET_VPT)
    # SUM_POCET_PT_ALT += math.ceil(POCET_KPT_ALT)
    # SUM_POCET_APT += math.ceil(POCET_APT)

    f.close()

#Removes mask to be ready for another calculations for whole area
print gscript.read_command('r.mask', flags="r")

#Sets area to ha
SUM_P1 = SUM_P1 / float(10000)
SUM_P2 = SUM_P2 / float(10000)
SUM_P3 = SUM_P3 / float(10000)
SUM_P4 = SUM_P4 / float(10000)
SUM_P5 = SUM_P5 / float(10000)
SUM_P6 = SUM_P6 / float(10000)
SUM_P7 = SUM_P7 / float(10000)
SUM_P8 = SUM_P8 / float(10000)
SUM_P9 = SUM_P9 / float(10000)
SUM_P10 = SUM_P10 / float(10000)

f = io.open(DATAPATH + '/pracovni/report.html.units', encoding='utf-8', mode='w')
#Reads numbers for existing search units from units.txt
CUR_KPT=0
CUR_PT=0
CUR_VPT=0
with open(PLUGIN_PATH + "/grass/units.txt", "rb") as fileInput:
    i=0
    for row in csv.reader(fileInput, delimiter=';'):
        unicode_row = [x.decode('utf8') for x in row]
        cur_count = int(unicode_row[0])
        if i == 0:  # Pes
            CUR_KPT = cur_count
        if i == 1:  # Rpjnice
            CUR_PT = cur_count
        if i == 5:  # Potápěč
            CUR_VPT = cur_count
        i=i+1

f.write(u'<div id="areas" class="fixed400">\n')
f.write(u"\n<h2>Typy povrchů</h2>\n");
f.write(u"<ul>\n")
f.write(u"<li>volný schůdný bez porostu: " + str(int(math.ceil(SUM_P1))) + " ha</li>\n")
f.write(u"<li>volný schůdný s porostem: " + str(int(math.ceil(SUM_P2))) + " ha</li>\n")
f.write(u"<li>volný obtížně schůdný: " + str(int(math.ceil(SUM_P3))) + " ha</li>\n")
f.write(u"<li>porost lehce průchozí: " + str(int(math.ceil(SUM_P4))) + " ha</li>\n")
f.write(u"<li>porost obtížně průchozí: " + str(int(math.ceil(SUM_P5))) + " ha</li>\n")
f.write(u"<li>zastavěné území měst a obcí: " + str(int(math.ceil(SUM_P6))) + " ha</li>\n")
f.write(u"<li>městské parky a hřiště s pohybem osob: " + str(int(math.ceil(SUM_P7))) + " ha</li>\n")
f.write(u"<li>městské parky a hřiště bez osob: " + str(int(math.ceil(SUM_P8))) + " ha</li>\n")
f.write(u"<li>vodní plocha: " + str(int(math.ceil(SUM_P9))) + " ha</li>\n")
f.write(u"<li>ostatní plochy: " + str(int(math.ceil(SUM_P10))) + " ha</li>\n")
f.write(u"</ul>\n")
f.write(u"</div>\n")

KPT = SUM_P2 + SUM_P3 + SUM_P5
KPT_PT = SUM_P1 + SUM_P4 + SUM_P8
f.write(u'<div id="teams" class="fixed400">\n')
f.write(u"<h2>KPT</h2>\n")
f.write(u"<p>Plocha pro pátrání vhodná pro KPT je " + str(int(math.ceil(KPT + KPT_PT))) + " ha.\n")
f.write(u"<p>K dispozici je " + str(CUR_KPT) + " KPT.\n")
P2_P3_P5_KPT = float(SUM_P2) / float(7) + float(SUM_P3) / float(4) + float(SUM_P5) / float(4)
P1_P4_P8_KPT = float(SUM_P1) / float(10) + float(SUM_P4) / float(7) + float(SUM_P8) / float(5)
if CUR_KPT > 0:
    f.write(u"<p>Oblast propátrají přibližně za " + str(int(math.ceil((P2_P3_P5_KPT + P1_P4_P8_KPT) / float(CUR_KPT)))) + " h.\n")
if KPT_PT > 0:
    P1_P4_P8_PT = float(SUM_P1) / (float(7) / float(20)) + float(SUM_P4) / (float(7) / float(20)) + float(SUM_P8) / (float(5) / float(20))
    f.write(u"<p>Součástí je prostor, kde je možno KPT nahradit PT. Jedná se o " + str(int(math.ceil(KPT_PT))) + " ha.\n")
if (SUM_P2 + SUM_P1) > 0:
    f.write(u"<p>Součástí je prostor vhodný pro APT (vrtulník, dron) o rozloze " + str(int(math.ceil(SUM_P2 + SUM_P1))) + " ha.\n")

PT = SUM_P6 + SUM_P7 + SUM_P10
f.write(u"<h2>PT</h2>\n")
f.write(u"<p>Plocha pro pátrání vhodná pro PT je " + str(round(PT)) + " ha.\n")
f.write(u"<p>K dispozici je " + str(CUR_PT) + " osob pro PT.\n")
if CUR_PT > 0:
    P6_P7_P10_PT = float(SUM_P6) / (float(1) / float(20)) + float(SUM_P7) / (float(5) / float(20)) + float(SUM_P10) / (float(5) / float(20))
    f.write(u"<p>Oblast propátrají přibližně za " + str(int(math.ceil(P6_P7_P10_PT / float(CUR_PT)))) + " h.\n")
else:
    f.write(u"<p>Nejsou k dispozici žádné PT. Je nutné nějaké zajistit.\n")

if SUM_P9 > 0:
    f.write(u"<h2>VPT</h2>\n")
    f.write(u"<p>Vodní plochy v oblasti mají " + str(int(math.ceil(SUM_P9))) + " ha.\n")
    if CUR_VPT > 0:
        #TODO count time for divers
        A = 100 #placeholder
    else:
        f.write(u"<p>Nejsou k dispozici žádné VPT. Je nutné nějaké zajistit.\n")

f.write(u"</div>\n")

maxtime = 3
if os.path.isfile(PLUGIN_PATH + "/grass/maxtime.txt"):
    try:
        maxtime = int(open(PLUGIN_PATH + "/grass/maxtime.txt", 'r').read())
    except ValueError:
        maxtime = 3

if maxtime <= 0:
    maxtime = 3

f.write(u'<div id="time" class="fixed400">\n')
f.write(u"<h2>Propátrání do stanoveného času</h2>\n")
f.write(u"\n<p>K propátrání do " + str(int(maxtime)) + u" hodin potřebujete:</p>\n")
f.write(u"\n<ul>\n")
f.write(u"\n<li>" + str(int(math.ceil((P2_P3_P5_KPT + P1_P4_P8_KPT) / float(maxtime)))) + u" KPT</li>\n")
f.write(u"\n<li>" + str(int(math.ceil((P6_P7_P10_PT) / float(maxtime)))) + u" PT</li>\n")
if SUM_P9 > 0:
    f.write(u"\n<li>Minimálně jeden VPT</li>\n")
if (SUM_P2 + SUM_P1) > 0:
    f.write(u"\n<li>Minimálně jeden APT</li>\n")
f.write(u"\n</ul>\n")
f.write(u"</div>\n")

    # for field in unicode_row:
        #     if j == 0:
        #         cur_count = int(field)
        #         j=j+1
        #         #Dog
        #         if float(SUM_POCET_KPT) > 0:
        #             if i == 0: #Pes
        #                 if cur_count != 0:
        #                     cur_pomer = float(SUM_POCET_KPT) / float(cur_count)
        #                     f.write(u"\n<p>K dispozici je " + str(cur_count) + u" KPT</p>\n");
        #                     f.write(u"\n<p>Oblast prohledají přibližně za " + str(math.ceil(cur_pomer * 3)) + u" hodin</p>\n");
        #                 else:
        #                     f.write(u"\n<p>K dispozici není žádný KPT. Je nutné využít náhradu.</p>\n");
        #         #Search team
        #         if float(SUM_POCET_PT) > 0:
        #             if i == 1: #Rojnice
        #                 if cur_count != 0:
        #                     cur_pomer = float(SUM_POCET_PT) / (float(cur_count) / float(20))
        #                     f.write(u"\n<p>K dispozici je " + str(cur_count) + u" lidí pro PT</p>\n");
        #                     f.write(u"\n<p>Oblast prohledají přibližně za " + str(math.ceil(cur_pomer * 3)) + u" hodin</p>\n");
        #                     #TODO Dořešit SUM_POCET_PT_ALT
        #                 else:
        #                     f.write(u"\n<p>K dispozici není žádný člověk pro PT. Je nutné nějaké zajistit.</p>\n");
        #         #Diver
        #         if float(SUM_POCET_VPT) > 0:
        #             if i == 5: #Potápěč
        #                 if cur_count != 0:
        #                     cur_pomer = float(SUM_POCET_VPT) / (float(cur_count) / float(2))
        #                     f.write(u"\n<p>K dispozici je " + str(cur_count) + u" potápěčů pro VPT</p>\n");
        #                     f.write(u"\n<p>Oblast prohledají přibližně za " + str(math.ceil(cur_pomer * 3)) + u" hodin</p>\n");
        #                 else:
        #                     f.write(u"\n<p>K dispozici není žádný potápěč. Je nutné nějaké zajistit.</p>\n");
        #         # air (helicopter, dron)
        #         if float(SUM_POCET_APT) > 0:
        #             # TODO check for helicopter - we do not have category yet
        #             if i == 0:
        #                 f.write(u"\n<p>Vhodné nasadit vzdušný pátrací tým (APT). Helikoptéru nebo dron. Prostor obsahuje volné plochy bez porostu.</p>\n");
        # i=i+1
