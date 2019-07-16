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

import csv, io, math, subprocess, os, sys, uuid

from qgis.core import *
from qgis.gui import *

from datetime import datetime, timedelta
from shutil import copy
from time import gmtime, strftime
from glob import glob

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Area(object):
    def __init__(self, widget):
        self.widget = widget
        self.plugin = self.widget.plugin
        self.pluginPath = self.widget.pluginPath
        self.iface = self.widget.plugin.iface
        self.canvas = self.widget.canvas
        self.Utils = self.widget.Utils

    def getArea(self):
        """Runs main search for suitable area"""

        # Check if the project has mista.shp
        if not self.Utils.checkLayer("/pracovni/mista.shp"):
            QMessageBox.information(None, "CHYBA:",
                                    u"Projekt neobsahuje vrstvu míst. Otevřete správný projekt, nebo vygenerujte nový z projektu simple.")
            return

        # Vybrana vrstva
        # qgis.utils.iface.setActiveLayer(QgsMapLayer)
        self.widget.setCursor(Qt.WaitCursor)
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        # Removes existing loaded layer with area for search
        # This is necessary on Windows - based on lock of files
        self.Utils.removeLayer(DATAPATH + '/pracovni/distances_costed_cum.tif')

        # Tests if layer mista exists
        # TODO should be done tests for attributes as well
        layer = None
        for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
            if lyr.source() == DATAPATH + "/pracovni/mista.shp":
                layer = lyr
                break
        if layer == None:
            QMessageBox.information(None, "INFO:", u"Nebyla nalezena vrstva s místy. Nemohu určit oblast.")
            self.widget.setCursor(Qt.ArrowCursor)
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
            useAzimuth = self.Utils.getProcessRadial()
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
        self.widget.setCursor(Qt.ArrowCursor)
        return

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
        self.Utils.addRasterLayer(DATAPATH + '/pracovni/distances_costed_cum.tif', 'procenta')
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
                                  , str(self.widget.personType)))
            p.wait()
        else:
            p = subprocess.Popen(
                ('bash', self.pluginPath + "/grass/run_cost_distance.sh", DATAPATH, self.pluginPath, str(id)
                 , str(self.widget.personType)))
            p.wait()
        return

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
        weightLimit = self.Utils.getWeightLimit()
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