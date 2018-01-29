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
from glob import iglob
import shutil
from shutil import copyfile
import csv
from PyQt4 import QtGui, uic

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from random import randint
from datetime import datetime
from dateutil import tz
from dateutil import parser
from dateutil.tz import tzutc, tzlocal

try:
    import win32api
except:
    QgsMessageLog.logMessage(u"Linux - no win api", "Import GPX")

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gpx.ui'))

class Ui_Gpx(QtGui.QDialog, FORM_CLASS):
    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Gpx, self).__init__(parent)
        self.setupUi(self)
        self.pluginPath = pluginPath
        prjfi = QFileInfo(QgsProject.instance().fileName())
        DATAPATH = prjfi.absolutePath()
        self.DATAPATH = DATAPATH
        self.buttonBoxTime.accepted.connect(self.acceptTime)
        self.buttonBoxAll.accepted.connect(self.acceptAll)
        self.fillTableWidgetSectors("/search/sectors.txt", self.tableWidgetSectors)
        self.fillListViewTracks()
        today = datetime.today()
        self.lineEditName.setText(today.strftime('den%d_cas%H_%M'))

    def fillTableWidgetSectors(self, fileName, tableWidget):
        tableWidget.setHorizontalHeaderLabels(['ID', 'Od', 'Do'])
        with open(self.DATAPATH + fileName, "rb") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=','):    
                j=0
                tableWidget.insertRow(tableWidget.rowCount())
                for field in row:
                    tableWidget.setItem(i, j, QtGui.QTableWidgetItem(field))                    
                    j=j+1
                i=i+1
        #tableWidget.rowCount = 3

    def getDrive(self):
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        items = ("D:", "E:", "F:", "G:", "H:", "I:")
        item, ok = QInputDialog.getItem(self, "select input dialog",
                                        "list of languages", drives, 0, False)
        if ok and item:
            return item
        else:
            return None


    def fillListViewTracks(self):
        if os.path.isfile(self.DATAPATH + '/search/temp/list.csv'):
            os.remove(self.DATAPATH + '/search/temp/list.csv')
        path = '/media/gpx/Garmin/GPX/*/*.gpx'
        if sys.platform.startswith('win'):
            drive = self.getDrive()
            if drive is None:
                drive = "C:/"
                QgsMessageLog.logMessage(u"Nebyl vybrán žádný disk, vybírám C:", "Import GPX")
            path = drive[:-1] + '/Garmin/GPX/*/*.gpx'
        #for f in glob.iglob('E:/Garmin/GPX/*/*.gpx'):  # generator, search immediate subdirectories
        i = 0
        for f in iglob(path):
            #copyfile(f, self.DATAPATH + '/search/gpx/' + SECTOR + '/' + os.path.basename(f))
            shutil.copyfile(f, self.DATAPATH + '/search/gpx/' + os.path.basename(f))
            shutil.copyfile(f, self.DATAPATH + '/search/temp/' + str(i) + '.gpx')
            if sys.platform.startswith('win'):
                p = subprocess.Popen((self.pluginPath + '/xslt/run_xslt_extent.bat', self.pluginPath, self.DATAPATH + '/search/temp/' + str(i) + '.gpx', self.DATAPATH + '/search/temp/list.csv'))
                p.wait()
            else:
                QgsMessageLog.logMessage(str(f), "XSLT")
                p = subprocess.Popen(('bash', self.pluginPath + '/xslt/run_xslt_extent.sh', self.pluginPath, self.DATAPATH + '/search/temp/' + str(i) + '.gpx', self.DATAPATH + '/search/temp/list.csv'))
                p.wait()
            i=i+1

        if os.path.isfile(self.DATAPATH + '/search/temp/list.csv'):
            self.listViewModel = QStandardItemModel()
            from_zone = tz.tzutc()
            to_zone = tz.tzlocal()
            with open(self.DATAPATH + '/search/temp/list.csv') as fp:
                for cnt, line in enumerate(fp):
                    track = u'Track ' + str(cnt) + ' '
                    items = line.split(';')
                    start = ''
                    end = ''
                    if len(items[0]) > 30:
                        items2 = items[0].split(' ')
                        #track+= "L " + str(local) + "U: " + items2[0]
                        start = items2[0]
                        items2 = items[1].split(' ')
                        end = items2[0]
                        #track += u' Konec: ' + items2[0]
                    else:
                        start = items[0]
                        end = items[1]
                    start_local = self.iso_time_to_local(start)
                    end_local = self.iso_time_to_local(end)
                    track += '(' + start_local + ' <-> ' + end_local + ')'
                    item = QStandardItem(track)
                    #check = Qt.Checked if randint(0, 1) == 1 else Qt.Unchecked
                    #item.setCheckState(check)
                    item.setCheckable(True)
                    self.listViewModel.appendRow(item)
                    #print("Line {}: {}".format(cnt, line))
            self.listViewTracks.setModel(self.listViewModel)
        else:
            QgsMessageLog.logMessage(u"Nebyl nalezen žádný záznam:", "Import GPX")

    def iso_time_to_local(self, iso):
        when = parser.parse(iso)
        local = when.astimezone(tzlocal())
        local_str = local.strftime("%Y-%m-%d %H:%M")
        return local_str

    def addToMap(self, input, SECTOR):
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_gpx_no_time.bat", self.DATAPATH, self.pluginPath, input, SECTOR))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_gpx_no_time.sh", self.DATAPATH, self.pluginPath, input, SECTOR))
            p.wait()

        qml = open(self.DATAPATH + '/search/shp/style.qml', 'r').read()
        f = open(self.DATAPATH + '/search/shp/' + SECTOR + '.qml', 'w')
        #qml = qml.replace("k=\"line_width\" v=\"0.26\"", "k=\"line_width\" v=\"1.2\"")
        f.write(qml)
        f.close()

        vector = QgsVectorLayer(self.DATAPATH + '/search/shp/' + SECTOR + '.shp', SECTOR, "ogr")
        if not vector.isValid():
            print "Layer " + self.DATAPATH + '/search/shp/' + SECTOR + '.shp' + " failed to load!"
        else:
            QgsMapLayerRegistry.instance().addMapLayer(vector)

    def acceptAll(self):
        if os.path.isfile(self.DATAPATH + '/search/temp/grouped.csv'):
            os.remove(self.DATAPATH + '/search/temp/grouped.csv')

        grouped = open(self.DATAPATH + '/search/temp/grouped.csv', 'w')

        SECTOR = self.lineEditName.text()
        if not os.path.exists(self.DATAPATH + '/search/gpx/' + SECTOR):
            os.makedirs(self.DATAPATH + '/search/gpx/' + SECTOR)
        i = 0
        while self.listViewModel.item(i):
            if self.listViewModel.item(i).checkState() == Qt.Checked:
                QgsMessageLog.logMessage("ID: " + str(i), "GPX")
                if sys.platform.startswith('win'):
                    p = subprocess.Popen((self.pluginPath + "/xslt/run_xslt_no_time.bat", self.pluginPath, self.DATAPATH + '/search/temp/' + str(i) + '.gpx', self.DATAPATH + '/search/temp/' + str(i) + '.csv'))
                    p.wait()
                else:
                    p = subprocess.Popen(('bash', self.pluginPath + "/xslt/run_xslt_no_time.sh", self.pluginPath, self.DATAPATH + '/search/temp/' + str(i) + '.gpx', self.DATAPATH + '/search/temp/' + str(i) + '.csv'))
                    p.wait()
                SECTOR_content = open(self.DATAPATH + '/search/temp/' + str(i) + '.csv', 'r').read()
                grouped.write(SECTOR_content)
            i += 1
        grouped.close()

        if self.checkBoxGroup.isChecked() == True:
            QgsMessageLog.logMessage("Check", "GPX")
            self.addToMap(self.DATAPATH + '/search/temp/grouped.csv', SECTOR)
        else:
            i = 0
            while self.listViewModel.item(i):
                if self.listViewModel.item(i).checkState() == Qt.Checked:
                    self.addToMap(self.DATAPATH + '/search/temp/' + str(i) + '.csv', SECTOR + '_' + str(i))
                i += 1
            QgsMessageLog.logMessage("NoCheck", "GPX")
        #QgsMessageLog.logMessage("Accept", "All")

    def acceptTime(self):
        #QgsMessageLog.logMessage("Accept", "A")
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
        
        if sys.platform.startswith('win'):
            p = subprocess.Popen((self.pluginPath + "/grass/run_gpx.bat", self.DATAPATH, self.pluginPath, SECTOR, DATEFROM, DATETO))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_gpx.sh", self.DATAPATH, self.pluginPath, SECTOR, DATEFROM, DATETO))
            p.wait()

        qml = open(self.DATAPATH + '/search/shp/style.qml', 'r').read()
        f = open(self.DATAPATH + '/search/shp/' + SECTOR + '.qml', 'w')
        #qml = qml.replace("k=\"line_width\" v=\"0.26\"", "k=\"line_width\" v=\"1.2\"")
        f.write(qml)
        f.close()

        vector = QgsVectorLayer(self.DATAPATH + '/search/shp/' + SECTOR + '.shp', SECTOR, "ogr")
        if not vector.isValid():
            print "Layer " + self.DATAPATH + '/search/shp/' + SECTOR + '.shp' + " failed to load!"
        else:
            QgsMapLayerRegistry.instance().addMapLayer(vector)        
