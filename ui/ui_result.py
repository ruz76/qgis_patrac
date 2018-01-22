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
import io
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'result.ui'))

class Ui_Result(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(Ui_Result, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        #self.init_param()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)

        self.DATAPATH = ''

        self.point = None

        date = QDate.currentDate();
        self.dateTimeEditMissing.setDate(date)

        self.comboBoxSex.addItem(_fromUtf8(u"Muž"))
        self.comboBoxSex.addItem(_fromUtf8(u"Žena"))

        self.comboBoxTerrain.addItem(_fromUtf8(u"Ano"))
        self.comboBoxTerrain.addItem(_fromUtf8(u"Ne"))
        self.comboBoxTerrain.addItem(_fromUtf8(u"Částečně"))

        self.comboBoxPurpose.addItem(_fromUtf8(u"Alzheimerova choroba"))
        self.comboBoxPurpose.addItem(_fromUtf8(u"Demence"))
        self.comboBoxPurpose.addItem(_fromUtf8(u"Deprese"))
        self.comboBoxPurpose.addItem(_fromUtf8(u"Retardovaný"))
        self.comboBoxPurpose.addItem(_fromUtf8(u"Psychická nemoc"))
        self.comboBoxPurpose.addItem(_fromUtf8(u"Sebevrah"))
        self.comboBoxPurpose.addItem(_fromUtf8(u"Dopravní nehoda(úraz, šok)"))
        self.comboBoxPurpose.addItem(_fromUtf8(u"Ǔtěk z domova"))
        self.comboBoxPurpose.addItem(_fromUtf8(u"Ztráta orientace"))
        self.comboBoxPurpose.addItem(_fromUtf8(u"Jiné (uveďte v pozn.)"))

        self.comboBoxCondition.addItem(_fromUtf8(u"Velmi dobrá"))
        self.comboBoxCondition.addItem(_fromUtf8(u"Dobrá"))
        self.comboBoxCondition.addItem(_fromUtf8(u"Špatná"))
        self.comboBoxCondition.addItem(_fromUtf8(u"Velmi špatná"))

        self.comboBoxHealth.addItem(_fromUtf8(u"Bez zdravotních obtíží"))
        self.comboBoxHealth.addItem(_fromUtf8(u"Diabetes"))
        self.comboBoxHealth.addItem(_fromUtf8(u"Epilepsie"))
        self.comboBoxHealth.addItem(_fromUtf8(u"Pohybově postižený"))
        self.comboBoxHealth.addItem(_fromUtf8(u"Vysoký krevní tlak"))
        self.comboBoxHealth.addItem(_fromUtf8(u"Jiné (uveďte v pozn.)"))

        self.comboBoxPlace.addItem(_fromUtf8(u"Vinice / chmelnice"))
        self.comboBoxPlace.addItem(_fromUtf8(u"Ovocný sad / zahrada"))
        self.comboBoxPlace.addItem(_fromUtf8(u"Louka"))
        self.comboBoxPlace.addItem(_fromUtf8(u"Pole s plodinami"))
        self.comboBoxPlace.addItem(_fromUtf8(u"Pole sklizené"))
        self.comboBoxPlace.addItem(_fromUtf8(u"Vodní plocha"))
        self.comboBoxPlace.addItem(_fromUtf8(u"Vodní tok"))
        self.comboBoxPlace.addItem(_fromUtf8(u"V obci / městě"))
        self.comboBoxPlace.addItem(_fromUtf8(u"Jiné (uveďte v pozn.)"))

        self.comboBoxPlace2.addItem(_fromUtf8(u"U stavebního objektu"))
        self.comboBoxPlace2.addItem(_fromUtf8(u"Uvnitř stavebního objektu"))
        self.comboBoxPlace2.addItem(_fromUtf8(u"U cesty (do cca 20 m)"))
        self.comboBoxPlace2.addItem(_fromUtf8(u"Na rozhraní terénů"))
        self.comboBoxPlace2.addItem(_fromUtf8(u"Houština"))
        self.comboBoxPlace2.addItem(_fromUtf8(u"Lom"))
        self.comboBoxPlace2.addItem(_fromUtf8(u"Skalní útvary"))
        self.comboBoxPlace2.addItem(_fromUtf8(u"Na cestě"))
        self.comboBoxPlace2.addItem(_fromUtf8(u"Jiné (uveďte v pozn.)"))

        self.comboBoxHealth2.addItem(_fromUtf8(u"Bez zdravotních obtíží"))
        self.comboBoxHealth2.addItem(_fromUtf8(u"Bezvědomí"))
        self.comboBoxHealth2.addItem(_fromUtf8(u"Krvácení"))
        self.comboBoxHealth2.addItem(_fromUtf8(u"Mrtvý"))
        self.comboBoxHealth2.addItem(_fromUtf8(u"Otrava"))
        self.comboBoxHealth2.addItem(_fromUtf8(u"Otřes mozku"))
        self.comboBoxHealth2.addItem(_fromUtf8(u"Podchlazení"))
        self.comboBoxHealth2.addItem(_fromUtf8(u"Fyzické vyčerpání"))
        self.comboBoxHealth2.addItem(_fromUtf8(u"Zlomeniny"))
        self.comboBoxHealth2.addItem(_fromUtf8(u"Jiné (uveďte v pozn.)"))

    def setPoint(self, point):
        self.point = point
        self.lineEditCoords.setText(str(round(self.point.x())) + ' ' + str(round(self.point.y())))

    def accept(self):
        xml = io.open(self.DATAPATH + "/search/result.xml", encoding='utf-8', mode='w')
        #html = open(self.DATAPATH + "/search/result.html", "w")
        #TODO taky htl, ale tam jsou zas ty debiliny s UTF
        xml.write(u'<?xml version="1.0"?>\n')
        xml.write(u"<result>\n")
        xml.write(u"<coords>" + self.lineEditCoords.text() + u"</coords>\n")
        xml.write(u"<datetimemissing>" + self.dateTimeEditMissing.text() + u"</datetimemissing>\n")
        xml.write(u"<hourfrommissing>" + self.spinBoxHourFromMissing.text() + u"</hourfrommissing>\n")
        xml.write(u"<sex>" + str(self.comboBoxSex.currentIndex()) + u"</sex>\n")
        xml.write(u"<!--" + self.comboBoxSex.currentText() + u"-->\n")
        xml.write(u"<age>" + self.spinBoxAge.text() + u"</age>\n")
        xml.write(u"<terrain>" + str(self.comboBoxTerrain.currentIndex()) + u"</terrain>\n")
        xml.write(u"<!--" + self.comboBoxTerrain.currentText() + u"-->\n")
        xml.write(u"<purpose>" + str(self.comboBoxPurpose.currentIndex()) + u"</purpose>\n")
        xml.write(u"<!--" + self.comboBoxPurpose.currentText() + u"-->\n")
        xml.write(u"<condition>" + str(self.comboBoxCondition.currentIndex()) + u"</condition>\n")
        xml.write(u"<!--" + self.comboBoxCondition.currentText() + u"-->\n")
        xml.write(u"<health>" + str(self.comboBoxHealth.currentIndex()) + u"</health>\n")
        xml.write(u"<!--" + self.comboBoxHealth.currentText() + u"-->\n")
        xml.write(u"<hourfromannonce>" + self.spinBoxHourFromAnnounce.text() + u"</hourfromannonce>\n")
        xml.write(u"<place>" + str(self.comboBoxPlace.currentIndex()) + u"</place>\n")
        xml.write(u"<!--" + self.comboBoxPlace.currentText() + u"-->\n")
        xml.write(u"<place2>" + str(self.comboBoxPlace2.currentIndex()) + u"</place2>\n")
        xml.write(u"<!--" + self.comboBoxPlace2.currentText() + u"-->\n")
        xml.write(u"<health2>" + str(self.comboBoxHealth2.currentIndex()) + u"</health2>\n")
        xml.write(u"<!--" + self.comboBoxHealth2.currentText() + u"-->\n")
        xml.write(u"<note>" + self.plainTextEditNote.toPlainText() + u"</note>\n")
        xml.write(u"</result>\n")
        xml.close()
        self.close()

    def setDataPath(self, DATAPATH):
        self.DATAPATH = DATAPATH


