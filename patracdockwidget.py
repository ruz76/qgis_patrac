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
from PyQt4.QtCore import QSettings

from qgis.core import *
from qgis.gui import *

from ui.ui_patracdockwidgetbase import Ui_PatracDockWidget
from ui.ui_settings import Ui_Settings
from ui.ui_gpx import Ui_Gpx
from ui.ui_message import Ui_Message
from ui.ui_coords import Ui_Coords
from ui.ui_point_tool import PointMapTool
from ui.ui_progress_tool import ProgressMapTool

from main.printing import Printing
from main.project import ZPM_Raster, Project
from main.area import Area
from main.utils import Utils
from main.sectors import Sectors
from main.hds import Hds
from main.styles import Styles

import os, sys, subprocess, time, urllib2, math, socket

from glob import glob
from urllib2 import quote
from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime

import csv, io, webbrowser, filecmp, uuid, random, getpass

#If on windows
try:
    import win32api
except:
    QgsMessageLog.logMessage(u"Linux - no win api", "Patrac")

class PatracDockWidget(QDockWidget, Ui_PatracDockWidget, object):
    def __init__(self, plugin):

        self.plugin = plugin
        self.iface = self.plugin.iface
        self.canvas = self.plugin.iface.mapCanvas()
        self.maxVal = 100
        self.minVal = 0
        self.serverUrl = 'http://gisak.vsb.cz/patrac/'
        self.currentStep = 1

        userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "python/plugins/qgis_patrac"
        systemPluginPath = QgsApplication.prefixPath() + "python/plugins/qgis_patrac"
        if QFileInfo(userPluginPath).exists():
            self.pluginPath = userPluginPath
        else:
            self.pluginPath = systemPluginPath

        QDockWidget.__init__(self, None)
        self.setupUi(self)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

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
        self.tbtnExtendRegion.clicked.connect(self.extendRegion)
        self.tbtnImportPaths.clicked.connect(self.showImportGpx)
        #self.tbtnShowSearchers.clicked.connect(self.showPeopleSimulation)
        self.tbtnShowSearchers.clicked.connect(self.showPeople)
        self.tbtnShowSearchersTracks.clicked.connect(self.showPeopleTracks)
        self.tbtnShowMessage.clicked.connect(self.showMessage)

        self.tbtnInsertFinal.clicked.connect(self.insertFinal)

        # Dialogs and tools are defined here
        self.settingsdlg = Ui_Settings(self.pluginPath, self)
        self.coordsdlg = Ui_Coords()
        self.pointtool = PointMapTool(self.plugin.iface.mapCanvas())
        self.progresstool = ProgressMapTool(self.plugin.iface.mapCanvas(), self.plugin.iface)

        self.setStepsConnection()

        # Help show
        self.helpShow.clicked.connect(self.showHelp)

        self.currentTool = self.iface.mapCanvas().mapTool()
        self.personType = 1

        self.Utils = Utils(self)
        self.Project = Project(self)
        self.Printing = Printing(self)
        self.Area = Area(self)
        self.Sectors = Sectors(self)
        self.Hds = Hds(self)
        self.Styles = Styles(self)
        self.sectorsUniqueStyle.clicked.connect(self.setSectorsUniqueValuesStyle)
        self.sectorsSingleStyle.clicked.connect(self.setSectorsSingleValuesStyle)
        self.sectorsLabelsOn.clicked.connect(self.setSectorsLabelsOn)
        self.sectorsLabelsOff.clicked.connect(self.setSectorsLabelsOff)
        self.sectorsProgressStyle.clicked.connect(self.setSectorsProgressStyle)
        self.sectorsUnitsStyle.clicked.connect(self.setSectorsUnitsStyle)
        self.sectorsProgress.clicked.connect(self.setSectorsProgress)


    def showHelp(self):
        webbrowser.open("file://" + self.pluginPath + "/doc/index.html")

    def getPluginPath(self):
        return self.pluginPath

    def setStepsConnection(self):
        # Autocompleter fro search of municipalities
        self.setCompleter(self.guideMunicipalitySearch)
        #self.guideMunicipalitySearch.returnPressed.connect(self.runGuideMunicipalitySearch)

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
        self.guideCopyGpx.clicked.connect(self.copyGpx)

    def runCreateProject(self):
        name = self.msearch.text()
        self.Project.createProject(name)

    def runCreateProjectGuide(self, index):
        desc = self.guideSearchDescription.text()
        self.Project.createProject(index, desc)

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
            return -1
        except IndexError:
            return -1

    def runExpertMunicipalitySearch(self):
        self.municipalitySearch(self.msearch)

    def runGuideMunicipalitySearch(self):
        municipalityindex = self.municipalitySearch(self.guideMunicipalitySearch)

        if municipalityindex < 0:
            return

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
        self.currentStep = 2

    def checkStep(self, nextStep):
        if self.currentStep == nextStep - 1:
            return True
        else:
            reply = QMessageBox.question(self, u'Krok',
                                         u'Přeskočili jste krok v průvodci. Chcete pokračovat?',
                                         QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                return True
            else:
                return False

    def runGuideStep2Next(self):
        if not self.checkStep(3):
            return

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
        self.currentStep = 3

    def runGuideStep3Next(self):
        if not self.checkStep(4):
            return

        # run area determination computation
        self.personType = self.guideComboPerson.currentIndex() + 1
        self.Area.getArea()

        # set spin to 70%
        self.__updateSliderEnd(70)

        # move to next tab (tab 4)
        self.tabGuideSteps.setCurrentIndex(3)
        self.currentStep = 4

    def runGuideStep4Next(self):
        if not self.checkStep(5):
            return

        # set percent of visibility
        self.spinStart.setValue(0)
        self.spinEnd.setValue(self.guideSpinEnd.value())
        self.updatePatrac()

        # move to next tab (tab 5)
        self.tabGuideSteps.setCurrentIndex(4)
        self.currentStep = 5

    def runGuideStep5Next(self):
        if not self.checkStep(6):
            return

        # saves information about available resources
        self.saveUnitsInformation()

        # saves maxtime information
        self.saveMaxTimeInformation()

        # select sectors
        self.runGuideGetSectors()

        # run sectors selection and exports
        self.Sectors.reportExportSectors(False, False)

        # move to next tab (tab 6)
        self.tabGuideSteps.setCurrentIndex(5)
        self.currentStep = 6

    def exportSectors(self):
        self.Sectors.exportSectors()

    def showReport(self):
        self.setCursor(Qt.WaitCursor)

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()

        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/distances_costed_cum.tif":
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, "CHYBA:",
                                    u"Nemohu najít vrstvu pravděpodobnosti. Nemohu pokračovat.");
            return

        transparencyList = []
        transparencyList.extend(self.generateTransparencyList(0, 100))
        layer.setCacheImage(None)
        layer.renderer().rasterTransparency().setTransparentSingleValuePixelList(transparencyList)
        self.plugin.iface.mapCanvas().refresh()

        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if DATAPATH + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, "CHYBA:",
                                    u"Nemohu najít vrstvu sektorů. Nemohu pokračovat.");
            return

        # exports overall map with all sectors to PDF
        if self.chkGenerateOverallPDF.isChecked():
            self.Printing.exportPDF(layer.extent(), DATAPATH + "/sektory/report.pdf")


        # exports map of sectors to PDF
        #if self.chkGeneratePDF.isChecked():
        #    self.exportPDF(layer.extent(), DATAPATH + "/sektory/report.pdf")

        #    provider = layer.dataProvider()
        #    features = provider.getFeatures()
        #    for feature in features:
        #        self.exportPDF(feature.geometry().boundingBox(), DATAPATH + "/sektory/pdf/" + feature['label'] + ".pdf")

        webbrowser.get().open("file://" + DATAPATH + "/sektory/report.html")
        self.setCursor(Qt.ArrowCursor)

    def copyGpx(self):
        drives = None
        if sys.platform.startswith('win'):
            drives = win32api.GetLogicalDriveStrings()
            drives = drives.split('\000')[:-1]
        else:
            username = getpass.getuser()
            drives = []
            for dirname in os.listdir('/media/' + username + '/'):
                drives.append('/media/' + username + '/' + dirname + '/')

        drives_gpx = []
        for drive in drives:
            if os.path.isdir(drive + 'Garmin/GPX'):
               drives_gpx.append(drive)

        if len(drives_gpx) == 1:
            # nice, only one GPX dir is available
            self.copyGpxToPath(drives_gpx[0] + 'Garmin/GPX')

        if len(drives_gpx) == 0:
            # Not Garmin. TODO
            QMessageBox.information(None, "INFO:", u"Nenašel jsem připojenou GPS. Soubor musite uložit jako z reportu ručně.")

        if len(drives_gpx) > 1:
            # We have more than one place with garmin/GPX
            item, ok = QInputDialog.getItem(self, "select input dialog", "list of drives", drives_gpx, 0, False)
            if ok and item:
                self.copyGpxToPath(item + 'Garmin/GPX')

    def copyGpxToPath(self, path):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        time = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
        copy(DATAPATH + '/sektory/gpx/all.gpx', path + "/sektory_" + time + ".gpx")
        if os.path.isfile(path + "/sektory_" + time + ".gpx"):
            QMessageBox.information(None, "INFO:", u"Sektory byly zkopírovány do zařízení: " + path + "/sektory_" + time + ".gpx")
        else:
            QMessageBox.information(None, "CHYBA:",
                                    u"Při kopírování sektorů došlo k chybě. Zkopírujte přes správce souborů z cesty: " + DATAPATH + '/sektory/gpx/all.gpx')

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

    def saveMaxTimeInformation(self):
        f = io.open(self.pluginPath + '/grass/maxtime.txt', 'w', encoding='utf-8')
        f.write(self.guideMaxTime.text())
        f.close()

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
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if DATAPATH + "/pracovni/distances_costed_cum.tif" in lyr.source():
                layer = lyr
                break

        if layer == None:
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu pravděpodobnosti. Zkuste prosím znovu použít krok 3 v průvodci.")
            return

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

        #if not self.chkManualUpdate.isChecked():
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

        #if not self.chkManualUpdate.isChecked():
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

    def runExpertGetArea(self):
        self.personType = self.comboPerson.currentIndex() + 1
        self.Area.getArea()

    def runExpertGetSectors(self):
        self.Sectors.getSectors(self.sliderStart.value(), self.sliderEnd.value())

    def runExpertReportExportSectors(self):
        self.Sectors.reportExportSectors(True, True)

    def runGuideGetSectors(self):
        self.Sectors.getSectors(0, self.guideSpinEnd.value())

    def recalculateSectorsExpert(self):
        self.Sectors.recalculateSectors(False)
        # TODO change icon and name of the function
        #self.extendRegion()

    def extendRegion(self):
        self.Sectors.extendRegion()

    def showSettings(self):
        """Shows the settings dialog"""
        self.settingsdlg.updateSettings()
        self.settingsdlg.show()

    def showMessage(self):
        """Show the dialog for sending messages"""
        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový pomocí průvodce.")
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
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový pomocí průvodce.")
            return

        self.importgpxdlg = Ui_Gpx(self.pluginPath)
        self.importgpxdlg.show()

    def insertFinal(self):
        """Sets tool to pointtool to be able handle from click to map.
            It is used at the time when the search is finished.
        """
        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový pomocí průvodce.")
            return

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.pointtool.setDataPath(DATAPATH)
        self.pointtool.setSearchid(self.getSearchID())
        self.plugin.iface.mapCanvas().setMapTool(self.pointtool)

    def setSectorsProgress(self):
        # Check if the project has sektory_group_selected.shp
        if not self.Utils.checkLayer("/pracovni/sektory_group.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu sektorů. Otevřete správný projekt, nebo vygenerujte nový pomocí průvodce.")
            return

        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if self.Utils.getDataPath() + "/pracovni/sektory_group.shp" in lyr.source():
                layer = lyr
                break

        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.progresstool.setDataPath(DATAPATH)
        self.progresstool.setPluginPath(self.pluginPath)
        attribute = 3
        type = 1
        if self.sectorsProgressStateNotStarted.isChecked() == True:
            attribute = 3
            type = 0
        if self.sectorsProgressStateStarted.isChecked() == True:
            attribute = 3
            type = 1
        if self.sectorsProgressStateFinished.isChecked() == True:
            attribute = 3
            type = 2
        if self.sectorsProgressAnalyzeTrack.isChecked() == True:
            attribute = -1
            type = 0
        self.progresstool.setAttribute(attribute)
        self.progresstool.setType(type)
        self.progresstool.setLayer(layer)
        self.plugin.iface.mapCanvas().setMapTool(self.progresstool)

    def definePlaces(self):
        """Moves the selected point to specified coordinates
            Or converts lines to points
            Or converts polygons to points
        """
        # Check if the project has mista.shp
        if not self.Utils.checkLayer("/pracovni/mista.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu míst. Otevřete správný projekt, nebo vygenerujte nový pomocí průvodce.")
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
            if DATAPATH + "/pracovni/mista.shp" in lyr.source():
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

    def addFeaturePolyLineFromPoints(self, points, cols, provider):
        fet = QgsFeature()
        # Name and sessionid are on first and second place
        fet.setAttributes([str(cols[0]), str(cols[1]), str(cols[2]), str(cols[3]).decode('utf8')])
        # Geometry is on third and fourth places
        if len(points) > 1:
            line = QgsGeometry.fromPolyline(points)
            fet.setGeometry(line)
            provider.addFeatures([fet])

    def showPeopleTracks(self):
        """Shows tracks of logged positions in map"""
        # Check if the project has patraci_lines.shp
        if not self.Utils.checkLayer("/pracovni/patraci_lines.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu pátračů. Otevřete správný projekt, nebo vygenerujte nový pomocí průvodce.")
            return

        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if DATAPATH + "/pracovni/patraci_lines.shp" in lyr.source():
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
                self.serverUrl + 'track.php?searchid=' + self.getSearchID(), None, 20)
            # Reads locations from response
            locations = response.read()
            if "Error" in locations:
                QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
                return
            # Splits to lines
            lines = locations.split("\n")
            # Loops the lines
            for line in lines:
                if line != "":  # add other needed checks to skip titles
                    # Splits based on semicolon
                    # TODO - add time
                    cols = line.split(";")
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
                                QgsMessageLog.logMessage(u"Problém s načtením dat z databáze: " + line.decode('utf8'), "Patrac")
                                pass
                        position = position + 1
                    self.addFeaturePolyLineFromPoints(points, cols, provider)
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
        if not self.Utils.checkLayer("/pracovni/patraci.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu pátračů. Otevřete správný projekt, nebo vygenerujte nový pomocí průvodce.")
            return

        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if DATAPATH + "/pracovni/patraci.shp" in lyr.source():
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
                self.serverUrl + 'loc.php?searchid=' + self.getSearchID(), None, 5)
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

    def showPeopleSimulation(self):
        """Shows location of logged positions in map"""

        # Check if the project has patraci.shp
        if not self.Utils.checkLayer("/pracovni/patraci.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu pátračů. Otevřete správný projekt, nebo vygenerujte nový pomocí průvodce.")
            return

        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if DATAPATH + "/pracovni/patraci.shp" in lyr.source():
                layer = lyr
                break
        provider = layer.dataProvider()
        features = provider.getFeatures()
        sectorid = 0
        layer.startEditing()
        listOfIds = [feat.id() for feat in layer.getFeatures()]
        # Deletes all features in layer patraci.shp
        layer.deleteFeatures(listOfIds)
        center = self.plugin.canvas.center()
        hh = int(self.plugin.canvas.height() / 2)
        for i in range(0, 10):
            fet = QgsFeature()
            rand = random.randint(-1 * hh, hh)
            rand2 = random.randint(-1 * hh, hh)
            crs_src = QgsCoordinateReferenceSystem(5514)
            crs_dest = QgsCoordinateReferenceSystem(4326)
            xform = QgsCoordinateTransform(crs_src, crs_dest)
            point_5514 = QgsPoint(center.x() + rand, center.y() + rand2)
            point_4326 = xform.transform(point_5514)
            fet.setGeometry(QgsGeometry.fromPoint(point_4326))
            fet.setAttributes(['idpatrani', '2019-09-03T13:00:00', 'A', 'Karel ' + str(i)])
            provider.addFeatures([fet])
        layer.commitChanges()
        layer.triggerRepaint()
        self.setCursor(Qt.ArrowCursor)

    def testHds(self):
        self.Hds.testHds()

    def setSectorsUniqueValuesStyle(self):
        self.Styles.setSectorsStyle('unique')

    def setSectorsSingleValuesStyle(self):
        self.Styles.setSectorsStyle('single')

    def setSectorsLabelsOn(self):
        self.Styles.setSectorsStyle('single')

    def setSectorsLabelsOff(self):
        self.Styles.setSectorsStyle('single_no_labels')

    def setSectorsProgressStyle(self):
        self.Styles.setSectorsStyle('stav')

    def setSectorsUnitsStyle(self):
        QMessageBox.information(None, "INFO:",
                                u"Funkce není implementována.")
