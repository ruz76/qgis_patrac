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
# The sliders and layer transparency are based on https://github.com/alexbruy/raster-transparency
#******************************************************************************


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from ui.ui_patracdockwidgetbase import Ui_PatracDockWidget
from ui.ui_settings import Ui_Settings
from ui.ui_gpx import Ui_Gpx
from ui.ui_message import Ui_Message
from ui.ui_coords import Ui_Coords

import os
import sys
import subprocess
from glob import glob
#from osgeo import ogr
#from osgeo import gdal
import time
import urllib2
import math
from datetime import datetime

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

        self.tbtnDefinePlaces.clicked.connect(self.definePlaces)
        self.tbtnGetSectors.clicked.connect(self.getSectors)
        self.tbtnRecalculateSectors.clicked.connect(self.recalculateSectors)
        self.tbtnExportSectors.clicked.connect(self.exportSectors)
        self.tbtnShowSettings.clicked.connect(self.showSettings)
        self.tbtnImportPaths.clicked.connect(self.showImportGpx)
        self.tbtnShowSearchers.clicked.connect(self.showPeople)
        self.tbtnShowMessage.clicked.connect(self.showMessage)

        userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/qgis_patrac"
        systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/qgis_patrac"
        if QFileInfo(userPluginPath).exists():
            self.pluginPath = userPluginPath
        else:
            self.pluginPath = systemPluginPath

        self.settingsdlg = Ui_Settings(self.pluginPath)
        center = self.plugin.canvas.center()        
        self.coordsdlg = Ui_Coords(center)        
              
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

        featuresCount = 0
        for feature in layer.getFeatures():
            featuresCount += 1

        pointid = 0
        if featuresCount > 1:
            radial = self.getRadial()
            self.generateRadialOnPoint(radial[1], layer)
            pointid = radial[1]
            self.writeAzimuthReclass(radial[0], 30, 100);
        else:
            self.generateRadialOnPoint(0, layer)
            self.writeAzimuthReclass(0, 0, 0);
                        
        #layer = self.plugin.iface.activeLayer()
        i = 0
        distances_costed_cum = ""
        for feature in layer.getFeatures():
            if i == pointid:
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
                #if (i == 0):
                    #distances_costed_cum = "distances0_costed"
                #else:
                    #distances_costed_cum = distances_costed_cum + ",distances" + str(i) + "_costed"
                distances_costed_cum = "distances" + str(i) + "_costed"
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
                QgsVectorFileWriter.writeAsVectorFormat(sector, DATAPATH + "/sektory/gpx/" + feature['label'] + ".gpx","utf-8", crs, "GPX", datasourceOptions=['GPX_USE_EXTENSIONS=YES','GPX_FORCE_TRACK=YES'])
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

    def definePlaces(self):        
        self.coordsdlg.setWidget(self)
        #self.coordsdlg.setLayer(layer)
        self.coordsdlg.setModal(True)      
        self.coordsdlg.exec_()
        x = None
        y = None 
        if self.coordsdlg.radioButtonJTSK.isChecked() == True:
            x = self.coordsdlg.lineEditX.text()
            y = self.coordsdlg.lineEditY.text()
        else:
            x = self.coordsdlg.lineEditLon.text()
            y = self.coordsdlg.lineEditLat.text()
            source_crs = QgsCoordinateReferenceSystem(4326)
            dest_crs = QgsCoordinateReferenceSystem(5514)
            transform = QgsCoordinateTransform(source_crs, dest_crs)
            xyJTSK = transform.transform(float(x), float(y))
            x = xyJTSK.x()
            y = xyJTSK.y()
        
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath() 
        layer=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        #provider = layer.dataProvider()   
        features = layer.selectedFeatures()
        #provider.getFeatures()
        layer.startEditing()
        for fet in features:
            geom = fet.geometry()
            pt = geom.asPoint()   
            print str(pt)
            fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(x),float(y))))
            layer.updateFeature(fet)
        layer.commitChanges()
        layer.triggerRepaint()

        if self.coordsdlg.checkBoxLine.isChecked() == True:
            self.convertLinesToPoints()
                
        if self.coordsdlg.checkBoxPolygon.isChecked() == True:
            self.convertPolygonsToPoints()
    
    def convertLinesToPoints(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath() 
        layerPoint=None
        layerLine=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista_linie.shp":
                layerLine = lyr
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layerPoint = lyr
        providerLine = layerLine.dataProvider()
        providerPoint = layerPoint.dataProvider()   
        #features = layer.selectedFeatures()
        features = providerLine.getFeatures()
        for fet in features:
            fetPoint = QgsFeature()
            fetPoint.setGeometry(fet.geometry().centroid())
            featureid = fet["id"] + 1000
            fetPoint.setAttributes([featureid, fet["cas_od"], fet["cas_do"]])
            providerPoint.addFeatures([fetPoint])
        layerPoint.commitChanges()
        layerPoint.triggerRepaint()

    def convertPolygonsToPoints(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath() 
        layerPoint=None
        layerPolygon=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista_polygon.shp":
                layerPolygon = lyr
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layerPoint = lyr
        providerPolygon = layerPolygon.dataProvider()
        providerPoint = layerPoint.dataProvider()   
        #features = layer.selectedFeatures()
        features = providerPolygon.getFeatures()
        for fet in features:
            fetPoint = QgsFeature()
            fetPoint.setGeometry(fet.geometry().centroid())
            featureid = fet["id"] + 2000
            fetPoint.setAttributes([featureid, fet["cas_od"], fet["cas_do"]])
            providerPoint.addFeatures([fetPoint])
        layerPoint.commitChanges()
        layerPoint.triggerRepaint()

    #Toto nefunguje
    def movePointJTSK(self, x, y):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath() 
        layer=None
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
            print str(pt)
            print str(x) + " " + str(y)	

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

    def azimuth(self, point1, point2):
        '''azimuth between 2 QGIS points ->must be adapted to 0-360°'''
        angle = math.atan2(point2.x() - point1.x(), point2.y() - point1.y())
        angle = math.degrees(angle)
        if angle < 0:
            angle = 360 + angle
        return angle   

    def avg_time(self, datetimes):
        total = sum(dt.hour * 3600 + dt.minute * 60 + dt.second for dt in datetimes)
        avg = total / len(datetimes)
        minutes, seconds = divmod(int(avg), 60)
        hours, minutes = divmod(minutes, 60)
        return datetime.combine(date(1900, 1, 1), time(hours, minutes, seconds)) 
    
    def getRadial(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath() 
        layer=None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        if layer==None:
            QMessageBox.information(None, "INFO:", u"Nebyla nalezena vrstva s místy. Nemohu určit oblast.")
            self.setCursor(Qt.ArrowCursor)
            return
        i = 0
        cas_datetime_max1 = datetime.strptime("1970-01-01 00:01", '%Y-%m-%d %H:%M')
        id_max1 = 0
        cas_datetime_max2 = datetime.strptime("1970-01-01 00:01", '%Y-%m-%d %H:%M')
        id_max2 = 0   
        from_geom = None
        to_geom = None
        for feature in layer.getFeatures():
            #TODO udělat průměr časů
            cas_od = feature["cas_od"]
            cas_od_datetime = datetime.strptime(cas_od, '%Y-%m-%d %H:%M')
            cas_do = feature["cas_do"]
            cas_do_datetime = datetime.strptime(cas_do, '%Y-%m-%d %H:%M')
            cas_datetime = self.avg_time([cas_od_datetime, cas_do_datetime])
            if cas_datetime > cas_datetime_max2:
                cas_datetime_max1 = cas_datetime_max2
                cas_datetime_max2 = cas_datetime
                id_max1 = id_max2
                id_max2 = i
                from_geom = to_geom
                geom = feature.geometry()
                to_geom = geom.asPoint()
            else:
                if cas_datetime > cas_datetime_max1:
                    cas_datetime_max1 = cas_datetime
                    id_max1 = i
                    geom = feature.geometry()
                    from_geom = geom.asPoint()
            i += 1
        azimuth = self.azimuth(from_geom, to_geom)                        
        print str(azimuth)
        print str(cas_datetime_max1) + " " + str(id_max1)
        print str(cas_datetime_max2) + " " + str(id_max2)
        cas_diff = cas_datetime_max2 - cas_datetime_max1
        cas_diff_seconds = cas_diff.total_seconds()
        print str(cas_diff_seconds)
        distance = QgsDistanceArea()
        distance_m = distance.measureLine(from_geom, to_geom)
        print str(distance_m)
        speed_m_s = distance_m / cas_diff_seconds
        print str(speed_m_s)
        return [azimuth, id_max2, speed_m_s]
        
    def getRadialAlpha(self, i, KVADRANT):
        alpha = (math.pi / float(2)) - ((math.pi / float(180)) * i)
        if KVADRANT == 2:
            alpha = ((math.pi / float(180)) * i) - (math.pi / float(2))
        if KVADRANT == 3:
            alpha = (3 * (math.pi / float(2))) - ((math.pi / float(180)) * i)
        if KVADRANT == 4:
            alpha = ((math.pi / float(180)) * i) - (3 * (math.pi / float(2)))
        return alpha
            
    def getRadialTriangleX(self, alpha, CENTERX, xdir, RADIUS):
        dx = xdir * math.cos(alpha) * RADIUS
        x = CENTERX + dx
        return x
        
    def getRadialTriangleY(self, alpha, CENTERY, ydir, RADIUS):
        dy = ydir * math.sin(alpha) * RADIUS
        y = CENTERY + dy
        return y

    def generateRadialOnPoint(self, pointid, layer):
        i = 0
        for feature in layer.getFeatures():
            if i == pointid:
                geom = feature.geometry()
                x = geom.asPoint()            
                coords = str(x)[1:-1]
                coords_splitted = coords.split(',')
                CENTERX = float(coords_splitted[0])
                CENTERY = float(coords_splitted[1])
                RADIUS = 20000;     
                csv = open(self.pluginPath + "/grass/radial.csv", "w")
                csv.write("id;wkt\n")
                self.generateRadial(CENTERX, CENTERY, RADIUS, 1, csv)
                self.generateRadial(CENTERX, CENTERY, RADIUS, 2, csv)
                self.generateRadial(CENTERX, CENTERY, RADIUS, 3, csv)
                self.generateRadial(CENTERX, CENTERY, RADIUS, 4, csv)
                csv.close() 
            i += 1

    def generateRadial(self, CENTERX, CENTERY, RADIUS, KVADRANT, csv):
        from_deg = 0
        to_deg = 90
        xdir = 1
        ydir = 1
        if KVADRANT == 2:
            from_deg = 90
            to_deg = 180
            xdir = 1
            ydir = -1
        if KVADRANT == 3:
            from_deg = 180
            to_deg = 270
            xdir = -1
            ydir = -1
        if KVADRANT == 4:
            from_deg = 270
            to_deg = 360
            xdir = -1
            ydir = 1    
        for i in xrange(from_deg, to_deg):	
            alpha = self.getRadialAlpha(i, KVADRANT);
            x = self.getRadialTriangleX(alpha, CENTERX, xdir, RADIUS)
            y = self.getRadialTriangleY(alpha, CENTERY, ydir, RADIUS)
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
            wkt_polygon = "POLYGON((" + str(CENTERX) + " " + str(CENTERY) + ", " + str(x) + " " + str(y) 	
            alpha = self.getRadialAlpha(i+1, KVADRANT);
            x = self.getRadialTriangleX(alpha, CENTERX, xdir, RADIUS)
            y = self.getRadialTriangleY(alpha, CENTERY, ydir, RADIUS)
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
        #reclass.write(str(azimuth) + " " + str(tolerance) + " " + str(friction) + "\n")
        reclass.close() 
      
