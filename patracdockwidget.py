# -*- coding: utf-8 -*-

#******************************************************************************
#
# Patrac
# ---------------------------------------------------------
# Podpora hledání pohřešované osoby
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
#******************************************************************************


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from ui.ui_patracdockwidgetbase import Ui_PatracDockWidget
from ui.ui_settings import Ui_Settings
from ui.ui_gpx import Ui_Gpx
from ui.ui_message import Ui_Message

import os
import sys
import subprocess
from glob import glob
#from osgeo import ogr
#from osgeo import gdal
import time
import urllib2

class PatracDockWidget(QDockWidget, Ui_PatracDockWidget, object):
    def __init__(self, plugin):
        QDockWidget.__init__(self, None)
        self.setupUi(self)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.plugin = plugin
        self.maxVal = 100
        self.minVal = 0

        # connect signals and slots
        self.chkManualUpdate.stateChanged.connect(self.__toggleRefresh)
        self.btnRefresh.clicked.connect(self.updatePatrac)
        self.btnGetArea.clicked.connect(self.getArea)

        self.sliderStart.valueChanged.connect(self.__updateSpinStart)
        self.spinStart.valueChanged.connect(self.__updateSliderStart)
        self.sliderEnd.valueChanged.connect(self.__updateSpinEnd)
        self.spinEnd.valueChanged.connect(self.__updateSliderEnd)

        self.btnGetSectors.clicked.connect(self.getSectors)
        self.btnRecalculateSectors.clicked.connect(self.recalculateSectors)
        self.btnExportSectors.clicked.connect(self.exportSectors)
        self.btnShowSettings.clicked.connect(self.showSettings)
        self.btnImportGpx.clicked.connect(self.showImportGpx)
        self.btnShowPeople.clicked.connect(self.showPeople)
        self.btnShowMessage.clicked.connect(self.showMessage)

        settings = QSettings("alexbruy", "Patrac")
        self.chkManualUpdate.setChecked(bool(settings.value("manualUpdate", False)))
        userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/qgis_patrac"
        systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/qgis_patrac"
        if QFileInfo(userPluginPath).exists():
            self.pluginPath = userPluginPath
        else:
            self.pluginPath = systemPluginPath

        self.settingsdlg = Ui_Settings(self.pluginPath)
        ##self.importgpxdlg.buttonBox.accepted.connect(self.importgpxdlg.accept)

    def updatePatrac(self):

        transparencyList = []

        if self.sliderStart.value() != 0:
            transparencyList.extend(self.generateTransparencyList(0, self.sliderStart.value()))

        if self.sliderEnd.value() != self.maxVal:
            transparencyList.extend(self.generateTransparencyList(self.sliderEnd.value(), self.maxVal))

        # update layer transparency
        layer = self.plugin.iface.mapCanvas().currentLayer()
        layer.setCacheImage(None)
        layer.renderer().rasterTransparency().setTransparentSingleValuePixelList(transparencyList)
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
        #self.maxVal = int(maxValue)
        #self.minVal = int(minValue)

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

    def getArea(self):
        #Vybrana vrstva
        #qgis.utils.iface.setActiveLayer(QgsMapLayer)
        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath() 
        self.removeLayer(DATAPATH + '/pracovni/distances_costed_cum.tif')
        layer=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        if layer==None:
            QMessageBox.information(None, "INFO:", u"Nebyla nalezena vrstva s místy. Nemohu určit oblast.")
            self.setCursor(Qt.ArrowCursor)
            return
        #layer = self.plugin.iface.activeLayer()
        i = 0
        distances_costed_cum = ""
        for feature in layer.getFeatures():
            geom = feature.geometry()
            x = geom.asPoint()            
            coords = str(x)[1:-1]
            f_coords = open(self.pluginPath + '/grass/coords.txt', 'w')
            f_coords.write(coords)
            f_coords.close()    
            print '*******Coords: ' + coords
            if sys.platform.startswith('win'):
                p = subprocess.Popen((self.pluginPath + "/grass/run_cost_distance.bat", DATAPATH, self.pluginPath, str(i), str(self.comboPerson.currentIndex()+1)))
                p.wait()
                #os.system(self.pluginPath + "/grass/run_cost_distance.bat " + DATAPATH + " " + self.pluginPath + " " + str(i) + " " + str(self.comboPerson.currentIndex()+1))
            else:
                p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_cost_distance.sh", DATAPATH, self.pluginPath, str(i), str(self.comboPerson.currentIndex()+1)))
                p.wait()
                #os.system("bash " + self.pluginPath + "/grass/run_cost_distance.sh " + DATAPATH + " " + self.pluginPath + " " + str(i) + " " + str(self.comboPerson.currentIndex()+1))
            if (i == 0):
                distances_costed_cum = "distances0_costed"
            else:
                distances_costed_cum = distances_costed_cum + ",distances" + str(i) + "_costed"
            i += 1
        #Windows - nutno nejdrive smazat tif
        #driver = gdal.GetDriverByName('GTiff')
        #driver.DeleteDataSource(DATAPATH + "/pracovni/distances_costed_cum.tif")
        #time.sleep(1)
        if os.path.isfile(DATAPATH + '/pracovni/distances_costed_cum.tif.aux.xml'):
            os.remove(DATAPATH + '/pracovni/distances_costed_cum.tif.aux.xml')
        if os.path.isfile(DATAPATH + '/pracovni/distances_costed_cum.tif'):
            os.remove(DATAPATH + '/pracovni/distances_costed_cum.tif')
        if os.path.isfile(DATAPATH + '/pracovni/distances_costed_cum.tfw'):
            os.remove(DATAPATH + '/pracovni/distances_costed_cum.tfw')    
           
        print "Spoustim python " + self.pluginPath + "/grass/run_distance_costed_cum.sh " + distances_costed_cum
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_distance_costed_cum.bat", DATAPATH, self.pluginPath, distances_costed_cum))
            p.wait()
            #os.system(self.pluginPath + "/grass/run_distance_costed_cum.bat " + DATAPATH + " " + self.pluginPath + " " + distances_costed_cum)
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_distance_costed_cum.sh", DATAPATH, self.pluginPath, distances_costed_cum))
            p.wait()            
            #os.system("bash " + self.pluginPath + "/grass/run_distance_costed_cum.sh " + DATAPATH + " " + self.pluginPath + " " + distances_costed_cum)
        self.addRasterLayer(DATAPATH + '/pracovni/distances_costed_cum.tif', 'procenta')
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/distances_costed_cum.tif":
                layer = lyr
                break
        layer.triggerRepaint()
        self.plugin.iface.setActiveLayer(layer)
        self.setCursor(Qt.ArrowCursor)
        return

    def getSectors(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.removeLayer(DATAPATH + '/pracovni/sektory_group_selected.shp')
        print "Spoustim python " + self.pluginPath + "/grass/sectors.py"
        self.setCursor(Qt.WaitCursor)
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_sectors.bat", DATAPATH, self.pluginPath, str(self.sliderStart.value()), str(self.sliderEnd.value())))
            p.wait()
            #os.system(self.pluginPath + "/grass/run_sectors.bat " + DATAPATH + " " + self.pluginPath + " " + str(self.sliderStart.value()) + " " + str(self.sliderEnd.value()))
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_sectors.sh", DATAPATH, self.pluginPath, str(self.sliderStart.value()), str(self.sliderEnd.value())))
            p.wait()
            #os.system("bash " + self.pluginPath + "/grass/run_sectors.sh " + DATAPATH + " " + self.pluginPath + " " + str(self.sliderStart.value()) + " " + str(self.sliderEnd.value()))
        self.addVectorLayer(DATAPATH + '/pracovni/sektory_group_selected.shp', 'sektory')    
        layer=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/sektory_group_selected.shp":
                layer = lyr
                break
        layer.dataProvider().forceReload()
               
        fList = list()
        fList.append(0)
        fList.append(1)
        layer.startEditing()
        layer.dataProvider().deleteAttributes(fList)
        layer.commitChanges()
        layer.triggerRepaint()
        self.setCursor(Qt.ArrowCursor)
        self.recalculateSectors()
        return
    
    def recalculateSectors(self):
        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath() 
        layer=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/sektory_group_selected.shp":
                layer = lyr
                break
        provider = layer.dataProvider()   
        features = provider.getFeatures()
        sectorid = 0
        layer.startEditing()
        for feature in features:
            sectorid = sectorid + 1
            feature['label'] = 'A' + str(sectorid)
            feature['area_ha'] = round(feature.geometry().area() / 10000)
            layer.updateFeature(feature)
        layer.commitChanges()
        layer.triggerRepaint()
        self.setCursor(Qt.ArrowCursor)
        return sectorid

    def exportSectors(self):
        sectorid = self.recalculateSectors()
        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath() 
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_report_export.bat", DATAPATH, self.pluginPath, str(sectorid)))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_report_export.sh", DATAPATH, self.pluginPath, str(sectorid)))
            p.wait()
        layer=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/sektory_group_selected.shp":
                layer = lyr
                break
        provider = layer.dataProvider()   
        features = provider.getFeatures()
        for feature in features:
            self.removeLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp")
            self.setStyle(DATAPATH + "/sektory/shp/", feature['label'])
            sector = QgsVectorLayer(DATAPATH + "/sektory/shp/" + feature['label'] + ".shp", feature['label'], "ogr")
            if not sector.isValid():
                print "Sector " + feature['label'] + "failed to load!"
            else:
                crs = QgsCoordinateReferenceSystem("EPSG:4326")
                QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + feature['label'] + ".gpx","utf-8", crs, "GPX", datasourceOptions=['GPX_USE_EXTENSIONS=YES','GPX_FORCE_TRACK-YES'])
                QgsMapLayerRegistry.instance().addMapLayer(sector)
        self.setCursor(Qt.ArrowCursor)
        return

    def removeLayer(self, path):
        layer=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == path:
                layer = lyr
                break
        if layer is not None:
            if layer.isValid():
                QgsMapLayerRegistry.instance().removeMapLayer(layer)
        return

    def setStyle(self, path, name):
        qml = open(path + 'style.qml', 'r').read()
        f = open(path + name + '.qml', 'w')
        qml = qml.replace("k=\"line_width\" v=\"0.26\"", "k=\"line_width\" v=\"1.2\"")
        f.write(qml)
        f.close()

    def showSettings(self):
        self.settingsdlg.show()

    def showMessage(self):
        self.messagedlg = Ui_Message(self.pluginPath)	
        self.messagedlg.show()

    def showImportGpx(self):
        self.importgpxdlg = Ui_Gpx(self.pluginPath)
        self.importgpxdlg.show()    

    def addRasterLayer(self, path, label):
        raster = QgsRasterLayer(path, label, "gdal")
        if not raster.isValid():
            print "Layer " + path + " failed to load!"
        else:
