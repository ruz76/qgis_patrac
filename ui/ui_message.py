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
import urllib2
import requests, json

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'message.ui'))

class Ui_Message(QtGui.QDialog, FORM_CLASS):
    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Message, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        #self.init_param()
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.browseButton.clicked.connect(self.showBrowse)
        response = urllib2.urlopen('http://158.196.143.122/patrac/mserver.php?operation=getlocations')
        locations = response.read()
        lines = locations.split("\n")
        for line in lines:
            if line != "":
                cols = line.split(";")
	        self.comboBoxUsers.addItem(cols[0] + " (" + cols[1] + ")")
    
    def showBrowse(self):
        filename1 = QFileDialog.getOpenFileName()
        self.lineEditPath.setText(filename1)

    def accept(self):
        filename1 = self.lineEditPath.text()
        idx = str(self.comboBoxUsers.currentText())
        cols = idx.split("(")
        id = cols[1].split(")")[0] 
        message = self.plainTextEditMessage.toPlainText()
        #data = json.dumps({'message': message, 'id': id, 'operation': 'insertmessage'})
        if (filename1 != ""):
            with open(filename1, 'rb') as f: r = requests.post('http://158.196.143.122/patrac/mserver.php', data = {'message': message, 'id': id, 'operation': 'insertmessage'}, files={'fileToUpload': f})
        else:
            r = requests.post('http://158.196.143.122/patrac/mserver.php', data = {'message': message, 'id': id, 'operation': 'insertmessage'})
        print r.text

