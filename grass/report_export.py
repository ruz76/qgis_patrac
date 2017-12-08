# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys
import subprocess
import math
import webbrowser
import io

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
COUNT=int(sys.argv[3])
print "COUNT: " + str(COUNT)
print gscript.read_command('v.import', input=DATAPATH + '/pracovni/sektory_group_selected.shp', layer='sektory_group_selected', output='sektory_group_selected_modified', overwrite=True)

header = io.open(DATAPATH + '/pracovni/report_header.html', encoding='utf-8', mode='r').read()
f = io.open(DATAPATH + '/pracovni/report.html', encoding='utf-8', mode='w')
f.write(header)
f.write(u'<h1>REPORT</h1>\n')


for i in xrange(1, COUNT+1):
    print i
    #vybrani jednoho sektoru dle poradi
    print gscript.read_command('v.extract', input='sektory_group_selected_modified', output='sektory_group_selected_modified_' + str(i), where="cat='"+str(i)+"'", overwrite=True)
    #ziskani atributu plocha a label
    VALUES=gscript.read_command('v.db.select', map='sektory_group_selected_modified_' + str(i), columns='label,area_ha', flags="c")
    VALUESITEMS=VALUES.split('|')
    #export do SHP s nazvem dle atributu label
    #print gscript.read_command('v.out.ogr', input='sektory_group_selected_modified_' + str(i), output=DATAPATH +'/sektory/shp/', output_layer=str(VALUESITEMS[0]), output_type='line' overwrite=True)
    print gscript.read_command('v.out.ogr', input='sektory_group_selected_modified_' + str(i), output=DATAPATH +'/sektory/shp/'+str(VALUESITEMS[0])+'.shp', output_layer=str(VALUESITEMS[0]), output_type='line', overwrite=True)

    #zamaskovani rastru s vyuzitim polygonu sektoru
    print gscript.read_command('r.mask', vector='sektory_group_selected_modified', where="cat='"+str(i)+"'", overwrite=True)

    #ziskani reportu - procenta ploch v sektoru
    REPORT=gscript.read_command('r.stats', input='landuse', separator='pipe', flags='pln')
    f.write(u"<hr/>\n")
    f.write(u"<h2>SEKTOR " + str(VALUESITEMS[0]) + "</h2>\n")
    f.write(u"<p>PLOCHA " + str(int(VALUESITEMS[1])) + " ha</p>\n")
    f.write(u"<h3>Typy povrchu</h3>\n")
    #TODO - prevod reportu do UTF - nejde
    #f.write(u"<pre>" + str(REPORT).encode('utf-8') + u"</pre>\n")
    
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

    REPORTITEMS = REPORT.splitlines(False)

    #prepocet ploch v sektoru dle kategorii nasazeni tymu
    for REPORTITEM in REPORTITEMS:
        REPORTITEMVALUES = REPORTITEM.split('|')
        if REPORTITEMVALUES[0] == '1': #1:Zastavena plocha (AREZAS)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '2': #2:Arealy (ARUCZA)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '3': #3:Hrbitovy (HRBITO)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '4': #4:Kolejiste (KOLEJI)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '5': #5:Letiste (LETISTE)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '6': #6:Nezjisteno (LPKOSO) - zarazeno do P1 - mozna chyba
            P1 = P1 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '7': #7:Louky, pastviny, kroviny (LPKROV)
            P5 = P5 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '8': #8:Louky, pastviny, stromy (LPSTROM)
            P4 = P4 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '9': #9:Nezjisteno (OBLEDR)
            P1 = P1 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '10': #10:Odpocivadla (ODPOCI)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '11': #11:Orna puda (ORNAPU)
            P2 = P2 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '12': #12:Ostani plochy u silnic (OSPLSI)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '13': #13:Lom (POTELO)
            P3 = P3 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '14': #14:Nezjisteno (PRSTPR)
            P1 = P1 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '15': #15:Sad, zahrada (SADZAH)
            P4 = P4 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '16': #16:Skladka (SKLADK)
            P3 = P3 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '17': #17:Travnaty povrch (TRTRPO)
            P1 = P1 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '18': #18:Vodni plocha (VODPLO)
            P9 = P9 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '19': #19:Zahrady, parky (ZAHPAR)
            P7 = P7 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '100': #100:Baziny, mocaly (BAZMOC)
            P3 = P3 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '101': #101:Budovy, bloky budov (BUBLBU)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '102': #102:Chladici veze (CHLVEZ)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '103': #103:Chmelnice (CHMELN)
            P4 = P4 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '104': #104:Elektrarna (ELEKTR)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '105': #105:Halda, odval (HALODV)
            P3 = P3 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '106': #106:Skleniky (KUSLFO)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '107': #107:Raseliniste (RASELI)
            P3 = P3 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '108': #108:Nezjisteno (ROZTRA)
            P1 = P1 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '109': #109:Budovy (ROZZRI)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '110': #110:Sesuv (SESPUD)
            P3 = P3 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '111': #111:Silo (SILO)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '112': #112:Obora (SKAUTV)
            P5 = P5 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '113': #113:Usazovaci nadrz (USNAOD)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '114': #114:Budovy na nadrazi (VANAZA)
            P6 = P6 + float(REPORTITEMVALUES[2].split('%')[0])
        if REPORTITEMVALUES[0] == '115': #115:Vinice (VINICE)
            P4 = P4 + float(REPORTITEMVALUES[2].split('%')[0])

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
    f.write(u"</ul>\n")
    
    POCET_KPT = 0
    POCET_PT = 0
    POCET_PT_ALT = 0
    POCET_KPT_ALT = 0

    POCET_KPT = POCET_KPT + (((int(VALUESITEMS[1]) / 100.0) * P1) / 45.0) #45 je plocha pro hledani jednim tymem
    POCET_KPT_ALT = POCET_KPT_ALT + (((int(VALUESITEMS[1]) / 100.0) * P1) / 45.0) #45 je plocha pro hledani jednim tymem
    POCET_PT_ALT = POCET_PT_ALT + (((int(VALUESITEMS[1]) / 100.0) * P1) / 30.0) #30 je plocha pro hledani jednim tymem

    POCET_KPT = POCET_KPT + (((int(VALUESITEMS[1]) / 100.0) * P2) / 30.0) #30 je plocha pro hledani jednim tymem

    POCET_KPT = POCET_KPT + (((int(VALUESITEMS[1]) / 100.0) * P3) / 20.0) #20 je plocha pro hledani jednim tymem

    POCET_KPT = POCET_KPT + (((int(VALUESITEMS[1]) / 100.0) * P4) / 30.0) #30 je plocha pro hledani jednim tymem
    POCET_PT_ALT = POCET_PT_ALT + (((int(VALUESITEMS[1]) / 100.0) * P4) / 30.0) #30 je plocha pro hledani jednim tymem
    POCET_KPT_ALT = POCET_KPT_ALT + (((int(VALUESITEMS[1]) / 100.0) * P4) / 30.0) #30 je plocha pro hledani jednim tymem
    
    POCET_KPT = POCET_KPT + (((int(VALUESITEMS[1]) / 100.0) * P5) / 20.0) #20 je plocha pro hledani jednim tymem

    POCET_PT = POCET_PT + (((int(VALUESITEMS[1]) / 100.0) * P6) / 5.0) #5 je plocha pro hledani jednim tymem

    POCET_PT = POCET_PT + (((int(VALUESITEMS[1]) / 100.0) * P7) / 15.0) #15 je plocha pro hledani jednim tymem

    POCET_KPT = POCET_KPT + (((int(VALUESITEMS[1]) / 100.0) * P8) / 20.0) #20 je plocha pro hledani jednim tymem
    POCET_KPT_ALT = POCET_KPT_ALT + (((int(VALUESITEMS[1]) / 100.0) * P8) / 20.0) #20 je plocha pro hledani jednim tymem
    POCET_PT_ALT = POCET_PT_ALT + (((int(VALUESITEMS[1]) / 100.0) * P8) / 15.0) #15 je plocha pro hledani jednim tymem

    POCET_VPT = 0
    if P9 > 0:
        POCET_VPT = 1 #jeden tym pro vodni plochu

    f.write(u"\n<h3>Nasazení</h3>\n");
    f.write(u"<p>Vhodné nasadit " + str(math.ceil(POCET_KPT)) + u" Kynologických pátracích týmů (KPT)</p>\n");
    f.write(u"<p>Vhodné nasadit " + str(math.ceil(POCET_PT)) + u" Pátracích týmů (PT)</p>\n");
    f.write(u"<p>Vhodné nasadit " + str(math.ceil(POCET_VPT)) + u" Vodních pátrcích týmů (VPT)</p>\n");
    f.write(u"<p>Je možné nahradit " + str(math.ceil(POCET_KPT_ALT)) + u" KPT " + str(math.ceil(POCET_PT_ALT)) + u" PT</p>\n");

print gscript.read_command('r.mask', flags="r")

footer = io.open(DATAPATH + '/pracovni/report_footer.html', encoding='utf-8', mode='r').read()
f.write(footer)
f.close()
webbrowser.open("file://" + DATAPATH + "/pracovni/report.html")
