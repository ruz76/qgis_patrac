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

import os
import shutil
import csv
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QMessageBox
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import urllib2
import socket
import requests, json
import io

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'message.ui'))

class Ui_Message(QtGui.QDialog, FORM_CLASS):
    """Dialog for sending the messages
        TODO - add functionality for history
        TODO - add possibility to send message to all users
        TODO - gets searchid from settings
    """
    def __init__(self, pluginPath, DATAPATH, parent=None):
        """Constructor."""
        super(Ui_Message, self).__init__(parent)
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.DATAPATH = DATAPATH
        self.browseButton.clicked.connect(self.showBrowse)
        self.btnCheckAll.clicked.connect(self.checkAll)
        self.btnCheckNone.clicked.connect(self.checkNone)
        self.fillSearchersList()

    def fillSearchersList(self):
        self.listViewModel = QStandardItemModel()
        response = None
        # Connects to the server to obtain list of users based on list of locations
        try:
            # response = urllib2.urlopen('http://gisak.vsb.cz/patrac/mserver.php?operation=getlocations&searchid=AAA111BBB', None, 5)
            response = urllib2.urlopen(
                'http://gisak.vsb.cz/patrac/mserver.php?operation=getlocations&searchid=' + self.getSearchID(), None, 5)
            locations = response.read()
            lines = locations.split("\n")
            # Loops via locations
            for line in lines:
                if line != "":
                    cols = line.split(";")
                    if cols != None:
                        # Adds name of the user and session id to the list
                        #self.comboBoxUsers.addItem(str(cols[3]).decode('utf8') + ' (' + str(cols[0]) + ')')
                        item = QStandardItem(str(cols[3]).decode('utf8') + ' (' + str(cols[0]) + ')')
                        item.setCheckable(True)
                        self.listViewModel.appendRow(item)
            self.listViewSearchers.setModel(self.listViewModel)
        except urllib2.URLError:
            QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
            self.close()
        except e:
            QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
            self.close()
        except socket.timeout:
            QMessageBox.information(None, "INFO:", u"Nepodařilo se spojit se serverem.")
            self.close()

    def getSearchID(self):
        searchid = open(self.pluginPath + '/grass/searchid.txt', 'r').read()
        return searchid.strip()

    def showBrowse(self):
        """Opens file dialog for browsing"""
        filename1 = QFileDialog.getOpenFileName()
        self.lineEditPath.setText(filename1)

    def checkAll(self):
        i = 0
        while self.listViewModel.item(i):
            self.listViewModel.item(i).setCheckState(Qt.Checked)
            i += 1

    def checkNone(self):
        i = 0
        while self.listViewModel.item(i):
            self.listViewModel.item(i).setCheckState(Qt.Unchecked)
            i += 1

    def getSearchersIDS(self):
        i = 0
        added = 0
        ids = ""
        while self.listViewModel.item(i):
            if self.listViewModel.item(i).checkState() == Qt.Checked:
                id = self.listViewModel.item(i).text().split("(")[1][:-1]
                if added > 0:
                    ids = ids + ";" + id
                else:
                    ids = id
                added += 1
            i += 1
        return ids

    def getSearchersNames(self):
        i = 0
        added = 0
        names = ""
        while self.listViewModel.item(i):
            if self.listViewModel.item(i).checkState() == Qt.Checked:
                name = self.listViewModel.item(i).text().split("(")[0][:-1]
                if added > 0:
                    names = names + ";" + name
                else:
                    names = name
                added += 1
            i += 1
        return names

    def accept(self):
        """Sends the message"""
        #Gets the filename
        filename1 = self.lineEditPath.text()
        #Gets the sessionid from combobox
        #id = str(self.comboBoxUsers.currentText()).split("(")[1][:-1]
        ids = self.getSearchersIDS()
        QgsMessageLog.logMessage(ids, "Patrac")
        #TODO test if something is selected
        #Gets the message as plain text
        message = self.plainTextEditMessage.toPlainText()
        searchid = self.getSearchID()
        if filename1:
            if os.path.isfile(filename1):
                #If the file exists
                #with open(filename1, 'rb') as f: r = requests.post('http://gisak.vsb.cz/patrac/mserver.php', data = {'message': message, 'id': id, 'operation': 'insertmessage', 'searchid': 'AAA111BBB'}, files={'fileToUpload': f})
                with open(filename1, 'rb') as f: r = requests.post('http://gisak.vsb.cz/patrac/mserver.php',
                                                                   data={'message': message, 'ids': ids,
                                                                         'operation': 'insertmessages',
                                                                         'searchid': searchid},
                                                                   files={'fileToUpload': f})
                QgsMessageLog.logMessage("Response: " + r.text, "Patrac")
                #Adds message info to the list of sent messages
                #Should be better - possibility to read whole message
                self.listWidgetHistory.addItem(str(self.getSearchersNames()) + ": " + message[0:10] + "... " + " @ ")
                #Stores message sinto file for archiving
                with io.open(self.DATAPATH + "/pracovni/zpravy.txt", encoding='utf-8', mode="a") as messages:
                    messages.write(str(self.getSearchersNames()) + "\n" + message + "\nFile:" + filename1 + "\n--------------------\n")
        else:
            #If file is not specified then send without file
            #r = requests.post('http://gisak.vsb.cz/patrac/mserver.php', data = {'message': message, 'id': id, 'operation': 'insertmessage', 'searchid': 'AAA111BBB'})
            r = requests.post('http://gisak.vsb.cz/patrac/mserver.php',
                              data={'message': message, 'ids': ids, 'operation': 'insertmessages',
                                    'searchid': searchid})
            QgsMessageLog.logMessage("Response: " + r.text, "Patrac")
            # Adds message info to the list of sent messages
            # Should be better - possibility to read whole message
            self.listWidgetHistory.addItem(str(self.getSearchersNames()) + ": " + message[0:10] + "... ")
            # Stores message sinto file for archiving
            with io.open(self.DATAPATH + "/pracovni/zpravy.txt", encoding='utf-8', mode="a") as messages:
                messages.write(str(self.getSearchersNames()) + "\n" + message + "\n--------------------\n")