##            crs = QgsCoordinateReferenceSystem("EPSG:4326")
            QgsMapLayerRegistry.instance().addMapLayer(raster)

    def addVectorLayer(self, path, label):
        vector = QgsVectorLayer(path, label, "ogr")
        if not vector.isValid():
            print "Layer " + path + " failed to load!"
        else:
##            crs = QgsCoordinateReferenceSystem("EPSG:4326")
            QgsMapLayerRegistry.instance().addMapLayer(vector)  

    def showPeople(self):
        self.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath() 
        layer=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/patraci.shp":
                layer = lyr
                break
        provider = layer.dataProvider()   
        features = provider.getFeatures()
        sectorid = 0
        layer.startEditing()
        listOfIds = [feat.id() for feat in layer.getFeatures()]
        layer.deleteFeatures( listOfIds )
        response = urllib2.urlopen('http://158.196.143.122/patrac/mserver.php?operation=getlocations')
        locations = response.read()
        lines = locations.split("\n")
        for line in lines:
            if line != "": # add other needed checks to skip titles
                cols = line.split(";")
                fet = QgsFeature()
                fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(cols[2]),float(cols[1]))))
                fet.setAttributes([cols[0]])
                provider.addFeatures([fet])
        layer.commitChanges()
        layer.triggerRepaint()
        self.setCursor(Qt.ArrowCursor)
      
