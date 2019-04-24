# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Patrac
# ---------------------------------------------------------
# Podpora pátrání po pohřešované osobě
#
# Copyright (C) 2017-2019 Jan Růžička (jan.ruzicka.vsb@gmail.com)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/copyleft/gpl.html>. You can also obtain it by writing
# to the Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.
#
# The sliders and layer transparency are based on https://github.com/alexbruy/raster-transparency
# ******************************************************************************


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from ui.ui_patracdockwidgetbase import Ui_PatracDockWidget
from ui.ui_settings import Ui_Settings
from ui.ui_gpx import Ui_Gpx
from ui.ui_message import Ui_Message
from ui.ui_coords import Ui_Coords
from ui.ui_point_tool import PointMapTool

import os
import sys
import subprocess
from glob import glob
# from osgeo import ogr
# from osgeo import gdal
import time
import urllib2
from urllib2 import quote
import math
import socket
from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime

import csv, io
import webbrowser
import filecmp
import uuid

from PyQt4.QtCore import QSettings

#from PyQt4.QtCore import QCoreApplication
#QCoreApplication.processEvents()

class ZPM_Raster():
    def __init__(self, name, distance, xmin, ymin, xmax, ymax):
        self.name = name
        self.distance = distance
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax


class PatracDockWidget(QDockWidget, Ui_PatracDockWidget, object):
    def __init__(self, plugin):

        self.plugin = plugin
        self.iface = self.plugin.iface
        self.canvas = self.plugin.iface.mapCanvas()
        self.maxVal = 100
        self.minVal = 0
        self.serverUrl = 'http://gisak.vsb.cz/patrac/mserver.php?'

        userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "python/plugins/qgis_patrac"
        systemPluginPath = QgsApplication.prefixPath() + "python/plugins/qgis_patrac"
        if QFileInfo(userPluginPath).exists():
            self.pluginPath = userPluginPath
        else:
            self.pluginPath = systemPluginPath

        QDockWidget.__init__(self, None)
        self.setupUi(self)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # connect signals and slots
        self.chkManualUpdate.stateChanged.connect(self.__toggleRefresh)
        self.btnRefresh.clicked.connect(self.updatePatrac)

        # Button GetArea
        self.btnGetArea.clicked.connect(self.runExpertGetArea)

        # Sliders
        self.sliderStart.valueChanged.connect(self.__updateSpinStart)
        self.spinStart.valueChanged.connect(self.__updateSliderStart)
        self.sliderEnd.valueChanged.connect(self.__updateSpinEnd)
        self.spinEnd.valueChanged.connect(self.__updateSliderEnd)

        # Button of places management
        self.tbtnDefinePlaces.clicked.connect(self.definePlaces)
        # Button of GetSectors
        self.tbtnGetSectors.clicked.connect(self.runExpertGetSectors)

        self.tbtnRecalculateSectors.clicked.connect(self.recalculateSectorsExpert)
        self.tbtnExportSectors.clicked.connect(self.exportSectors)
        self.tbtnReportExportSectors.clicked.connect(self.runExpertReportExportSectors)
        self.tbtnShowSettings.clicked.connect(self.showSettings)
        self.guideShowSettings.clicked.connect(self.showSettings)
        self.tbtnImportPaths.clicked.connect(self.showImportGpx)
        self.tbtnShowSearchers.clicked.connect(self.showPeople)
        self.tbtnShowSearchersTracks.clicked.connect(self.showPeopleTracks)
        self.tbtnShowMessage.clicked.connect(self.showMessage)

        self.tbtnInsertFinal.clicked.connect(self.insertFinal)
        self.guideInsertFinal.clicked.connect(self.insertFinal)

        # Dialogs and tools are defined here
        self.settingsdlg = Ui_Settings(self.pluginPath, self)
        self.coordsdlg = Ui_Coords()
        self.pointtool = PointMapTool(self.plugin.iface.mapCanvas())

        self.setStepsConnection()

        # Help show
        self.helpShow.clicked.connect(self.showHelp)

        self.currentTool = self.iface.mapCanvas().mapTool()
        self.personType = 1

    def showHelp(self):
        webbrowser.open("file://" + self.pluginPath + "/doc/intro.html")

    def getPluginPath(self):
        return self.pluginPath

    def setStepsConnection(self):
        # Autocompleter fro search of municipalities
        self.setCompleter(self.guideMunicipalitySearch)
        self.guideMunicipalitySearch.returnPressed.connect(self.runGuideMunicipalitySearch)

        # Step 1 Next
        self.guideStep1Next.clicked.connect(self.runGuideMunicipalitySearch)

        # Step 2 Next
        self.guideStep2Next.clicked.connect(self.runGuideStep2Next)

        # Step 3 Next
        self.guideStep3Next.clicked.connect(self.runGuideStep3Next)

        # Step 4 Next
        self.guideStep4Next.clicked.connect(self.runGuideStep4Next)

        # Step 5 Next
        self.guideStep5Next.clicked.connect(self.runGuideStep5Next)

        # Step 6 Show Report
        self.guideShowReport.clicked.connect(self.showReport)

    def getProcessRadial(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        processRadial = open(DATAPATH + '/config/radialsettings.txt', 'r').read()
        processRadial = processRadial.strip()
        if (processRadial == "0"):
            return False
        else:
            return True

    def getWeightLimit(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        weightLimit = open(DATAPATH + '/config/weightlimit.txt', 'r').read()
        weightLimit = weightLimit.strip()
        if weightLimit.isdigit():
            return int(weightLimit)
        else:
            return 1

    def getLength(self):
        li = self.iface.legendInterface()
        sl = li.selectedLayers(True)
        info = ""
        for lyr in sl:
            line_length = 0
            for feature in lyr.getFeatures():
                sourceCrs = QgsCoordinateReferenceSystem(4326)
                destCrs = QgsCoordinateReferenceSystem(2154)
                tr = QgsCoordinateTransform(sourceCrs, destCrs)
                geom = feature.geometry()
                geom.transform(tr)
                line_length += geom.length()
            str_line_length = str(round(line_length))
            index = len(str_line_length) - 5
            info += lyr.name() + ": " + str_line_length[:index] + " km " + str_line_length[index:][:-2] + " m\n"
        QMessageBox.information(None, "DELKY:", info)

    def pomAddRasters(self):
        KRAJ_DATA_PATH = "/data/patracdata/kraje/vy"
        self.addZPMRasters(KRAJ_DATA_PATH, "100", 2, 80000, 1000000)
        self.addZPMRasters(KRAJ_DATA_PATH, "50", 2, 40000, 80000)
        self.addZPMRasters(KRAJ_DATA_PATH, "25", 2, 20000, 40000)
        self.addZPMRasters(KRAJ_DATA_PATH, "16", 9, 10000, 20000)
        self.addZPMRasters(KRAJ_DATA_PATH, "8", 9, 5000, 10000)
        self.addZPMRasters(KRAJ_DATA_PATH, "3", 81, 1, 5000)

    def addZPMRasters(self, KRAJ_DATA_PATH, Level, Layers_Count, minscaledenominator, maxscaledenominator):
        XCENTER = self.canvas.extent().center().x()
        YCENTER = self.canvas.extent().center().y()
        with open(KRAJ_DATA_PATH + "/raster/ZPM_" + Level + "tis/metadata.csv", "rb") as fileInput:
            rasters = list()
            rasters_count = 0
            for row in csv.reader(fileInput, delimiter=';'):
                distance = math.hypot(XCENTER - float(row[1]), YCENTER - float(row[2]))
                raster = ZPM_Raster(row[0], distance, row[3], row[4], row[5], row[6])
                # print "Not ordered " + raster.name + " " + str(raster.distance)
                if rasters_count > 0:
                    counter = 0
                    inserted = False
                    for x in rasters:
                        if x.distance > distance:
                            rasters.insert(counter, raster)
                            inserted = True
                            break
                        counter = counter + 1
                    if not inserted:
                        rasters.append(raster)
                else:
                    rasters.append(raster)
                rasters_count = rasters_count + 1
            for x in range(0, Layers_Count):
                if x < len(rasters):
                    raster = rasters[x]
                    # print "Ordered " + raster.name + " " + str(raster.distance)
                    self.addRasterLayerToGroup(KRAJ_DATA_PATH + "/raster/ZPM_" + Level + "tis/" + raster.name,
                                               raster.name,
                                               "zbg_" + Level + "tis_orig", minscaledenominator, maxscaledenominator)

    def addAllZPMRasters(self, KRAJ_DATA_PATH):
        self.addZPMRasters(KRAJ_DATA_PATH, "100", 4, 80000, 1000000)
        self.addZPMRasters(KRAJ_DATA_PATH, "50", 4, 40000, 80000)
        self.addZPMRasters(KRAJ_DATA_PATH, "25", 6, 20000, 40000)
        self.addZPMRasters(KRAJ_DATA_PATH, "16", 9, 10000, 20000)
        self.addZPMRasters(KRAJ_DATA_PATH, "8", 9, 5000, 10000)
        self.addZPMRasters(KRAJ_DATA_PATH, "3", 72, 1, 5000)
        self.iface.messageBar().clearWidgets()

    def copyTemplate(self, NEW_PROJECT_PATH, TEMPLATES_PATH, NAMESAFE):
        if not os.path.isdir(NEW_PROJECT_PATH):
            os.mkdir(NEW_PROJECT_PATH)

            # sets the settings to zero, so no radial and no weight limit is used
            os.mkdir(NEW_PROJECT_PATH + "/config")
            f = open(NEW_PROJECT_PATH + '/config/weightlimit.txt', 'w')
            f.write("0")
            f.close()
            f = open(NEW_PROJECT_PATH + '/config/radialsettings.txt', 'w')
            f.write("0")
            f.close()

            copy(TEMPLATES_PATH + "/projekt/clean.qgs", NEW_PROJECT_PATH + "/" + NAMESAFE + ".qgs")
            os.mkdir(NEW_PROJECT_PATH + "/pracovni")
            for file in glob(TEMPLATES_PATH + '/projekt/pracovni/*'):
                copy(file, NEW_PROJECT_PATH + "/pracovni/")
            os.mkdir(NEW_PROJECT_PATH + "/search")
            copy(TEMPLATES_PATH + "/projekt/search/sectors.txt", NEW_PROJECT_PATH + "/search/")
            os.mkdir(NEW_PROJECT_PATH + "/search/gpx")
            os.mkdir(NEW_PROJECT_PATH + "/search/shp")
            copy(TEMPLATES_PATH + "/projekt/search/shp/style.qml", NEW_PROJECT_PATH + "/search/shp/")
            os.mkdir(NEW_PROJECT_PATH + "/search/temp")
            os.mkdir(NEW_PROJECT_PATH + "/sektory")
            os.mkdir(NEW_PROJECT_PATH + "/sektory/gpx")
            os.mkdir(NEW_PROJECT_PATH + "/sektory/shp")
            os.mkdir(NEW_PROJECT_PATH + "/sektory/pdf")
            os.mkdir(NEW_PROJECT_PATH + "/sektory/styles")
            for file in glob(TEMPLATES_PATH + "/projekt/sektory/shp/*"):
                copy(file, NEW_PROJECT_PATH + "/sektory/shp/")
            for file in glob(TEMPLATES_PATH + "/projekt/sektory/styles/*"):
                copy(file, NEW_PROJECT_PATH + "/sektory/styles/")
            # copy(TEMPLATES_PATH + "/projekt/sektory/shp/style.qml", NEW_PROJECT_PATH + "/sektory/shp/")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata/jtsk")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata/jtsk/PERMANENT")
            # print TEMPLATES_PATH + '/grassdata/jtsk/PERMANENT'
            for file in glob(TEMPLATES_PATH + '/grassdata/jtsk/PERMANENT/*'):
                # print file
                copy(file, NEW_PROJECT_PATH + "/grassdata/jtsk/PERMANENT/")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata/wgs84")
            os.mkdir(NEW_PROJECT_PATH + "/grassdata/wgs84/PERMANENT")
            for file in glob(TEMPLATES_PATH + '/grassdata/wgs84/PERMANENT/*'):
                copy(file, NEW_PROJECT_PATH + "/grassdata/wgs84/PERMANENT/")

    def getSafeDirectoryName(self, name):
        name = name.lower()
        replace = ['a', 'c', 'd', 'e', 'e', 'i', 'n', 'o', 'r', 's', 't', 'u', 'u', 'y', 'z']
        position = 0
        for ch in [u'á', u'č', u'ď', u'ě', u'é', u'í', u'ň', u'ó', u'ř', u'š', u'ť', u'ú', u'ů', u'ý', u'ž']:
            if ch in name:
                name = name.replace(ch, replace[position])
            position = position + 1
        name = name.encode('ascii', 'replace').replace("?", "_").replace("(", "_").replace(")", "_").replace(" ",
                                                                                                             "_").replace(
            "\:", "_").replace("\.", "_")
        return name

    def openProjectSimple(self):
        # Tries to open simple project for generating search project
        simpleProjectPath = ''

        if os.path.isfile('C:/patracdata/cr/projekty/simple/simple.qgs'):
            simpleProjectPath = 'C:/patracdata/cr/projekty/simple/simple.qgs'
        if os.path.isfile('D:/patracdata/cr/projekty/simple/simple.qgs'):
            simpleProjectPath = 'D:/patracdata/cr/projekty/simple/simple.qgs'
        if os.path.isfile('E:/patracdata/cr/projekty/simple/simple.qgs'):
            simpleProjectPath = 'E:/patracdata/cr/projekty/simple/simple.qgs'
        if os.path.isfile('/data/patracdata/cr/projekty/simple/simple.qgs'):
            simpleProjectPath = '/data/patracdata/cr/projekty/simple/simple.qgs'

        if simpleProjectPath == '':
            QMessageBox.information(None, "CHYBA:",
                                    u"Nepodařilo se načíst výchozí projekt. Zkuste jej prosím načíst ručně.")
            return False
        else:
            project = QgsProject.instance()
            project.read(QFileInfo(simpleProjectPath))
            #QMessageBox.information(None, "INFO:",
            #                        u"Podařilo se načíst výchozí projekt. Vyhledejte znovu obec a vygenerujte projekt pro hledání.")

            return True

    def getRegion(self):
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if "okresy_pseudo.shp" in lyr.source():
                layer = lyr
                break

        for feature in layer.getFeatures():
            if (feature.geometry().contains(self.canvas.extent().center())):
                return feature["nk"]

        return None

    def getSimpleProjectDataPath(self):
        DATAPATH = ''
        if os.path.isfile('C:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'C:/patracdata/cr/projekty/simple/'
        if os.path.isfile('D:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'D:/patracdata/cr/projekty/simple/'
        if os.path.isfile('E:/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = 'E:/patracdata/cr/projekty/simple/'
        if os.path.isfile('/data/patracdata/cr/projekty/simple/simple.qgs'):
            DATAPATH = '/data/patracdata/cr/projekty/simple/'

        return DATAPATH

    def checkRegion(self, region):
        if region is not None:
            region = region.lower()
        else:
            QMessageBox.information(None, "CHYBA:",
                                    u"Extent mapy je mimo ČR. Nemám data nemohu pokračovat.")
            return None

        DATAPATH = self.getSimpleProjectDataPath()

        if DATAPATH == '':
            QMessageBox.information(None, "KRITICKÁ CHYBA:",
                                    u"Nepodařilo se najít adresář s daty. Nemohu pokračovat.")
            return None

        regionOut = None
        QgsMessageLog.logMessage(u"Region: " + region, "Patrac")
        if os.path.isfile(DATAPATH + '/../../../kraje/' + region + '/vektor/OSM/line_x/merged_polygons_groupped.shp'):
            regionOut = region
        if os.path.isfile(
                DATAPATH + '/../../../kraje/' + region + '/vektor/ZABAGED/line_x/merged_polygons_groupped.shp'):
            regionOut = region

        return regionOut

    def checkRegionExtent(self):
        if (self.canvas.extent().width() > 10000) or (self.canvas.extent().height() > 10000):
            reply = QMessageBox.question(self, u'Region',
                                         u'Region je příliš rozsáhlý. Výpočty budou pomalé. Chcete pokračovat?',
                                         QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                return True
            else:
                return False
        else:
            return True

    def runCreateProject(self):
        name = self.msearch.text()
        self.createProject(name)

    def runCreateProjectGuide(self, index):
        #name = self.guideMunicipalitySearch.text()
        self.createProject(index)

    def createProject(self, index):
        # Check if the project has okresy_pseudo.shp

        QgsMessageLog.logMessage("CREATING PROJECT", "Patrac")
        #project = QgsProject.instance()
        #project.clear()
        #QgsMapLayerRegistry.instance().mapLayers().clear()

        #if not self.openProjectSimple():
        #    return

        # if not self.checkLayer("okresy_pseudo.shp"):
            #QMessageBox.information(None, "CHYBA:",
            #                        u"Projekt neobsahuje vrstvu okresy. Pokusím se otevřít výchozí projekt.")
            # QgsMessageLog.logMessage("checkLayer(okresy_pseudo.shp)", "Patrac")
            # if not self.openProjectSimple():
            #    return

        # QgsMessageLog.logMessage("openProjectSimple OK", "Patrac")

        name = self.municipalities_names[index]
        region = self.municipalities_regions[index]

        #region = self.getRegion()
        region = self.checkRegion(region)

        if region is None:
            QMessageBox.information(None, "CHYBA:",
                                    u"Pro daný kraj nemám k dispozici data. Nemám data nemohu pokračovat.")
            return

        if not self.checkRegionExtent():
            QMessageBox.information(None, "INFO:",
                                    u"Ukončuji generování.")
            return

        self.setCursor(Qt.WaitCursor)
        if name == '':
            name = 'noname_' + strftime("%Y-%m-%d_%H-%M-%S", gmtime())
            QgsMessageLog.logMessage(u"Noname: " + name, "Patrac")
        else:
            name = name + "_" + strftime("%Y-%m-%d_%H-%M-%S", gmtime())

        NAMESAFE = self.getSafeDirectoryName(name)

        items = self.municipalities_coords[index].split(";")
        x = int(items[0])
        y = int(items[1])
        XMIN = str(x - 6000)
        YMIN = str(y - 5000)
        XMAX = str(x + 6000)
        YMAX = str(y + 5000)
        QgsMessageLog.logMessage(u"g.region e=" + XMAX + " w=" + XMIN + " n=" + YMAX + " s=" + YMIN, "Patrac")
        QgsMessageLog.logMessage(u"Název: " + NAMESAFE, "Patrac")

        DATAPATH = self.getSimpleProjectDataPath()

        NEW_PROJECT_PATH = DATAPATH + "/../../../kraje/" + region + "/projekty/" + NAMESAFE
        # set working dir to new path
        QSettings().setValue("UI/lastProjectDir", DATAPATH + "/../../../kraje/" + region + "/projekty/" + NAMESAFE)

        TEMPLATES_PATH = DATAPATH + "/../../../kraje/templates"
        KRAJ_DATA_PATH = DATAPATH + "/../../../kraje/" + region
        self.copyTemplate(NEW_PROJECT_PATH, TEMPLATES_PATH, NAMESAFE)

        if sys.platform.startswith('win'):
            p = subprocess.Popen((
                                 self.pluginPath + "/grass/run_export.bat", KRAJ_DATA_PATH, self.pluginPath, XMIN, YMIN,
                                 XMAX, YMAX, NEW_PROJECT_PATH))
            p.wait()
            p = subprocess.Popen((self.pluginPath + "/grass/run_import.bat", NEW_PROJECT_PATH, self.pluginPath, XMIN,
                                  YMIN, XMAX, YMAX, KRAJ_DATA_PATH))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_export.sh", KRAJ_DATA_PATH, self.pluginPath,
                                  XMIN, YMIN, XMAX, YMAX, NEW_PROJECT_PATH))
            p.wait()
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_import.sh", NEW_PROJECT_PATH, self.pluginPath,
                                  XMIN, YMIN, XMAX, YMAX, KRAJ_DATA_PATH))
            p.wait()

        # self.copyQGSTemplate(NEW_PROJECT_PATH, TEMPLATES_PATH, KRAJ_DATA_PATH)
        project = QgsProject.instance()
        QgsMessageLog.logMessage(NEW_PROJECT_PATH + '/' + NAMESAFE + '.qgs', "Patrac")
        project.read(QFileInfo(NEW_PROJECT_PATH + '/' + NAMESAFE + '.qgs'))
        # self.do_msearch()
        self.zoomToExtent(XMIN, YMIN, XMAX, YMAX)
        self.addAllZPMRasters(KRAJ_DATA_PATH)
        self.recalculateSectors(True)
        self.createNewSearch(name, region)
        self.settingsdlg.updateSettings()
        self.saveRegion(region, NEW_PROJECT_PATH)
        self.saveExtent(XMIN, YMIN, XMAX, YMAX, NEW_PROJECT_PATH)
        self.setCursor(Qt.ArrowCursor)

    def getDataPath(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        return prjfi.absolutePath()

    def saveRegion(self, region, DATAPATH):
        QgsMessageLog.logMessage(u"Saving region: " + region + u" to " + DATAPATH + '/config/region.txt', "Patrac")
        f = open(DATAPATH + '/config/region.txt', 'w')
        f.write(region)
        f.close()

    def saveExtent(self, XMIN, YMIN, XMAX, YMAX, DATAPATH):
        QgsMessageLog.logMessage(u"Saving extent to " + DATAPATH + '/config/extent.txt', "Patrac")
        f = open(DATAPATH + '/config/extent.txt', 'w')
        f.write(XMIN + " " + YMIN + " " + XMAX + " " + YMAX)
        f.close()

    def getRegionDataPath(self):
        region = open(self.getDataPath() + '/config/region.txt', 'r').read()
        return self.getDataPath() + "/../../../" + region

    def zoomToExtent(self, XMIN, YMIN, XMAX, YMAX):
        rect = QgsRectangle(float(XMIN), float(YMIN), float(XMAX), float(YMAX))
        self.canvas.setExtent(rect)
        self.canvas.refresh()

    def createNewSearch(self, name, region):
        QgsMessageLog.logMessage(u"Vytvářím nové pátrání: " + name + " " + region, "Patrac")
        searchid = self.createSearchId(name)
        self.createSearchOnServer(searchid, name, region)

    def createSearchId(self, name):
        dirname = self.getSafeDirectoryName(name.split(" ")[0])
        start = dirname.replace("_", "").replace("?", "")
        searchid = start + str(uuid.uuid4()).replace("-", "")
        searchid20 = searchid[:20]
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        f = io.open(DATAPATH + '/config/searchid.txt', 'w', encoding='utf-8')
        f.write(searchid20.decode('utf-8'))
        f.close()
        return searchid20

    def createSearchOnServer(self, searchid, name, region):
        response = None
        # Connects to the server to obtain list of users based on list of locations
        try:
            escaped_name = quote(name.encode('utf-8'))
            url = self.serverUrl + 'operation=createnewsearch&id=pcr007&searchid='\
                  + searchid + '&description=' + escaped_name + '&region=' + region
            response = urllib2.urlopen(url, None, 5)
            searchStatus = response.read()
        except urllib2.URLError:
            QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
            self.close()
        except socket.timeout:
            QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
            self.close()
        # TODO - if we can not connect to server, we should connect later
        # self.getMessage()

    def municipalitySearch(self, textBox):
        """Tries to find municipallity in list and zoom to coordinates of it."""
        # Check if the project has okresy_pseudo.shp

        # project = QgsProject.instance()
        # project.clear()
        #
        # if not self.checkLayer("okresy_pseudo.shp"):
        #     #QMessageBox.information(None, "CHYBA:",
        #     #                        u"Projekt neobsahuje vrstvu okresy. Pokusím se otevřít výchozí projekt.")
        #     result = self.openProjectSimple()
        #     if not result:
        #         QMessageBox.information(None, "KRITICKÁ CHYBA:",
        #                                 u"Nepodařilo se otevřít projekt pro generování. Zkuste jej otevřít přes Projekt/Otevřít. "
        #                                 u"Měl by se nacházet na disku C, D, E nebo F v adresáři patracdata.")
        #         return

        try:
            input_name = textBox.text()
            i = 0
            # -1 for just test if the municipality was found
            x = -1
            # loop via list of municipalities
            for m in self.municipalities_names:
                # if the municipality is in the list
                if m == input_name:
                    # get the coords from string
                    items = self.municipalities_coords[i].split(";")
                    x = items[0]
                    y = items[1]
                    break
                i = i + 1
            # if the municipality is not found
            if x == -1:
                QMessageBox.information(self.iface.mainWindow(), u"Chybná obec", u"Obec nebyla nalezena")
                return -1
            else:
                # if the municipality has coords
                #self.zoomto(x, y)
                return i
        except (KeyError, IOError):
            QMessageBox.information(self.iface.mainWindow(), u"Chybná obec", u"Obec nebyla nalezena")
            return i
        except IndexError:
            pass

    def runExpertMunicipalitySearch(self):
        self.municipalitySearch(self.msearch)

    def runGuideMunicipalitySearch(self):
        municipalityindex = self.municipalitySearch(self.guideMunicipalitySearch)

        # generate project
        self.runCreateProjectGuide(municipalityindex)

        # set mista to editing mode
        self.currentTool = self.iface.mapCanvas().mapTool()
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break

        if layer is not None:
            self.iface.setActiveLayer(layer)
            layer.startEditing()

            # set tool to add feature
            self.iface.actionAddFeature().trigger()
        self.tabGuideSteps.setCurrentIndex(1)

    def runGuideStep2Next(self):
        # set tool to save edits
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break

        layer.commitChanges()
        self.iface.actionToggleEditing().trigger()

        # move to next tab (tab 3)
        self.tabGuideSteps.setCurrentIndex(2)

    def runGuideStep3Next(self):
        # run area determination computation
        self.personType = self.guideComboPerson.currentIndex() + 1
        self.getArea()

        # set spin to 70%
        self.__updateSliderEnd(70)

        # move to next tab (tab 4)
        self.tabGuideSteps.setCurrentIndex(3)

    def runGuideStep4Next(self):
        # set percent of visibility
        self.spinStart.setValue(0)
        self.spinEnd.setValue(self.guideSpinEnd.value())
        self.updatePatrac()

        # move to next tab (tab 5)
        self.tabGuideSteps.setCurrentIndex(4)

    def runGuideStep5Next(self):
        # saves information about available resources
        self.saveUnitsInformation()

        # select sectors
        self.runGuideGetSectors()

        # run sectors selection and exports
        self.reportExportSectors(False, True)

        # move to next tab (tab 6)
        self.tabGuideSteps.setCurrentIndex(5)

    def showReport(self):
        self.setCursor(Qt.WaitCursor)

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/distances_costed_cum.tif":
                layer = lyr
                break

        transparencyList = []
        transparencyList.extend(self.generateTransparencyList(0, 100))
        layer.setCacheImage(None)
        layer.renderer().rasterTransparency().setTransparentSingleValuePixelList(transparencyList)
        self.plugin.iface.mapCanvas().refresh()

        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/sektory_group_selected.shp":
                layer = lyr
                break

        # exports overall map with all sectors to PDF
        if self.chkGenerateOverallPDF.isChecked():
            self.exportPDF(layer.extent(), DATAPATH + "/sektory/report.pdf")


        # exports map of sectors to PDF
        #if self.chkGeneratePDF.isChecked():
        #    self.exportPDF(layer.extent(), DATAPATH + "/sektory/report.pdf")

        #    provider = layer.dataProvider()
        #    features = provider.getFeatures()
        #    for feature in features:
        #        self.exportPDF(feature.geometry().boundingBox(), DATAPATH + "/sektory/pdf/" + feature['label'] + ".pdf")

        webbrowser.get().open("file://" + DATAPATH + "/sektory/report.html")
        self.setCursor(Qt.ArrowCursor)

    def saveUnitsInformation(self):
        f = io.open(self.pluginPath + '/grass/units.txt.tmp', 'w', encoding='utf-8')

        with open(self.pluginPath + "/grass/units.txt", "rb") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=';'):
                unicode_row = [x.decode('utf8') for x in row]
                # dog
                if i == 0:
                    unicode_row[0] = self.guideDogCount.text()
                # person
                if i == 1:
                    unicode_row[0] = self.guidePersonCount.text()
                # diver
                if i == 5:
                    unicode_row[0] = self.guideDiverCount.text()
                j = 0
                for field in unicode_row:
                    if j == 0:
                        f.write(field)
                    else:
                        f.write(u";" + field)
                    j=j+1
                i=i+1
                f.write(u"\n")
        f.close()

        copy(self.pluginPath + '/grass/units.txt.tmp', self.pluginPath + "/grass/units.txt")

    def exportPDF(self, extent, path):
        active_Composer = self.iface.activeComposers()
        composer = active_Composer[0]
        composition = composer.composition()
        canvas = self.iface.mapCanvas()
        maps = [item for item in composition.items() if item.type() == QgsComposerItem.ComposerMap and item.scene()]
        composer_map = maps[0]
        composer_map.setMapCanvas(canvas)
        extent.scale(1.1)
        composer_map.zoomToExtent(extent)
        composer_map.updateItem()
        composition.refreshItems()
        composition.updateSettings()
        #https://gis.stackexchange.com/questions/216863/set-print-composer-to-map-canvas-extent-using-python
        # moveX = composer_map.extent().center().x() - canvas.extent().center().x()
        # moveY = composer_map.extent().center().y() - canvas.extent().center().y()
        # unitCon = composer_map.mapUnitsToMM()
        # print str(moveX) + " " + str(moveY) + " " + str(unitCon) + " " + str(canvas.scale())
        # composer_map.moveContent(-moveX * unitCon, moveY * unitCon)
        # composer_map.setNewScale(canvas.scale())
        composition.exportAsPDF(path)

    def setCompleter(self, textBox):
        """Sets the autocompleter for municipalitities."""
        completer = QCompleter()
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        textBox.setCompleter(completer)
        model = QStringListModel()
        completer.setModel(model)
        # sets arrays of municipalities names and coords
        self.municipalities_names = []
        self.municipalities_coords = []
        self.municipalities_regions = []
        # reads list of municipalities from CSV
        with open(self.pluginPath + "/ui/obce_okr_kr_utf8_20180131.csv", "rb") as fileInput:
            for row in csv.reader(fileInput, delimiter=';'):
                unicode_row = [x.decode('utf8') for x in row]
                # sets the name (and province in brackets for iunique identification)
                self.municipalities_names.append(unicode_row[3] + " (" + unicode_row[5] + ")")
                self.municipalities_coords.append(unicode_row[0] + ";" + unicode_row[1])
                self.municipalities_regions.append(unicode_row[6])
        # Sets list of names to model for autocompleter
        model.setStringList(self.municipalities_names)

    def transform(self, cor):
        """Transforms coords to S-JTSK (EPSG:5514)."""
        map_renderer = self.canvas.mapRenderer()
        srs = map_renderer.destinationCrs()
        crs_src = QgsCoordinateReferenceSystem(5514)
        crs_dest = QgsCoordinateReferenceSystem(srs)
        xform = QgsCoordinateTransform(crs_src, crs_dest)
        x = int(cor[0])
        y = int(cor[1])
        t_point = xform.transform(QgsPoint(x, y))
        return t_point

    def check_crs(self):
        """Check if a transformation needs to take place"""
        map_renderer = self.canvas.mapRenderer()
        srs = map_renderer.destinationCrs()
        current_crs = srs.authid()
        return current_crs

    def zoomto(self, x, y):
        """Zooms to coordinates"""
        current_crs = self.check_crs()
        # If the current CRS is not S-JTSK
        if current_crs != "EPSG:5514":
            cor = (x, y)
            # Do the transformation
            point = self.transform(cor)
            self.update_canvas(point)
        else:
            point = (x, y)
            self.update_canvas(point)

    def update_canvas(self, point):
        # Update the canvas and add vertex marker
        x = point[0]
        y = point[1]
        # TODO change scale according to srid
        # This condition is just quick hack for some srids with deegrees and meters
        if y > 100:
            scale = 2500
        else:
            scale = 0.07
        rect = QgsRectangle(float(x) - scale, float(y) - scale, float(x) + scale, float(y) + scale)
        self.canvas.setExtent(rect)
        self.canvas.refresh()

    def updatePatrac(self):
        """Changes the transfṕarency of raster"""
        transparencyList = []
        if self.sliderStart.value() != 0:
            transparencyList.extend(self.generateTransparencyList(0, self.sliderStart.value()))

        if self.sliderEnd.value() != self.maxVal:
            transparencyList.extend(self.generateTransparencyList(self.sliderEnd.value(), self.maxVal))

        # update layer transparency
        layer = self.plugin.iface.mapCanvas().currentLayer()
        layer.setCacheImage(None)
        layer.renderer().rasterTransparency().setTransparentSingleValuePixelList(transparencyList)
        layer.renderer().setOpacity(0.5)
        self.plugin.iface.mapCanvas().refresh()

    def __updateSpinStart(self, value):
        endValue = self.sliderEnd.value()
        if value >= endValue:
            self.spinStart.setValue(endValue - 1)
            self.sliderStart.setValue(endValue - 1)
            return
        self.spinStart.setValue(value)

        if not self.chkManualUpdate.isChecked():
            self.updatePatrac()

    def __updateSliderStart(self, value):
        endValue = self.spinEnd.value()
        if value >= endValue:
            self.spinStart.setValue(endValue - 1)
            self.sliderStart.setValue(endValue - 1)
            return
        self.sliderStart.setValue(value)

    def __updateSpinEnd(self, value):
        startValue = self.sliderStart.value()
        if value <= startValue:
            self.spinEnd.setValue(startValue + 1)
            self.sliderEnd.setValue(startValue + 1)
            return
        self.spinEnd.setValue(value)

        if not self.chkManualUpdate.isChecked():
            self.updatePatrac()

    def __updateSliderEnd(self, value):
        startValue = self.sliderStart.value()
        if value <= startValue:
            self.spinEnd.setValue(startValue + 1)
            self.sliderEnd.setValue(startValue + 1)
            return
        self.sliderEnd.setValue(value)

    def __toggleRefresh(self):
        settings = QSettings("alexbruy", "Patrac")
        settings.setValue("manualUpdate", self.chkManualUpdate.isChecked())

        if self.chkManualUpdate.isChecked():
            self.btnRefresh.setEnabled(True)
            try:
                self.sliderStart.sliderReleased.disconnect(self.updatePatrac)
                self.sliderEnd.sliderReleased.disconnect(self.updatePatrac)
            except:
                pass
        else:
            self.btnRefresh.setEnabled(False)
            self.sliderStart.sliderReleased.connect(self.updatePatrac)
            self.sliderEnd.sliderReleased.connect(self.updatePatrac)

    def disableOrEnableControls(self, disable):
        self.label.setEnabled(disable)
        self.sliderStart.setEnabled(disable)
        self.spinStart.setEnabled(disable)
        self.label_2.setEnabled(disable)
        self.sliderEnd.setEnabled(disable)
        self.spinEnd.setEnabled(disable)

    def updateSliders(self, maxValue, minValue):
        # self.maxVal = int(maxValue)
        # self.minVal = int(minValue)

        self.maxVal = 100
        self.minVal = 0

        self.spinStart.setMaximum(int(self.maxVal))
        self.spinStart.setMinimum(int(self.minVal))
        self.spinStart.setValue(int(self.minVal))

        self.spinEnd.setMaximum(int(self.maxVal))
        self.spinEnd.setMinimum(int(self.minVal))
        self.spinEnd.setValue(int(self.maxVal))

        self.sliderStart.setMinimum(int(self.minVal))
        self.sliderStart.setMaximum(int(self.maxVal))
        self.sliderStart.setValue(int(self.minVal))

        self.sliderEnd.setMinimum(int(self.minVal))
        self.sliderEnd.setMaximum(int(self.maxVal))
        self.sliderEnd.setValue(int(self.maxVal))

    def generateTransparencyList(self, minVal, maxVal):
        trList = []
        tr = QgsRasterTransparency.TransparentSingleValuePixel()
        tr.min = minVal
        tr.max = maxVal
        tr.percentTransparent = 100
        trList.append(tr)
        return trList

    def addPlaceToTheCenter(self):
        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        provider = layer.dataProvider()
        layer.startEditing()
        fet = QgsFeature()
        center = self.plugin.canvas.center()
        fet.setGeometry(QgsGeometry.fromPoint(center))
        fet.setAttributes(
            [1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        provider.addFeatures([fet])
        layer.commitChanges()

    def runExpertGetArea(self):
        self.personType = self.comboPerson.currentIndex() + 1
        self.getArea()

    def getArea(self):
        """Runs main search for suitable area"""

        # Check if the project has mista.shp
        if not self.checkLayer("/pracovni/mista.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu míst. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        # Vybrana vrstva
        # qgis.utils.iface.setActiveLayer(QgsMapLayer)
        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        # Removes existing loaded layer with area for search
        # This is necessary on Windows - based on lock of files
        self.removeLayer(DATAPATH + '/pracovni/distances_costed_cum.tif')

        # Tests if layer mista exists
        # TODO should be done tests for attributes as well
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        if layer == None:
            QMessageBox.information(None, "INFO:", u"Nebyla nalezena vrstva s místy. Nemohu určit oblast.")
            self.setCursor(Qt.ArrowCursor)
            return

        features = self.filterAndSortFeatures(layer.getFeatures())

        if len(features) == 0:
            # There is not any place defined
            # Place the place to the center of the map
            QMessageBox.information(None, "INFO:",
                                    u"Vrstva s místy neobsahuje žádný prvek. Vkládám bod do středu mapy s aktuálním časem.")
            self.addPlaceToTheCenter()

        # If there is just one point - impossible to define direction
        # TODO - think more about this check - should be more than two, probably and in some shape as well
        if len(features) > 1:
            azimuth = self.getRadial(features)
            # TODO read from setings
            useAzimuth = self.getProcessRadial()
            # difficult to set azimuth (for example wrong shape of the path (e.q. close to  circle))
            if azimuth <= 360 and useAzimuth:
                self.generateRadialOnPoint(features[len(features) - 1])
                self.writeAzimuthReclass(azimuth, 30, 100)
                self.findAreaWithRadial(features[len(features) - 1], 0)
                self.createCumulativeArea("distances0_costed")
            else:
                self.writeAzimuthReclass(0, 0, 0)
                i = 0
                distances_costed_cum = ""
                max_weight = 1
                for feature in features:
                    self.generateRadialOnPoint(feature)
                    self.findAreaWithRadial(feature, i)
                    cur_weight = "1"
                    if str(feature["vaha"]) != "NULL":
                        cur_weight = str(feature["vaha"])
                    if str(feature["vaha"]) != "NULL" and feature["vaha"] > max_weight:
                        max_weight = feature["vaha"]
                    if (i == 0):
                        distances_costed_cum = "(distances0_costed/" + cur_weight + ")"
                    else:
                        distances_costed_cum = distances_costed_cum + ",(distances" + str(i) + "_costed/" + cur_weight + ")"
                    i += 1
                #print "DC: min(" + distances_costed_cum + ")*" + str(max_weight)
                self.createCumulativeArea("min(" + distances_costed_cum + ")*" + str(max_weight))
        else:
            self.generateRadialOnPoint(features[0])
            self.writeAzimuthReclass(0, 0, 0)
            self.findAreaWithRadial(features[0], 0)
            self.createCumulativeArea("distances0_costed")
        self.setCursor(Qt.ArrowCursor)
        return

    def createCumulativeArea(self, distances_costed_cum):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        # Windows - nutno nejdrive smazat tif
        # driver = gdal.GetDriverByName('GTiff')
        # driver.DeleteDataSource(DATAPATH + "/pracovni/distances_costed_cum.tif")
        # time.sleep(1)
        if os.path.isfile(DATAPATH + '/pracovni/distances_costed_cum.tif.aux.xml'):
            os.remove(DATAPATH + '/pracovni/distances_costed_cum.tif.aux.xml')
        if os.path.isfile(DATAPATH + '/pracovni/distances_costed_cum.tif'):
            os.remove(DATAPATH + '/pracovni/distances_costed_cum.tif')
        if os.path.isfile(DATAPATH + '/pracovni/distances_costed_cum.tfw'):
            os.remove(DATAPATH + '/pracovni/distances_costed_cum.tfw')

        QgsMessageLog.logMessage(
            "Spoustim python " + self.pluginPath + "/grass/run_distance_costed_cum.sh " + distances_costed_cum,
            "Patrac")
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_distance_costed_cum.bat", DATAPATH, self.pluginPath,
                                  distances_costed_cum))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_distance_costed_cum.sh", DATAPATH,
                                  self.pluginPath, distances_costed_cum))
            p.wait()

        # Adds exported raster to map
        self.addRasterLayer(DATAPATH + '/pracovni/distances_costed_cum.tif', 'procenta')
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/distances_costed_cum.tif":
                layer = lyr
                break
        layer.triggerRepaint()
        # Sets the added layer as sctive
        self.plugin.iface.setActiveLayer(layer)

    def findAreaWithRadial(self, feature, id):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        geom = feature.geometry()
        x = geom.asPoint()
        coords = str(x)[1:-1]
        # writes coord to file for grass
        f_coords = open(self.pluginPath + '/grass/coords.txt', 'w')
        f_coords.write(coords)
        f_coords.close()
        QgsMessageLog.logMessage(u"Souřadnice: " + coords, "Patrac")
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_cost_distance.bat", DATAPATH, self.pluginPath, str(id)
                                  , str(self.personType)))
            p.wait()
        else:
            p = subprocess.Popen(
                ('bash', self.pluginPath + "/grass/run_cost_distance.sh", DATAPATH, self.pluginPath, str(id)
                 , str(self.personType)))
            p.wait()
        return

    def runExpertGetSectors(self):
        self.getSectors(self.sliderStart.value(), self.sliderEnd.value())

    def runExpertReportExportSectors(self):
        self.reportExportSectors(True, True)

    def runGuideGetSectors(self):
        self.getSectors(0, self.guideSpinEnd.value())

    def getSectors(self, min, max):
        """Selects sectors from grass database based on filtered raster"""

        # Check if the project has sektory_group_selected.shp
        if not self.checkLayer("/pracovni/sektory_group_selected.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        # Removes layer
        self.removeLayer(DATAPATH + '/pracovni/sektory_group_selected.shp')

        QgsMessageLog.logMessage("Spoustim python " + self.pluginPath + "/grass/sectors.py", "Patrac")
        self.setCursor(Qt.WaitCursor)
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_sectors.bat", DATAPATH, self.pluginPath,
                                  str(min), str(max)))
            p.wait()
            # os.system(self.pluginPath + "/grass/run_sectors.bat " + DATAPATH + " " + self.pluginPath + " " + str(self.sliderStart.value()) + " " + str(self.sliderEnd.value()))
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_sectors.sh", DATAPATH, self.pluginPath,
                                  str(min), str(max)))
            p.wait()
            # os.system("bash " + self.pluginPath + "/grass/run_sectors.sh " + DATAPATH + " " + self.pluginPath + " " + str(self.sliderStart.value()) + " " + str(self.sliderEnd.value()))

        # Adds newly created layer with sectors to map
        self.addVectorLayer(DATAPATH + '/pracovni/sektory_group_selected.shp', 'sektory')
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/sektory_group_selected.shp":
                layer = lyr
                break
        layer.dataProvider().forceReload()

        # Removes first two attrbutes from added layer
        # Attributes are something like cat_
        # Attributes cat and cat_ are identical
        fList = list()
        fList.append(0)
        fList.append(1)
        layer.startEditing()
        layer.dataProvider().deleteAttributes(fList)
        layer.commitChanges()
        layer.triggerRepaint()
        self.setCursor(Qt.ArrowCursor)
        self.recalculateSectors(False)
        return

    def recalculateSectorsExpert(self):
        # self.recalculateSectors(False)
        # TODO change icon and name of the function
        self.extendRegion()

    def extendRegion(self):
        QgsMessageLog.logMessage("Spoustim python " + self.pluginPath + "/grass/export.py", "Patrac")
        self.setCursor(Qt.WaitCursor)

        initialExtent = open(self.getDataPath() + '/config/extent.txt', 'r').read()
        initialExtentItems = initialExtent.split(" ")

        XMIN = str(self.canvas.extent().xMinimum()) \
            if self.canvas.extent().xMinimum() < float(initialExtentItems[0]) else initialExtentItems[0]
        YMIN = str(self.canvas.extent().yMinimum()) \
            if self.canvas.extent().yMinimum() < float(initialExtentItems[1]) else initialExtentItems[1]
        XMAX = str(self.canvas.extent().xMaximum()) \
            if self.canvas.extent().xMaximum() > float(initialExtentItems[2]) else initialExtentItems[2]
        YMAX = str(self.canvas.extent().yMaximum()) \
            if self.canvas.extent().yMaximum() > float(initialExtentItems[3]) else initialExtentItems[3]

        # XMIN = str(self.canvas.extent().xMinimum())
        # YMIN = str(self.canvas.extent().yMinimum())
        # XMAX = str(self.canvas.extent().xMaximum())
        # YMAX = str(self.canvas.extent().yMaximum())

        if sys.platform.startswith('win'):
            p = subprocess.Popen((
                self.pluginPath + "/grass/run_export.bat", self.getRegionDataPath(), self.pluginPath, XMIN, YMIN,
                XMAX, YMAX, self.getDataPath()))
            p.wait()
            p = subprocess.Popen((self.pluginPath + "/grass/run_import_for_extend.bat", self.getDataPath(), self.pluginPath, XMIN,
                                  YMIN, XMAX, YMAX, self.getRegionDataPath()))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_export.sh", self.getRegionDataPath(), self.pluginPath,
                                  XMIN, YMIN, XMAX, YMAX, self.getDataPath()))
            p.wait()
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_import_for_extend.sh", self.getDataPath(), self.pluginPath,
                                  XMIN, YMIN, XMAX, YMAX, self.getRegionDataPath()))
            p.wait()

        self.appendSectors()
        self.setCursor(Qt.ArrowCursor)

    def getSectorsIds(self):
        with open(self.getDataPath() + '/pracovni/listOfIds.txt') as f:
            return f.read().splitlines()

    def appendSectors(self):
        self.addVectorLayer(self.getDataPath() + "/pracovni/sektory_group_to_append.shp", u"Sektory k přidání")

        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == self.getDataPath() + "/pracovni/sektory_group_selected.shp":
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt nemá načtenu vrstvu sektorů. Nemohu pokračovat.")
            return

        layerToAdd = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == self.getDataPath() + "/pracovni/sektory_group_to_append.shp":
                layerToAdd = lyr
                break

        if layerToAdd == None:
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt nemá načtenu vrstvu k přidání sektorů. Nemohu pokračovat.")
            return

        # we save the edits before the process (if there are any)
        layer.commitChanges()

        # we create list of ids of existing layer
        startingLetter = 'B'
        featureIds = self.getSectorsIds()
        print(featureIds)
        #geometries = []
        provider = layer.dataProvider()
        features = provider.getFeatures()
        for feature in features:
            #featureIds.append(feature['id'])
            #geometries.append(feature.geometry())
            if ord(feature['label'][0:1]) >= ord(startingLetter):
                startingLetter = chr(ord(feature['label'][0:1]) + 1)

        # we open layer again to add new sectors
        layer.startEditing()

        f = open(self.getDataPath() + '/pracovni/listOfIds.txt', 'a')
        providerToAdd = layerToAdd.dataProvider()
        featuresToAdd = providerToAdd.getFeatures()
        sectorid = 0
        for feature in featuresToAdd:
            if str(feature['id']) not in featureIds:
                print("ADD " + str(feature['id']))
                f.write(str(feature['id']) + u"\n")
                sectorid = sectorid + 1
                feature['label'] = str(startingLetter) + str(sectorid)
                feature['area_ha'] = round(feature.geometry().area() / 10000)
                layer.addFeature(feature)

        f.close()
        layer.commitChanges()
        layer.triggerRepaint()

        self.removeLayer(self.getDataPath() + "/pracovni/sektory_group_to_append.shp")

    def dump(self, obj):
        for attr in dir(obj):
            if hasattr(obj, attr):
                print("obj.%s = %s" % (attr, getattr(obj, attr)))

    def featureIntersects(self, featureToCheck, geometries):
        # does not work, and it works it will be slow
        print("START INTERSECT")
        for geometry in geometries:
            print("FEATURE:" + geometry.exportToWkt())
            print("featureToCheck:" + featureToCheck.geometry().exportToWkt())
            if geometry.intersects(featureToCheck.geometry()):
                return True
        return False

    def recalculateSectors(self, setLabels):
        """Recalculate areas of sectors and identifiers"""

        # Check if the project has sektory_group_selected.shp
        if not self.checkLayer("/pracovni/sektory_group_selected.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/sektory_group_selected.shp":
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt nemá načtenu vrstvu sektorů. Nemohu pokračovat.")
            return

        provider = layer.dataProvider()
        features = provider.getFeatures()
        sectorid = 0
        f = open(DATAPATH + '/pracovni/listOfIds.txt', 'w')
        layer.startEditing()
        for feature in features:
            sectorid = sectorid + 1
            # Label is set to A and sequential number
            # Labels must be stable for whole search area, so only at the beginning are sectors labeled
            if setLabels:
                feature['label'] = 'A' + str(sectorid)
            # Area in hectares
            feature['area_ha'] = round(feature.geometry().area() / 10000)
            #print(str(feature['id']))
            f.write(str(feature['id']) + u"\n")
            layer.updateFeature(feature)
        layer.commitChanges()
        layer.triggerRepaint()
        f.close()

        QgsMessageLog.logMessage("Spoustim python " + self.pluginPath + "/grass/store_sectors.py", "Patrac")
        self.setCursor(Qt.WaitCursor)
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_store_sectors.bat", DATAPATH, self.pluginPath))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_store_sectors.sh", DATAPATH, self.pluginPath))
            p.wait()

        self.setCursor(Qt.ArrowCursor)
        return sectorid

    def removeExportedSectors(self):
        self.setCursor(Qt.WaitCursor)
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if "sektory/shp" in lyr.source():
                if lyr.isValid():
                    QgsMapLayerRegistry.instance().removeMapLayer(lyr)
        self.setCursor(Qt.ArrowCursor)
        return

    def exportSectors(self):
        """Exports sectors to SHP and GPX without creating report. It is much faster and allows to use only selected sectors."""

        # Check if the project has sektory_group_selected.shp
        if not self.checkLayer("/pracovni/sektory_group_selected.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        sectorid = self.recalculateSectors(False)
        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/sektory_group_selected.shp":
                layer = lyr
                break
        provider = layer.dataProvider()
        features = layer.selectedFeatures()
        if len(features) < 1:
            features = provider.getFeatures()
            QgsMessageLog.logMessage(u"Není vybrán žádný sektor. Exportuji všechny", "Patrac")

        self.removeExportedSectors()

        i = 1
        for feature in features:
            # Removes existing layer according to label in features
            # TODO - if the number of sectors is higher than in previous step, some of the layers are not removed
            # self.removeLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp")
            self.copyLayer(DATAPATH, feature['label'])
            sector = QgsVectorLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp", feature['label'], "ogr")
            providerSector = sector.dataProvider()
            sector.startEditing()
            fet = QgsFeature()
            fet.setAttributes([feature['area_ha'], feature['label'], u"REPORT nebyl realizován"])

            polygon = feature.geometry().asPolygon()
            polygon_points_count = len(polygon[0])
            points = []
            for pointi in range(polygon_points_count):
                points.append(polygon[0][pointi])
            line = QgsGeometry.fromPolyline(points)
            fet.setGeometry(line)
            providerSector.addFeatures([fet])
            sector.commitChanges()

            if not sector.isValid():
                QgsMessageLog.logMessage(u"Sector " + feature['label'] + u" se nepodařilo načíst", "Patrac")
            else:
                # Export do GPX
                crs = QgsCoordinateReferenceSystem("EPSG:4326")
                QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + feature['label'] + ".gpx",
                                                        "utf-8", crs, "GPX",
                                                        datasourceOptions=['GPX_USE_EXTENSIONS=YES'],
                                                        layerOptions=['FORCE_GPX_TRACK=YES'])
                QgsMapLayerRegistry.instance().addMapLayer(sector, False)
                root = QgsProject.instance().layerTreeRoot()
                sektorygroup = root.findGroup("sektory")
                if sektorygroup is None:
                    sektorygroup = root.insertGroup(0, "sektory")
                sektorygroup.addLayer(sector)
                sektorygroup.setExpanded(False)

            i += 1

        self.setCursor(Qt.ArrowCursor)
        return

    def reportExportSectors(self, openReport, exportPDF):
        """Creates report and exports sectors to SHP and GPX"""

        # Check if the project has sektory_group_selected.shp
        if not self.checkLayer("/pracovni/sektory_group_selected.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        sectorid = self.recalculateSectors(False)
        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/sektory_group_selected.shp":
                layer = lyr
                break

        provider = layer.dataProvider()
        features = provider.getFeatures()

        AREAS = ""
        for feature in features:
            AREAS = AREAS + "!" + str(feature['area_ha'])

        # GRASS exports to SHP
        if sys.platform.startswith('win'):
            p = subprocess.Popen(
                (self.pluginPath + "/grass/run_report_export.bat", DATAPATH, self.pluginPath, str(sectorid), AREAS))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_report_export.sh", DATAPATH, self.pluginPath,
                                  str(sectorid), AREAS))
            p.wait()

        # prepare all sectors to one file
        self.copyLayer(DATAPATH, "all")
        layerLines = QgsVectorLayer(DATAPATH + "/sektory/shp/all.shp", "sektory linie", "ogr")
        providerLayerLines = layerLines.dataProvider()
        layerLines.startEditing()

        # Reads header of report
        header = io.open(DATAPATH + '/pracovni/report_header.html', encoding='utf-8', mode='r').read()
        # Writes header to report
        f = io.open(DATAPATH + '/sektory/report.html', encoding='utf-8', mode='w')
        f.write(header)
        f.write(u'<h1>REPORT</h1>\n')
        f.write(u'<div class="flex-container">\n')

        self.removeExportedSectors()

        # Header for search time
        f.write(u'<div id="summary" class="fixed400">\n')
        f.write(u"\n<h2>Doba pro pátrání</h2>\n");
        f.write(u"\n<p>Pro propátrání se počítá 3 hodiny jedním týmem</p>\n");

        # Reads units report
        report_units = io.open(DATAPATH + '/pracovni/report.html.units', encoding='utf-8', mode='r').read()
        f.write(report_units)
        f.write(u"\n<h2>GPX a PDF pro pátrání</h2>\n");
        f.write(u"\n<p>Pro propátrání referenční plochy (cca 30 ha) se počítá 3 hodiny jedním týmem.</p>\n");
        f.write(u'<p><a href="report.pdf"><img src="styles/pdf.png" alt="PDF" width="40"></a>&nbsp;<a href="gpx/all.gpx">'
                u'<img src="styles/gpx.png" alt="GPX" width="40"></a></p>\n')
        f.write(u'</div>\n')

        #styles
        styles = ""

        # crs for GPX
        crs = QgsCoordinateReferenceSystem("EPSG:4326")

        # Loop via features in sektory_group_selected
        features = provider.getFeatures()
        i = 1
        for feature in features:

            styles += u"#a" + str(i) + u"s {display: none;}\n"
            styles += u"#a" + str(i) + u"n {display: none;}\n"
            styles += u"#a" + str(i) + u"sc:checked ~ #a" + str(i) + u"s {display: block;}\n"
            styles += u"#a" + str(i) + u"nc:checked ~ #a" + str(i) + u"n {display: block;}\n"

            f.write(u'<div id="a' + str(i) + '" class="fixed400">\n')
            # Prints previously obtained area and label of the sector
            f.write(u"<p>SEKTOR " + feature['label'] + " (" + str(feature['area_ha']) + u" ha)"
                    + '<label class="rolldown" for="a' + str(i) + 'sc"> Typy povrchu </label></p>' + "\n")
            f.write(u'<input id="a' + str(i) + 'sc" type="checkbox" style="display: none">\n')

            # Reads sector report
            report = io.open(DATAPATH + '/pracovni/report.html.' + str(i), encoding='utf-8', mode='r').read()
            f.write(report)

            # Removes existing layer according to label in features
            # TODO - if the number of sectors is higher than in previous step, some of the layers are not removed
            # self.removeLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp")
            # self.setStyle(DATAPATH + "/sektory/shp/", feature['label'])
            # crs = QgsCoordinateReferenceSystem("EPSG:5514")
            # QgsVectorFileWriter.writeAsVectorFormat(layer, DATAPATH + "/sektory/shp/" + feature['label'] + ".shp",
            #                                        "utf-8", crs, "ESRI Shapefile")
            self.copyLayer(DATAPATH, feature['label'])
            sector = QgsVectorLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp", feature['label'], "ogr")
            providerSector = sector.dataProvider()
            sector.startEditing()
            fet = QgsFeature()

            report_units = io.open(DATAPATH + '/pracovni/report.html.units.' + str(i), encoding='utf-8',
                                   mode='r').read()
            fet.setAttributes([feature['area_ha'], feature['label'], report_units])

            polygon = feature.geometry().asPolygon()
            polygon_points_count = len(polygon[0])
            points = []
            for pointi in range(polygon_points_count):
                points.append(polygon[0][pointi])
            line = QgsGeometry.fromPolyline(points)
            fet.setGeometry(line)
            providerSector.addFeatures([fet])
            providerLayerLines.addFeatures([fet])
            sector.commitChanges()

            if not sector.isValid():
                QgsMessageLog.logMessage(u"Sector " + feature['label'] + u" se nepodařilo načíst", "Patrac")
            else:
                # Export do GPX
                QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + feature['label'] + ".gpx",
                                                        "utf-8", crs, "GPX",
                                                        datasourceOptions=['GPX_USE_EXTENSIONS=YES'],
                                                        layerOptions=['FORCE_GPX_TRACK=YES'])
                QgsMapLayerRegistry.instance().addMapLayer(sector, False)
                root = QgsProject.instance().layerTreeRoot()
                sektorygroup = root.findGroup("sektory")
                if sektorygroup is None:
                    sektorygroup = root.insertGroup(0, "sektory")
                sektorygroup.addLayer(sector)
                sektorygroup.setExpanded(False)

            # Writes link to PDF and GPX
            #f.write(u'<p><a href="pdf/' + feature['label'] + '.pdf"><img src="styles/pdf.png" alt="PDF" width="40"></a>&nbsp;<a href="gpx/'+ feature['label'] +'.gpx"><img src="styles/gpx.png" alt="GPX" width="40"></a></p>\n')
            f.write(u'<p><a href="gpx/' + feature[
                        'label'] + '.gpx"><img src="styles/gpx.png" alt="GPX" width="40"></a></p>\n')
            f.write(u"</div>\n")

            i += 1

        # writes all sectors to one file
        layerLines.commitChanges()
        QgsVectorFileWriter.writeAsVectorFormat(layerLines, DATAPATH + "/sektory/gpx/all.gpx",
                                                "utf-8", crs, "GPX",
                                                datasourceOptions=['GPX_USE_EXTENSIONS=YES'],
                                                layerOptions=['FORCE_GPX_TRACK=YES'])

        #Writes styles
        f.write(u"<style>")
        f.write(styles)
        f.write(u"</style>")

        # Writes footer
        footer = io.open(DATAPATH + '/pracovni/report_footer.html', encoding='utf-8', mode='r').read()
        f.write(footer)
        f.close()

        self.setCursor(Qt.ArrowCursor)
        # Opens report in default browser
        if openReport:
            webbrowser.open("file://" + DATAPATH + "/sektory/report.html")
        return

    def copyLayer(self, DATAPATH, name):
        copy(DATAPATH + "/sektory/shp/template.shp", DATAPATH + "/sektory/shp/" + name + ".shp")
        copy(DATAPATH + "/sektory/shp/template.shx", DATAPATH + "/sektory/shp/" + name + ".shx")
        copy(DATAPATH + "/sektory/shp/template.dbf", DATAPATH + "/sektory/shp/" + name + ".dbf")
        copy(DATAPATH + "/sektory/shp/template.prj", DATAPATH + "/sektory/shp/" + name + ".prj")
        copy(DATAPATH + "/sektory/shp/template.qml", DATAPATH + "/sektory/shp/" + name + ".qml")
        copy(DATAPATH + "/sektory/shp/template.qpj", DATAPATH + "/sektory/shp/" + name + ".qpj")

    def removeLayer(self, path):
        """Removes layer based on path to file"""
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == path:
                layer = lyr
                break
        if layer is not None:
            if layer.isValid():
                QgsMapLayerRegistry.instance().removeMapLayer(layer)
        return

    def setStyle(self, path, name):
        """Copies style and replaces some definitions"""
        # TODO - maybe just copy the style
        qml = open(path + 'style.qml', 'r').read()
        f = open(path + name + '.qml', 'w')
        qml = qml.replace("k=\"line_width\" v=\"0.26\"", "k=\"line_width\" v=\"1.2\"")
        f.write(qml)
        f.close()

    def showSettings(self):
        """Shows the settings dialog"""
        self.settingsdlg.updateSettings()
        self.settingsdlg.show()

    def showMessage(self):
        """Show the dialog for sending messages"""
        # Check if the project has sektory_group_selected.shp
        if not self.checkLayer("/pracovni/sektory_group_selected.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.setCursor(Qt.WaitCursor)
        self.messagedlg = Ui_Message(self.pluginPath, DATAPATH)
        self.messagedlg.show()
        self.setCursor(Qt.ArrowCursor)

    def showImportGpx(self):
        """Shows the dialog for import of GPX tracks"""
        # Check if the project has sektory_group_selected.shp
        if not self.checkLayer("/pracovni/sektory_group_selected.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        self.importgpxdlg = Ui_Gpx(self.pluginPath)
        self.importgpxdlg.show()

    def insertFinal(self):
        """Sets tool to pointtool to be able handle from click to map.
            It is used at the time when the search is finished.
        """
        # Check if the project has sektory_group_selected.shp
        if not self.checkLayer("/pracovni/sektory_group_selected.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.pointtool.setDataPath(DATAPATH)
        self.pointtool.setSearchid(self.getSearchID())
        self.plugin.iface.mapCanvas().setMapTool(self.pointtool)

    def addRasterLayer(self, path, label):
        """Adds raster layer to map"""
        raster = QgsRasterLayer(path, label, "gdal")
        if not raster.isValid():
            QgsMessageLog.logMessage(u"Vrstvu " + path + u" se nepodařilo načíst", "Patrac")
        else:
            ##            crs = QgsCoordinateReferenceSystem("EPSG:4326")
            QgsMapLayerRegistry.instance().addMapLayer(raster)

    def addRasterLayerToGroup(self, path, label, group, minscaledenominator, maxscaledenominator):
        """Adds raster layer to map"""
        raster = QgsRasterLayer(path, label, "gdal")
        if not raster.isValid():
            QgsMessageLog.logMessage(u"Vrstvu " + path + u" se nepodařilo načíst", "Patrac")
        else:
            raster.setCrs(QgsCoordinateReferenceSystem(5514, QgsCoordinateReferenceSystem.EpsgCrsId))
            raster.toggleScaleBasedVisibility(True)
            raster.setMinimumScale(minscaledenominator)
            raster.setMaximumScale(maxscaledenominator)
            QgsMapLayerRegistry.instance().addMapLayer(raster, False)
            root = QgsProject.instance().layerTreeRoot()
            mygroup = root.findGroup(group)
            mygroup.addLayer(raster)
            mygroup.setExpanded(False)

    def addVectorLayer(self, path, label):
        """Adds raster layer to map"""
        vector = QgsVectorLayer(path, label, "ogr")
        if not vector.isValid():
            QgsMessageLog.logMessage(u"Vrstvu " + path + u" se nepodařilo načíst", "Patrac")
        else:
            ##            crs = QgsCoordinateReferenceSystem("EPSG:4326")
            QgsMapLayerRegistry.instance().addMapLayer(vector)

    def checkLayer(self, name):
        layerExists = False
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMessageLog.logMessage("Check layer: " + name + ": " + lyr.source(), "Patrac")
            if name in lyr.source():
                layerExists = True
                break
        return layerExists

    def definePlaces(self):
        """Moves the selected point to specified coordinates
            Or converts lines to points
            Or converts polygons to points
        """
        # Check if the project has mista.shp
        if not self.checkLayer("/pracovni/mista.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu míst. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        # Get center of the map
        center = self.plugin.canvas.center()
        self.coordsdlg.setCenter(center)
        self.coordsdlg.setWidget(self)
        # self.coordsdlg.setLayer(layer)
        self.coordsdlg.setModal(True)
        # Show dialog with coordinates of the center
        self.coordsdlg.exec_()
        x = None
        y = None

        # If S-JTSk then simply read
        if self.coordsdlg.radioButtonJTSK.isChecked() == True:
            x = self.coordsdlg.lineEditX.text()
            y = self.coordsdlg.lineEditY.text()

        # If WGS then transformation
        if self.coordsdlg.radioButtonWGS.isChecked() == True:
            x = self.coordsdlg.lineEditLon.text()
            y = self.coordsdlg.lineEditLat.text()
            source_crs = QgsCoordinateReferenceSystem(4326)
            dest_crs = QgsCoordinateReferenceSystem(5514)
            transform = QgsCoordinateTransform(source_crs, dest_crs)
            xyJTSK = transform.transform(float(x), float(y))
            x = xyJTSK.x()
            y = xyJTSK.y()

        # If UTM then transformation
        if self.coordsdlg.radioButtonUTM.isChecked() == True:
            x = self.coordsdlg.lineEditUTMX.text()
            y = self.coordsdlg.lineEditUTMY.text()
            source_crs = QgsCoordinateReferenceSystem(32633)
            dest_crs = QgsCoordinateReferenceSystem(5514)
            transform = QgsCoordinateTransform(source_crs, dest_crs)
            xyJTSK = transform.transform(float(x), float(y))
            x = xyJTSK.x()
            y = xyJTSK.y()

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        # If we would like to switch to all features
        # provider = layer.dataProvider()
        # provider.getFeatures()
        # Work only with selected features
        features = layer.selectedFeatures()
        layer.startEditing()
        for fet in features:
            geom = fet.geometry()
            pt = geom.asPoint()
            # print str(pt)
            # Moves point to specified coordinates
            fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(x), float(y))))
            layer.updateFeature(fet)
        layer.commitChanges()
        layer.triggerRepaint()

        # Converts lines to points
        if self.coordsdlg.checkBoxLine.isChecked() == True:
            self.convertLinesToPoints()

        # Converts polygons to points
        if self.coordsdlg.checkBoxPolygon.isChecked() == True:
            self.convertPolygonsToPoints()

    def getLinePoints(self, line):
        """Returns point in the center of the line or two points
            First point is center of the line and second is end of the line.
            Two points are returned in a case that line has smer attribuet equal to 1.
        """
        geom = line.geometry()
        lineLength = geom.length()
        point = geom.interpolate(lineLength / 2)
        if line["smer"] == 1:
            points = geom.asPolyline()
            return [point, QgsGeometry.fromPoint(points[len(points) - 1])]
        else:
            return [point]

    def convertLinesToPoints(self):
        """Converts lines to points
        """
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layerPoint = None
        layerLine = None
        # Reads lines from mista_line layer
        # Writes centroid to mista
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista_linie.shp":
                layerLine = lyr
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layerPoint = lyr
        providerLine = layerLine.dataProvider()
        providerPoint = layerPoint.dataProvider()
        # features = layer.selectedFeatures()
        features = providerLine.getFeatures()
        for fet in features:
            points = self.getLinePoints(fet)
            fetPoint = QgsFeature()
            fetPoint.setGeometry(points[0])
            featureid = fet["id"] + 1000
            fetPoint.setAttributes([featureid, fet["cas_od"], fet["cas_do"], fet["vaha"]])
            if len(points) == 2:
                fetPoint2 = QgsFeature()
                fetPoint2.setGeometry(points[1])
                featureid = fet["id"] + 1000
                cas_od_datetime = datetime.strptime(fet["cas_od"], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)
                cas_do_datetime = datetime.strptime(fet["cas_do"], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)
                fetPoint2.setAttributes([featureid, format(cas_od_datetime, '%Y-%m-%d %H:%M:%S'),
                                         format(cas_do_datetime, '%Y-%m-%d %H:%M:%S'), fet["vaha"]])
                providerPoint.addFeatures([fetPoint, fetPoint2])
            else:
                providerPoint.addFeatures([fetPoint])
        layerPoint.commitChanges()
        layerPoint.triggerRepaint()

    def convertPolygonsToPoints(self):
        """Converts polygons to points
           Simply creates centroid of polygon.
        """
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layerPoint = None
        layerPolygon = None
        # Reads lines from mista_polygon layer
        # Writes centroid to mista
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista_polygon.shp":
                layerPolygon = lyr
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layerPoint = lyr
        providerPolygon = layerPolygon.dataProvider()
        providerPoint = layerPoint.dataProvider()
        # features = layer.selectedFeatures()
        features = providerPolygon.getFeatures()
        for fet in features:
            fetPoint = QgsFeature()
            fetPoint.setGeometry(fet.geometry().centroid())
            featureid = fet["id"] + 2000
            fetPoint.setAttributes([featureid, fet["cas_od"], fet["cas_do"], fet["vaha"]])
            providerPoint.addFeatures([fetPoint])
        layerPoint.commitChanges()
        layerPoint.triggerRepaint()

    # It does not work
    # I do not know why it does not work
    def movePointJTSK(self, x, y):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        provider = layer.dataProvider()
        features = provider.getFeatures()
        layer.startEditing()
        for fet in features:
            geom = fet.geometry()
            pt = geom.asPoint()
            # print str(pt)
            # print str(x) + " " + str(y)

    def getSearchID(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        searchid = open(DATAPATH + '/config/searchid.txt', 'r').read()
        return searchid

    def showPeopleTracks(self):
        """Shows tracks of logged positions in map"""
        # Check if the project has patraci_lines.shp
        if not self.checkLayer("/pracovni/patraci_lines.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu pátračů. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/patraci_lines.shp":
                layer = lyr
                break
        provider = layer.dataProvider()
        features = provider.getFeatures()
        sectorid = 0
        layer.startEditing()
        listOfIds = [feat.id() for feat in layer.getFeatures()]
        # Deletes all features in layer patraci.shp
        layer.deleteFeatures(listOfIds)
        response = None
        try:
            # Connects the server with log
            response = urllib2.urlopen(
                self.serverUrl + 'operation=gettracks&searchid=' + self.getSearchID(), None, 20)
            # Reads locations from response
            locations = response.read()
            # Splits to lines
            lines = locations.split("\n")
            # Loops the lines
            for line in lines:
                if line != "":  # add other needed checks to skip titles
                    # Splits based on semicolon
                    # TODO - add time
                    cols = line.split(";")
                    fet = QgsFeature()
                    # Name and sessionid are on first and second place
                    fet.setAttributes([str(cols[0]), str(cols[1]), str(cols[2]), str(cols[3]).decode('utf8')])
                    # Geometry is on third and fourth places
                    points = []
                    position = 0
                    # print "COLS: " + str(len(cols))
                    for col in cols:
                        if position > 3:
                            try:
                                xy = str(col).split(" ")
                                point = QgsPoint(float(xy[0]), float(xy[1]))
                                points.append(point)
                            except:
                                QgsMessageLog.logMessage(u"Problém s načtením dat z databáze: " + line, "Patrac")
                                pass
                        position = position + 1
                    if len(points) > 1:
                        line = QgsGeometry.fromPolyline(points)
                        fet.setGeometry(line)
                        provider.addFeatures([fet])
            layer.commitChanges()
            layer.triggerRepaint()
        except urllib2.URLError as e:
            QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
        except socket.timeout:
            QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
        self.setCursor(Qt.ArrowCursor)

    def showPeople(self):
        """Shows location of logged positions in map"""

        # Check if the project has patraci.shp
        if not self.checkLayer("/pracovni/patraci.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu pátračů. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/patraci.shp":
                layer = lyr
                break
        provider = layer.dataProvider()
        features = provider.getFeatures()
        sectorid = 0
        layer.startEditing()
        listOfIds = [feat.id() for feat in layer.getFeatures()]
        # Deletes all features in layer patraci.shp
        layer.deleteFeatures(listOfIds)
        response = None
        try:
            # Connects the server with locations
            response = urllib2.urlopen(
                self.serverUrl + 'operation=getlocations&searchid=' + self.getSearchID(), None, 5)
            # Reads locations from response
            locations = response.read()
            # print("LOCATIONS: " + locations)
            # Splits to lines
            lines = locations.split("\n")
            # Loops the lines
            for line in lines:
                if line != "":  # add other needed checks to skip titles
                    # Splits based on semicolon
                    # TODO - add time
                    cols = line.split(";")
                    fet = QgsFeature()
                    # Geometry is on last place
                    try:
                        xy = str(cols[4]).split(" ")
                        fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(xy[0]), float(xy[1]))))
                        # Name and sessionid are on first and second place
                        fet.setAttributes([str(cols[0]), str(cols[1]), str(cols[2]), str(cols[3]).decode('utf8')])
                        provider.addFeatures([fet])
                    except:
                        QgsMessageLog.logMessage(u"Problém s načtením dat z databáze: " + line, "Patrac")
                        pass
            layer.commitChanges()
            layer.triggerRepaint()
        except urllib2.URLError as e:
            QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
        except socket.timeout:
            QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
        self.setCursor(Qt.ArrowCursor)

    def azimuth(self, point1, point2):
        '''azimuth between 2 QGIS points ->must be adapted to 0-360°'''
        angle = math.atan2(point2.x() - point1.x(), point2.y() - point1.y())
        angle = math.degrees(angle)
        if angle < 0:
            angle = 360 + angle
        return angle

    def avg_time(self, datetimes):
        """Returns average datetime from two datetimes"""
        epoch = datetime.utcfromtimestamp(0)
        dt1 = (datetimes[0] - epoch).total_seconds()
        dt2 = (datetimes[1] - epoch).total_seconds()
        dt1_dt2 = (dt1 + dt2) / 2
        dt1_dt2_datetime = datetime.utcfromtimestamp(dt1_dt2)
        return dt1_dt2_datetime
        # return datetimes[0]

    def feature_agv_time(self, feature):
        cas_od = feature["cas_od"]
        cas_od_datetime = datetime.strptime(cas_od, '%Y-%m-%d %H:%M:%S')
        cas_do = feature["cas_do"]
        cas_do_datetime = datetime.strptime(cas_do, '%Y-%m-%d %H:%M:%S')
        cas_datetime = self.avg_time([cas_od_datetime, cas_do_datetime])
        return cas_datetime

    def filterAndSortFeatures(self, features):
        items = []
        featuresIndex = 0
        weightLimit = self.getWeightLimit()
        for feature in features:
            print
            "VAHA: " + str(feature["vaha"])
            if feature["vaha"] > weightLimit:
                featuresIndex += 1
                index = 0
                for item in items:
                    feature_cas = self.feature_agv_time(feature)
                    item_cas = self.feature_agv_time(item)
                    if feature_cas < item_cas:
                        items.insert(index, feature)
                        break
                    index += 1
                if len(items) < featuresIndex:
                    items.append(feature)
        return items

    def getRadial(self, features):
        """Computes direction of movement"""
        from_geom = None
        to_geom = None
        geom = features[len(features) - 2].geometry()
        from_geom = geom.asPoint()
        geom = features[len(features) - 1].geometry()
        to_geom = geom.asPoint()
        # Computes azimuth from two last points of collection
        azimuth = self.azimuth(from_geom, to_geom)
        QgsMessageLog.logMessage(u"Azimut " + str(azimuth), "Patrac")
        # QgsMessageLog.logMessage(u"Čas " + str(cas_datetime_max1) + " Id " + str(id_max1), "Patrac")
        # QgsMessageLog.logMessage(u"Čas " + str(cas_datetime_max2) + " Id " + str(id_max2), "Patrac")
        # cas_diff = cas_datetime_max2 - cas_datetime_max1
        # cas_diff_seconds = cas_diff.total_seconds()
        # QgsMessageLog.logMessage(u"Doba " + str(cas_diff_seconds), "Patrac")
        distance = QgsDistanceArea()
        distance_m = distance.measureLine(from_geom, to_geom)
        QgsMessageLog.logMessage(u"Vzdálenost " + str(distance_m), "Patrac")
        # speed_m_s = distance_m / cas_diff_seconds
        # QgsMessageLog.logMessage(u"Rychlost " + str(speed_m_s), "Patrac")
        return azimuth

    def getRadialAlpha(self, i, KVADRANT):
        """Returns angle based on quandrante"""
        alpha = (math.pi / float(2)) - ((math.pi / float(180)) * i)
        if KVADRANT == 2:
            alpha = ((math.pi / float(180)) * i) - (math.pi / float(2))
        if KVADRANT == 3:
            alpha = (3 * (math.pi / float(2))) - ((math.pi / float(180)) * i)
        if KVADRANT == 4:
            alpha = ((math.pi / float(180)) * i) - (3 * (math.pi / float(2)))
        return alpha

    def getRadialTriangleX(self, alpha, CENTERX, xdir, RADIUS):
        """Gets X coordinate of the triangle"""
        dx = xdir * math.cos(alpha) * RADIUS
        x = CENTERX + dx
        return x

    def getRadialTriangleY(self, alpha, CENTERY, ydir, RADIUS):
        """Gets Y coordinate of the triangle"""
        dy = ydir * math.sin(alpha) * RADIUS
        y = CENTERY + dy
        return y

    def generateRadialOnPoint(self, feature):
        """Generates triangles from defined point in step one degree"""
        geom = feature.geometry()
        x = geom.asPoint()
        coords = str(x)[1:-1]
        coords_splitted = coords.split(',')
        CENTERX = float(coords_splitted[0])
        CENTERY = float(coords_splitted[1])
        # Radius is set ot 20000 meters to be sure that whole area is covered
        RADIUS = 20000;
        # Writes output to radial.csv
        csv = open(self.pluginPath + "/grass/radial.csv", "w")
        # Writes in WKT format
        csv.write("id;wkt\n")
        self.generateRadial(CENTERX, CENTERY, RADIUS, 1, csv)
        self.generateRadial(CENTERX, CENTERY, RADIUS, 2, csv)
        self.generateRadial(CENTERX, CENTERY, RADIUS, 3, csv)
        self.generateRadial(CENTERX, CENTERY, RADIUS, 4, csv)
        csv.close()

    def generateRadial(self, CENTERX, CENTERY, RADIUS, KVADRANT, csv):
        """Generates triangles in defined quadrante"""
        # First quadrante is from 0 to 90 degrees
        # In both axes is coordinates increased
        from_deg = 0
        to_deg = 90
        xdir = 1
        ydir = 1
        # Second quadrante is from 90 to 180 degrees
        # In axe X is coordinate increased
        # In axe Y is coordinate decreased
        if KVADRANT == 2:
            from_deg = 90
            to_deg = 180
            xdir = 1
            ydir = -1
        # Second quadrante is from 180 to 270 degrees
        # In axe X is coordinate decreased
        # In axe Y is coordinate decreased
        if KVADRANT == 3:
            from_deg = 180
            to_deg = 270
            xdir = -1
            ydir = -1
        # Second quadrante is from 270 to 360 degrees
        # In axe X is coordinate decreased
        # In axe Y is coordinate increased
        if KVADRANT == 4:
            from_deg = 270
            to_deg = 360
            xdir = -1
            ydir = 1
        for i in xrange(from_deg, to_deg):
            alpha = self.getRadialAlpha(i, KVADRANT);
            x = self.getRadialTriangleX(alpha, CENTERX, xdir, RADIUS)
            y = self.getRadialTriangleY(alpha, CENTERY, ydir, RADIUS)
            # Special condtions where one of the axes is on zero direction
            if i == 0:
                x = CENTERX
                y = CENTERY + RADIUS
            if i == 90:
                x = CENTERX + RADIUS
                y = CENTERY
            if i == 180:
                x = CENTERX
                y = CENTERY - RADIUS
            if i == 270:
                x = CENTERX - RADIUS
                y = CENTERY
            # Triangle is written as Polygon
            wkt_polygon = "POLYGON((" + str(CENTERX) + " " + str(CENTERY) + ", " + str(x) + " " + str(y)
            alpha = self.getRadialAlpha(i + 1, KVADRANT);
            x = self.getRadialTriangleX(alpha, CENTERX, xdir, RADIUS)
            y = self.getRadialTriangleY(alpha, CENTERY, ydir, RADIUS)
            # Special condtions where one of the axes is on zero direction
            if i == 89:
                x = CENTERX + RADIUS
                y = CENTERY
            if i == 179:
                x = CENTERX
                y = CENTERY - RADIUS
            if i == 269:
                x = CENTERX - RADIUS
                y = CENTERY
            if i == 359:
                x = CENTERX
                y = CENTERY + RADIUS
            wkt_polygon = wkt_polygon + ", " + str(x) + " " + str(y) + ", " + str(CENTERX) + " " + str(CENTERY) + "))"
            csv.write(str(i) + ";" + wkt_polygon + "\n")

    def writeAzimuthReclass(self, azimuth, tolerance, friction):
        """Creates reclass rules for direction
            Tolerance is for example 30 degrees
            Friction is how frict is the direction
        """
        reclass = open(self.pluginPath + "/grass/azimuth_reclass.rules", "w")
        tolerance_half = tolerance / 2
        astart = int(azimuth) - tolerance_half
        aend = int(azimuth) + tolerance_half
        if astart < 0:
            astart = 360 + astart
            reclass.write(str(astart) + " thru 360 = 0\n")
            reclass.write("0 thru " + str(aend) + " = 0\n")
            reclass.write("* = " + str(friction) + "\n")
            reclass.write("end\n")
        else:
            if aend > 360:
                aend = aend - 360
                reclass.write(str(astart) + " thru 360 = 0\n")
                reclass.write("0 thru " + str(aend) + " = 0\n")
                reclass.write("* = " + str(friction) + "\n")
                reclass.write("end\n")
            else:
                reclass.write(str(astart) + " thru " + str(aend) + "= 0\n")
                reclass.write("* = " + str(friction) + "\n")
                reclass.write("end\n")
        # reclass.write(str(azimuth) + " " + str(tolerance) + " " + str(friction) + "\n")
        reclass.close()

    def creation_date(self, path_to_file):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See http://stackoverflow.com/a/39501288/1709587 for explanation.
        """
        if sys.platform.startswith('win'):
            return os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime

    # Tests
    def loadTestProject(self):
        project = QgsProject.instance()
        project.read(QFileInfo(self.pluginPath + '/tests/data/zahradka__plzen-sever_/clean.qgs'))

    def compareFiles(self, file1, file2, datetimefile1_orig):
        # we test just the binary content
        datetimefile1 = self.creation_date(file1)
        if (filecmp.cmp(file1, file2)) and (datetimefile1 != datetimefile1_orig):
            return True
        else:
            return False

    # Happy day scenario test
    def testHds(self):
        # prepare

        # load project
        self.loadTestProject()

        # get area
        datetimefile1_orig = self.creation_date(
            self.pluginPath + '/tests/data/zahradka__plzen-sever_/pracovni/distances_costed_cum.tif')
        self.getArea()
        # the tiff should be the same as matrice

        if self.compareFiles(self.pluginPath + '/tests/data/zahradka__plzen-sever_/pracovni/distances_costed_cum.tif',
                             self.pluginPath + '/tests/data/zahradka__plzen-sever_/tests/distances_costed_cum.tif',
                             datetimefile1_orig):
            QgsMessageLog.logMessage(u"INFO: Area test skončil dobře (výstupní tif odpovídá očekávanému stavu)",
                                     "Patrac")
        else:
            QgsMessageLog.logMessage(u"ERROR: Area test skončil chybou (výstupní tif neodpovídá očekávanému stavu)",
                                     "Patrac")

        # get sectors
        datetimefile1_orig = self.creation_date(
            self.pluginPath + '/tests/data/zahradka__plzen-sever_/pracovni/sektory_group_selected.shp')
        self.sliderEnd.setValue(60)
        self.getSectors(0,60)
        # the shp should be same as matrice
        if self.compareFiles(self.pluginPath + '/tests/data/zahradka__plzen-sever_/pracovni/sektory_group_selected.shp',
                             self.pluginPath + '/tests/data/zahradka__plzen-sever_/tests/sektory_group_selected.shp',
                             datetimefile1_orig):
            QgsMessageLog.logMessage(u"INFO: Sectors test skončil dobře (výstupní SHP odpovídá očekávanému stavu)",
                                     "Patrac")
        else:
            QgsMessageLog.logMessage(u"ERROR: Sectors test skončil chybou (výstupní SHP neodpovídá očekávanému stavu)",
                                     "Patrac")

        # repost export
        datetimefile1_orig = self.creation_date(
            self.pluginPath + '/tests/data/zahradka__plzen-sever_/sektory/report.html')
        self.reportExportSectors(True, True)
        # the html should be same as matrice
        if self.compareFiles(self.pluginPath + '/tests/data/zahradka__plzen-sever_/sektory/report.html',
                             self.pluginPath + '/tests/data/zahradka__plzen-sever_/tests/report.html',
                             datetimefile1_orig):
            QgsMessageLog.logMessage(
                u"INFO: Report_Export test skončil dobře (výstupní HTML odpovídá očekávanému stavu)", "Patrac")
        else:
            QgsMessageLog.logMessage(
                u"ERROR: Report_Export test skončil chybou (výstupní HTML neodpovídá očekávanému stavu)", "Patrac")
