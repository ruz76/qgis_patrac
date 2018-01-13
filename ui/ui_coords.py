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
from qgis.core import *
from qgis.gui import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'coords.ui'))

class Ui_Coords(QtGui.QDialog, FORM_CLASS):
    def __init__(self, center, parent=None):
        """Constructor."""
        super(Ui_Coords, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        #self.init_param()
        self.setupUi(self)
        self.layer = None
        self.center = center
        self.widget = None
        self.lineEditX.setText(str(center.x()))
        self.lineEditY.setText(str(center.y()))
        source_crs = QgsCoordinateReferenceSystem(5514)
        dest_crs = QgsCoordinateReferenceSystem(4326)
        transform = QgsCoordinateTransform(source_crs, dest_crs)
        xyWGS = transform.transform(center.x(), center.y())
        self.lineEditLon.setText(str(xyWGS.x()))
        self.lineEditLat.setText(str(xyWGS.y()))
        self.buttonBox.accepted.connect(self.accept)

    def setLayer(self, layer):
        self.layer = layer

    def setWidget(self, widget):
        self.widget = widget
    
    def setCenter(self, center):
        self.center = center

    #Toto taky nefungovalo, takže jinak, stále to ale nechápu
    def accept(self):
        #self.widget.movePointJTSK(float(self.lineEditX.text()),float(self.lineEditY.text()))
        self.close()

    def acceptNefuncki(self):
        #vraci  objektu misto jednoho a nedela editaci - nechapu, asi nejaka dvojita reference
        provider = self.layer.dataProvider()   
        features = provider.getFeatures()
        self.layer.startEditing()
        for fet in features:
            print self.lineEditX.text() + " " + self.lineEditY.text()
            geom = fet.geometry()
            pt = geom.asPoint()   
            print str(pt)
            fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(self.lineEditX.text()),float(self.lineEditY.text()))))
            self.layer.commitChanges()
        self.layer.triggerRepaint()
