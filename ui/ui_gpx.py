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
import fnmatch
from array import array
import getpass

#If on windows
try:
    import win32api
except:
    QgsMessageLog.logMessage(u"Linux - no win api", "Patrac")

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
        #self.path = '/media/gpx'
        self.path = '/tmp/GARMIN'
        self.DATAPATH = DATAPATH
        self.buttonBoxTime.accepted.connect(self.acceptTime)
        self.buttonBoxAll.accepted.connect(self.acceptAll)
        #Fills the table with names and times from sectors.txt
        self.fillTableWidgetSectors("/search/sectors.txt", self.tableWidgetSectors)
        self.fillListViewTracks()
        today = datetime.today()
        #Set name for output file when groupped GPX together
        #name is based on day and time
        self.lineEditName.setText(today.strftime('den%d_cas%H_%M'))

    def fillTableWidgetSectors(self, fileName, tableWidget):
        """Fills table with search sectors
           The table is used for cut of GPX according to time.
        """
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
        """Shows list of Windows drives"""
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        item, ok = QInputDialog.getItem(self, "select input dialog",
                                        "list of drives", drives, 0, False)
        if ok and item:
            return item
        else:
            return None

    def getDriveLinux(self):
        """Shows list of user drives"""
        username = getpass.getuser()
        drives = []
        for dirname in os.listdir('/media/' + username + '/'):
            drives.append('/media/' + username + '/' + dirname + '/')
        item, ok = QInputDialog.getItem(self, "select input dialog",
                                        "list of drives", drives, 0, False)
        if ok and item:
            return item
        else:
            return None

    def fillListViewTracks(self):
        """Fills list with tracks"""
        files = glob(self.DATAPATH + '/search/temp/*')
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
        #If Windows
        if sys.platform.startswith('win'):
            #Get drive from user select
            drive = self.getDrive()
            #If not selected than C:, that should be always present
            if drive is None:
                #drive = "C:/" Very dangerous feature. Reads all GPX from the C: drive. It can take a lot of time.
                #removed
                QgsMessageLog.logMessage(u"Nebyl vybrán žádný disk. Nebudu hledat data.", "Patrac")
                return
            #TODO - do it better to handle another devices than Garmin
            self.path = drive[:-1] + '/'
        # For Linux is path set just for testing purposes
        # TODO - change to have real connected devices
        else:
            drive = self.getDriveLinux()
            if drive is None:
                #drive = "C:/" Very dangerous feature. Reads all GPX from the C: drive. It can take a lot of time.
                #removed
                QgsMessageLog.logMessage(u"Nebyl vybrán žádný disk. Nebudu hledat data.", "Patrac")
                return
            self.path = drive

        #for f in glob.iglob('E:/Garmin/GPX/*/*.gpx'):  # generator, search immediate subdirectories
        i = 0
        for root, dirnames, filenames in os.walk(self.path):
            for f in fnmatch.filter(filenames, '*.gpx'):
            #for f in iglob(self.path, recursive=True):
                #copyfile(f, self.DATAPATH + '/search/gpx/' + SECTOR + '/' + os.path.basename(f))
                #First copy original file to search/gpx/ directory
                #shutil.copyfile(os.path.join(root, f.decode('utf8')), self.DATAPATH + u'/search/gpx/' + os.path.basename(f.decode('utf8')))
                #Then copy the same file to search/tem/ directory and name it according to position in list
                shutil.copyfile(os.path.join(root, f), self.DATAPATH + '/search/temp/' + str(i) + '.gpx')
                #Notice size of list.csv
                listSize = 0
                if i > 0:
                    listSize = os.path.getsize(self.DATAPATH + '/search/temp/list.csv')
                #Run transformation to get time extent of the GPX
                #Extent is added to search/temp/list.csv
                if sys.platform.startswith('win'):
                    # QgsMessageLog.logMessage(str(f), "Patrac")
                    p = subprocess.Popen((self.pluginPath + '/xslt/run_xslt_extent.bat', self.pluginPath, self.DATAPATH + '/search/temp/' + str(i) + '.gpx', self.DATAPATH + '/search/temp/list.csv'))
                    p.wait()
                else:
                    # QgsMessageLog.logMessage(str(f), "Patrac")
                    p = subprocess.Popen(('bash', self.pluginPath + '/xslt/run_xslt_extent.sh', self.pluginPath, self.DATAPATH + '/search/temp/' + str(i) + '.gpx', self.DATAPATH + '/search/temp/list.csv'))
                    p.wait()
                i=i+1
                listSizeAfterXSLT = os.path.getsize(self.DATAPATH + '/search/temp/list.csv')
                if listSize == listSizeAfterXSLT:
                    #Something bad happend with XSLT
                    #Add empty row to /search/temp/list.csv'
                    listFile = open(self.DATAPATH + '/search/temp/list.csv', 'w+')
                    listFile.write(";\n")
                    listFile.close()


        #if some GPX were found
        if os.path.isfile(self.DATAPATH + '/search/temp/list.csv'):
            self.listViewModel = QStandardItemModel()
            from_zone = tz.tzutc()
            to_zone = tz.tzlocal()
            #Loop via GPX tracks
            with open(self.DATAPATH + '/search/temp/list.csv') as fp:
                for cnt, line in enumerate(fp):
                    track = u'Track ' + str(cnt) + ' '
                    items = line.split(';')
                    start = ''
                    end = ''
                    #This is some workatound, becaouse the list can contain more than one time information for each track
                    if len(items[0]) > 30:
                        items2 = items[0].split(' ')
                        start = items2[0]
                    else:
                        start = items[0]

                    if len(items[1]) > 30:
                        items2 = items[1].split(' ')
                        end = items2[len(items2) - 1]
                    else:
                        end = items[1]

                    if len(start) > 10 and len(end) > 10:
                        #Convert to local time zone from UTC
                        start_local = self.iso_time_to_local(start)
                        end_local = self.iso_time_to_local(end)
                        track += '(' + start_local + ' <-> ' + end_local + ')'
                        item = QStandardItem(track)
                        #check = Qt.Checked if randint(0, 1) == 1 else Qt.Unchecked
                        #item.setCheckState(check)
                        item.setCheckable(True)
                        self.listViewModel.appendRow(item)
                    else:
                        item = QStandardItem("Another Type of GPX")
                        item.setCheckable(False)
                        self.listViewModel.appendRow(item)
                        #print("Line {}: {}".format(cnt, line))
            self.listViewTracks.setModel(self.listViewModel)
        else:
            QgsMessageLog.logMessage(u"Nebyl nalezen žádný záznam:", "Patrac")

    def iso_time_to_local(self, iso):
        """COnverts UTC to local time zone"""
        when = parser.parse(iso)
        local = when.astimezone(tzlocal())
        local_str = local.strftime("%Y-%m-%d %H:%M")
        return local_str

    def addToMap(self, input, SECTOR):
        """Converts track to SHP and adds it to the map
           Uses XSLT and GRASS to do it.
           TODO - do it faster to remove GRASS from process
        """
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
            QgsMessageLog.logMessage("Layer " + self.DATAPATH + '/search/shp/' + SECTOR + '.shp' + " failed to load!", "Patrac")
        else:
            if vector.featureCount() > 0:
                QgsMapLayerRegistry.instance().addMapLayer(vector)
            else:
                QMessageBox.information(None, "INFO:", u"Soubory GPX neobsahují žádné stopy.")

    def acceptAll(self):
        """Creates groupped version of GPX tracks"""
        if os.path.isfile(self.DATAPATH + '/search/temp/grouped.csv'):
            os.remove(self.DATAPATH + '/search/temp/grouped.csv')

        grouped = open(self.DATAPATH + '/search/temp/grouped.csv', 'w')

        SECTOR = self.lineEditName.text()
        if not os.path.exists(self.DATAPATH + '/search/gpx/' + SECTOR):
            os.makedirs(self.DATAPATH + '/search/gpx/' + SECTOR)

        #TODO fix move of the files with unicode names
        #for f in glob(self.DATAPATH + '/search/gpx/*.gpx'):
            #QgsMessageLog.logMessage(f.decode('utf8'), "Patrac")
            #print self.DATAPATH.decode('utf8') + u'/search/gpx/' + SECTOR.decode('utf8') + u'/' + os.path.basename(f.decode('utf8'))
            #shutil.move(f.decode('utf8'), self.DATAPATH.decode('utf8') + u'/search/gpx/' + SECTOR.decode('utf8') + u'/' + os.path.basename(f.decode('utf8')))

        i = 0
        while self.listViewModel.item(i):
            if self.listViewModel.item(i).checkState() == Qt.Checked:
                QgsMessageLog.logMessage("ID: " + str(i), "Patrac")
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
            QgsMessageLog.logMessage("GPX Check", "Patrac")
            self.addToMap(self.DATAPATH + '/search/temp/grouped.csv', SECTOR)
        else:
            i = 0
            while self.listViewModel.item(i):
                if self.listViewModel.item(i).checkState() == Qt.Checked:
                    self.addToMap(self.DATAPATH + '/search/temp/' + str(i) + '.csv', SECTOR + '_' + str(i))
                i += 1
            QgsMessageLog.logMessage("GPX NoCheck", "Patrac")
        #QgsMessageLog.logMessage("Accept", "All")

    def acceptTime(self):
        """Cuts records accroding to the times specified in tableWidgetSectors"""
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
            p = subprocess.Popen((self.pluginPath + "/grass/run_gpx.bat", self.DATAPATH, self.pluginPath, SECTOR, DATEFROM, DATETO, self.path))
            p.wait()
        else:
            p = subprocess.Popen(('bash', self.pluginPath + "/grass/run_gpx.sh", self.DATAPATH, self.pluginPath, SECTOR, DATEFROM, DATETO, self.path))
            p.wait()

        qml = open(self.DATAPATH + '/search/shp/style.qml', 'r').read()
        f = open(self.DATAPATH + '/search/shp/' + SECTOR + '.qml', 'w')
        #qml = qml.replace("k=\"line_width\" v=\"0.26\"", "k=\"line_width\" v=\"1.2\"")
        f.write(qml)
        f.close()

        vector = QgsVectorLayer(self.DATAPATH + '/search/shp/' + SECTOR + '.shp', SECTOR, "ogr")
        if not vector.isValid():
            QgsMessageLog.logMessage("Layer " + self.DATAPATH + '/search/shp/' + SECTOR + '.shp' + " failed to load!", "Patrac")
        else:
            if vector.featureCount() > 0:
                QgsMapLayerRegistry.instance().addMapLayer(vector)
            else:
                QMessageBox.information(None, "INFO:", u"V daném období nejsou žádná data.")