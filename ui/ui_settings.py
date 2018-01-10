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
from PyQt4 import QtGui, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'settings.ui'))

class Ui_Settings(QtGui.QDialog, FORM_CLASS):
    def __init__(self, pluginPath, parent=None):
        """Constructor."""
        super(Ui_Settings, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        #self.init_param()
        self.setupUi(self)
        self.pluginPath = pluginPath
        self.comboBoxDistance.addItem(u"LSOM")
        self.comboBoxDistance.addItem(u"Hill")
        self.comboBoxDistance.addItem(u"UK")
        self.comboBoxDistance.addItem(u"Vlastní")
        self.comboBoxFriction.addItem(u"Pastorková")
        self.comboBoxFriction.addItem(u"Vlastní")
        self.fillTableWidgetDistance("/grass/distancesLSOM.txt", self.tableWidgetDistancesLSOM)
        self.fillTableWidgetDistance("/grass/distancesHill.txt", self.tableWidgetDistancesHill)
        self.fillTableWidgetDistance("/grass/distancesUK.txt", self.tableWidgetDistancesUK)
        self.fillTableWidgetDistance("/grass/distancesUser.txt", self.tableWidgetDistancesUser)
        self.fillTableWidgetUnits("/grass/units.txt", self.tableWidgetUnits)
        self.buttonBox.accepted.connect(self.accept)

    def fillTableWidgetUnits(self, fileName, tableWidget):
        tableWidget.setHorizontalHeaderLabels([u"Počet", u"Poznámka"])
        tableWidget.setVerticalHeaderLabels([u"Pes", u"Člověk do rojnice", u"Kůň", u"Čtyřkolka", u"Vrtulník", u"Potápěč", u"Jiné"])
        tableWidget.setColumnWidth(1, 600);
        with open(self.pluginPath + fileName, "rb") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=';'):
                j=0
                unicode_row = [x.decode('utf8') for x in row]
                #yield row.encode('utf-8')
                for field in unicode_row:
                    tableWidget.setItem(i, j, QtGui.QTableWidgetItem(field))
                    j=j+1
                i=i+1

    def fillTableWidgetDistance(self, fileName, tableWidget):
        tableWidget.setHorizontalHeaderLabels(['10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '95%'])
        tableWidget.setVerticalHeaderLabels([u"Dítě 1-3", u"Dítě 4-6", u"Dítě 7-12", u"Dítě 13-15", u"Deprese", u"Psychická nemoc", u"Retardovaný", u"Alzheimer", u"Turista", u"Demence"])
        with open(self.pluginPath + fileName, "rb") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=','):    
                j=0
                for field in row:
                    tableWidget.setItem(i, j, QtGui.QTableWidgetItem(field))                    
                    j=j+1
                i=i+1

    def accept(self):
        f = open(self.pluginPath + '/grass/distancesUser.txt', 'w')
        for i in range(0, 10):
            for j in range(0, 9):
                value = self.tableWidgetDistancesUser.item(i, j).text()
                if value == '': 
                    value = '0'
                if j == 0:
                    f.write(value)
                else:
                    f.write("," + value)
            f.write("\n")
        f.close()
        f = io.open(self.pluginPath + '/grass/units.txt', 'w', encoding='utf-8')
        for i in range(0, 7):
            for j in range(0, 2):
                value = self.tableWidgetUnits.item(i, j).text()
                if value == '':
                    value = '0'
                unicode_value = self.get_unicode(value)
                if j == 0:
                    f.write(unicode_value)
                else:
                    f.write(u";" + unicode_value)
            f.write(u"\n")
        f.close()
        if self.comboBoxDistance.currentIndex() == 0:
            shutil.copy (self.pluginPath + "/grass/distancesLSOM.txt", self.pluginPath + "/grass/distances.txt")

        if self.comboBoxDistance.currentIndex() == 1:
            shutil.copy (self.pluginPath + "/grass/distancesHill.txt", self.pluginPath + "/grass/distances.txt")

        if self.comboBoxDistance.currentIndex() == 2:
            shutil.copy (self.pluginPath + "/grass/distancesUK.txt", self.pluginPath + "/grass/distances.txt")

        if self.comboBoxDistance.currentIndex() == 3:
            shutil.copy (self.pluginPath + "/grass/distancesUser.txt", self.pluginPath + "/grass/distances.txt")


    def if_number_get_string(self, number):
        converted_str = number
        if isinstance(number, int) or \
                isinstance(number, float):
            converted_str = str(number)
        return converted_str

    def get_unicode(self, strOrUnicode, encoding='utf-8'):
        strOrUnicode = self.if_number_get_string(strOrUnicode)
        if isinstance(strOrUnicode, unicode):
            return strOrUnicode
        return unicode(strOrUnicode, encoding, errors='ignore')

    def get_string(self, strOrUnicode, encoding='utf-8'):
        strOrUnicode = self.if_number_get_string(strOrUnicode)
        if isinstance(strOrUnicode, unicode):
            return strOrUnicode.encode(encoding)
        return strOrUnicode