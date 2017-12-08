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

import os, sys
import subprocess
from glob import glob
import shutil
import csv
from PyQt4 import QtGui, uic

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gpx.ui'))

class Ui_Gpx(QtGui.QDialog, FORM_CLASS):
    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Gpx, self).__init__(parent)
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.fillTableWidgetSectors("/search/sectors.txt", self.tableWidgetSectors)

    def fillTableWidgetSectors(self, fileName, tableWidget):
        tableWidget.setHorizontalHeaderLabels(['ID', 'Od', 'Do'])
##        tableWidget.setVerticalHeaderLabels([u"Dítě 1-3", u"Dítě 4-6", u"Dítě 7-12", u"Dítě 13-15", u"Deprese", u"Psychická nemoc", u"Retardovaný", u"Alzheimer", u"Turista", u"Demence"])
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        with open(DATAPATH + fileName, "rb") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=','):    
                j=0
                tableWidget.insertRow(tableWidget.rowCount())
                for field in row:
                    tableWidget.setItem(i, j, QtGui.QTableWidgetItem(field))                    
                    j=j+1
                i=i+1

    def accept(self):
        QgsMessageLog.logMessage("Accept", "A")
        SECTOR = 'K1'
        DATEFROM = '2017-06-07T15:10:00Z'
        DATETO = '2017-06-07T15:12:00'
        for s in range(0, self.tableWidgetSectors.rowCount()):
            if self.tableWidgetSectors.item(s,0).isSelected():
            ##QgsMessageLog.logMessage(str(s), "Selection")
            ##QgsMessageLog.logMessage(str(self.tableWidgetSectors.item(s, 0).text()), "A")
                SECTOR = self.tableWidgetSectors.item(s, 0).text()
                DATEFROM = self.tableWidgetSectors.item(s, 1).text()
                DATETO = self.tableWidgetSectors.item(s, 2).text()
                
        value = self.tableWidgetSectors.item(0, 0).text()
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_gpx.bat", DATAPATH, self.pluginPath, SECTOR, DATEFROM, DATETO))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_gpx.sh", DATAPATH, self.pluginPath, SECTOR, DATEFROM, DATETO))
            p.wait()

        qml = open(DATAPATH + '/search/shp/style.qml', 'r').read()
        f = open(DATAPATH + '/search/shp/' + SECTOR + '.qml', 'w')
        #qml = qml.replace("k=\"line_width\" v=\"0.26\"", "k=\"line_width\" v=\"1.2\"")
        f.write(qml)
        f.close()

        vector = QgsVectorLayer(DATAPATH + '/search/shp/' + SECTOR + '.shp', SECTOR, "ogr")
        if not vector.isValid():
            print "Layer " + DATAPATH + '/search/shp/' + SECTOR + '.shp' + " failed to load!"
        else:
            QgsMapLayerRegistry.instance().addMapLayer(vector)        
