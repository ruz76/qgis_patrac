# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import os.path

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_PatracDockWidget(object):
    def setupUi(self, PatracDockWidget):
        PatracDockWidget.setObjectName(_fromUtf8("PatracDockWidget"))
        PatracDockWidget.resize(302, 182)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

        self.horizontalLayoutToolbarSearch = QtGui.QHBoxLayout()
        self.horizontalLayoutToolbarSearch.setObjectName(_fromUtf8("horizontalLayoutToolbarSearch"))

        self.msearch = QLineEdit()
        self.msearch.setMaximumWidth(280)
        self.msearch.setAlignment(Qt.AlignLeft)
        self.msearch.setPlaceholderText(u"Zadejte název obce ...")
        self.horizontalLayoutToolbarSearch.addWidget(self.msearch)

        self.tbtnZoomToMunicipality = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnZoomToMunicipality.setObjectName(_fromUtf8("tbtnZoomToMunicipality"))
        self.tbtnZoomToMunicipality.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "zoom.png")));
        self.tbtnZoomToMunicipality.setIconSize(QSize(32, 32));
        self.tbtnZoomToMunicipality.setFixedSize(QSize(42, 42));
        self.tbtnZoomToMunicipality.setToolTip(QtGui.QApplication.translate("PatracDockWidget", "Přiblížit", None,
                                                                       QtGui.QApplication.UnicodeUTF8))
        self.horizontalLayoutToolbarSearch.addWidget(self.tbtnZoomToMunicipality)

        self.tbtnCreateProject = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnCreateProject.setObjectName(_fromUtf8("tbtnCreateProject"))
        self.tbtnCreateProject.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "project.png")));
        self.tbtnCreateProject.setIconSize(QSize(32, 32));
        self.tbtnCreateProject.setFixedSize(QSize(42, 42));
        self.tbtnCreateProject.setToolTip(QtGui.QApplication.translate("PatracDockWidget", "Vytvoření projektu", None, QtGui.QApplication.UnicodeUTF8))
        self.horizontalLayoutToolbarSearch.addWidget(self.tbtnCreateProject)

        self.verticalLayout.addLayout(self.horizontalLayoutToolbarSearch)

        self.horizontalLayoutToolbar = QtGui.QHBoxLayout()
        self.horizontalLayoutToolbar.setObjectName(_fromUtf8("horizontalLayoutToolbar"))  

        self.tbtnDefinePlaces = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnDefinePlaces.setObjectName(_fromUtf8("tbtnDefinePlaces"))  
        self.tbtnDefinePlaces.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "define_places.png")));
        self.tbtnDefinePlaces.setIconSize(QSize(32,32));
        self.tbtnDefinePlaces.setFixedSize(QSize(42,42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnDefinePlaces)
        self.tbtnDefinePlaces.setToolTip(QtGui.QApplication.translate("PatracDockWidget", "Správa míst", None, QtGui.QApplication.UnicodeUTF8)) 

        self.tbtnGetSectors = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnGetSectors.setObjectName(_fromUtf8("tbtnGetSectors"))  
        self.tbtnGetSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "select_sectors.png")));
        self.tbtnGetSectors.setIconSize(QSize(32,32));
        self.tbtnGetSectors.setFixedSize(QSize(42,42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnGetSectors)
        self.tbtnGetSectors.setToolTip(QtGui.QApplication.translate("PatracDockWidget", "Vybrat sektory", None, QtGui.QApplication.UnicodeUTF8)) 

        self.tbtnRecalculateSectors = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnRecalculateSectors.setObjectName(_fromUtf8("tbtnRecalculateSectors"))  
        self.tbtnRecalculateSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "number_sectors.png")));
        self.tbtnRecalculateSectors.setIconSize(QSize(32,32));
        self.tbtnRecalculateSectors.setFixedSize(QSize(42,42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnRecalculateSectors)
        self.tbtnRecalculateSectors.setToolTip(QtGui.QApplication.translate("PatracDockWidget", "Přečíslovat sektory", None, QtGui.QApplication.UnicodeUTF8)) 

        self.tbtnExportSectors = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnExportSectors.setObjectName(_fromUtf8("tbtnExportSectors"))  
        self.tbtnExportSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "export_sectors.png")));
        self.tbtnExportSectors.setIconSize(QSize(32,32));
        self.tbtnExportSectors.setFixedSize(QSize(42,42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnExportSectors)
        self.tbtnExportSectors.setToolTip(QtGui.QApplication.translate("PatracDockWidget", "Exportovat sektory", None, QtGui.QApplication.UnicodeUTF8)) 

        self.tbtnShowSettings = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnShowSettings.setObjectName(_fromUtf8("tbtnShowSettings"))  
        self.tbtnShowSettings.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "settings.png")));
        self.tbtnShowSettings.setIconSize(QSize(32,32));
        self.tbtnShowSettings.setFixedSize(QSize(42,42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnShowSettings)
        self.tbtnShowSettings.setToolTip(QtGui.QApplication.translate("PatracDockWidget", "Nastavení", None, QtGui.QApplication.UnicodeUTF8)) 
 
        self.verticalLayout.addLayout(self.horizontalLayoutToolbar) 

        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        
        #self.horizontalLayout_6 = QtGui.QHBoxLayout()
        #self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.comboPerson = QtGui.QComboBox(self.dockWidgetContents)
        self.comboPerson.setObjectName(_fromUtf8("comboPerson"))
        self.comboPerson.addItem(_fromUtf8(u"Dítě 1-3"))
        self.comboPerson.addItem(_fromUtf8(u"Dítě 4-6"))
        self.comboPerson.addItem(_fromUtf8(u"Dítě 7-12"))
        self.comboPerson.addItem(_fromUtf8(u"Dítě 13-15"))
        self.comboPerson.addItem(_fromUtf8(u"Deprese"))
        self.comboPerson.addItem(_fromUtf8(u"Psychická nemoc"))
        self.comboPerson.addItem(_fromUtf8(u"Retardovaný"))
        self.comboPerson.addItem(_fromUtf8(u"Alzheimer"))
        self.comboPerson.addItem(_fromUtf8(u"Turista"))
        self.comboPerson.addItem(_fromUtf8(u"Demence"))
        self.horizontalLayout_4.addWidget(self.comboPerson)
        #self.verticalLayout.addLayout(self.horizontalLayout_6)
        
        self.btnGetArea = QtGui.QPushButton(self.dockWidgetContents)
        self.btnGetArea.setObjectName(_fromUtf8("btnGetArea"))
        self.horizontalLayout_4.addWidget(self.btnGetArea)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.label = QtGui.QLabel(self.dockWidgetContents)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.sliderStart = QtGui.QSlider(self.dockWidgetContents)
        self.sliderStart.setProperty("value", 0)
        self.sliderStart.setOrientation(QtCore.Qt.Horizontal)
        self.sliderStart.setTickPosition(QtGui.QSlider.TicksBelow)
        self.sliderStart.setObjectName(_fromUtf8("sliderStart"))
        self.horizontalLayout.addWidget(self.sliderStart)
        self.spinStart = QtGui.QSpinBox(self.dockWidgetContents)
        self.spinStart.setMaximum(100)
        self.spinStart.setObjectName(_fromUtf8("spinStart"))
        self.horizontalLayout.addWidget(self.spinStart)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.label_2 = QtGui.QLabel(self.dockWidgetContents)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.sliderEnd = QtGui.QSlider(self.dockWidgetContents)
        self.sliderEnd.setOrientation(QtCore.Qt.Horizontal)
        self.sliderEnd.setTickPosition(QtGui.QSlider.TicksBelow)
        self.sliderEnd.setObjectName(_fromUtf8("sliderEnd"))
        self.horizontalLayout_2.addWidget(self.sliderEnd)
        self.spinEnd = QtGui.QSpinBox(self.dockWidgetContents)
        self.spinEnd.setObjectName(_fromUtf8("spinEnd"))
        self.horizontalLayout_2.addWidget(self.spinEnd)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.chkManualUpdate = QtGui.QCheckBox(self.dockWidgetContents)
        self.chkManualUpdate.setObjectName(_fromUtf8("chkManualUpdate"))
        self.horizontalLayout_3.addWidget(self.chkManualUpdate)
        self.btnRefresh = QtGui.QPushButton(self.dockWidgetContents)
        self.btnRefresh.setObjectName(_fromUtf8("btnRefresh"))
        self.horizontalLayout_3.addWidget(self.btnRefresh)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayoutToolbar_5 = QtGui.QHBoxLayout()
        self.horizontalLayoutToolbar_5.setObjectName(_fromUtf8("horizontalLayoutToolbar_5"))

        self.tbtnImportPaths = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnImportPaths.setObjectName(_fromUtf8("tbtnImportPaths"))
        self.tbtnImportPaths.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "import_paths.png")));
        self.tbtnImportPaths.setIconSize(QSize(32, 32));
        self.tbtnImportPaths.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnImportPaths)
        self.tbtnImportPaths.setToolTip(QtGui.QApplication.translate("PatracDockWidget", "Importovat cesty z GPS", None,
                                                                     QtGui.QApplication.UnicodeUTF8))
        self.tbtnShowSearchers = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnShowSearchers.setObjectName(_fromUtf8("tbtnShowSearchers"))
        self.tbtnShowSearchers.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "show_searchers.png")));
        self.tbtnShowSearchers.setIconSize(QSize(32, 32));
        self.tbtnShowSearchers.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnShowSearchers)
        self.tbtnShowSearchers.setToolTip(
            QtGui.QApplication.translate("PatracDockWidget", "Ukázat pátrače (body)", None, QtGui.QApplication.UnicodeUTF8))

        self.tbtnShowSearchersTracks = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnShowSearchersTracks.setObjectName(_fromUtf8("tbtnShowSearchersTracks"))
        self.tbtnShowSearchersTracks.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "show_searchers_tracks.png")));
        self.tbtnShowSearchersTracks.setIconSize(QSize(32, 32));
        self.tbtnShowSearchersTracks.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnShowSearchersTracks)
        self.tbtnShowSearchersTracks.setToolTip(
            QtGui.QApplication.translate("PatracDockWidget", "Ukázat pátrače (linie)", None, QtGui.QApplication.UnicodeUTF8))

        self.tbtnShowMessage = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnShowMessage.setObjectName(_fromUtf8("tbtnShowMessage"))
        self.tbtnShowMessage.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "message.png")));
        self.tbtnShowMessage.setIconSize(QSize(32, 32));
        self.tbtnShowMessage.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnShowMessage)
        self.tbtnShowMessage.setToolTip(
            QtGui.QApplication.translate("PatracDockWidget", "Zprávy", None, QtGui.QApplication.UnicodeUTF8))


        self.tbtnInsertFinal = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnInsertFinal.setObjectName(_fromUtf8("tbtnInsertFinal"))
        self.tbtnInsertFinal.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "set_result.png")));
        self.tbtnInsertFinal.setIconSize(QSize(32, 32));
        self.tbtnInsertFinal.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnInsertFinal)
        self.tbtnInsertFinal.setToolTip(QtGui.QApplication.translate(
            "PatracDockWidget", "Nález", None, QtGui.QApplication.UnicodeUTF8))

        self.verticalLayout.addLayout(self.horizontalLayoutToolbar_5)

        PatracDockWidget.setWidget(self.dockWidgetContents)
        self.retranslateUi(PatracDockWidget)
        QtCore.QMetaObject.connectSlotsByName(PatracDockWidget)

    def retranslateUi(self, PatracDockWidget):
        PatracDockWidget.setWindowTitle(QtGui.QApplication.translate(
            "PatracDockWidget", "Pátrač", None, QtGui.QApplication.UnicodeUTF8))
        self.btnGetArea.setText(QtGui.QApplication.translate(
            "PatracDockWidget", "Určit prostor", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate(
            "PatracDockWidget", "Hodnoty min/max", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate(
            "PatracDockWidget", "Hodnoty max/min", None, QtGui.QApplication.UnicodeUTF8))
        self.chkManualUpdate.setText(QtGui.QApplication.translate(
            "PatracDockWidget", "Ruční aktualizace", None, QtGui.QApplication.UnicodeUTF8))
        self.btnRefresh.setText(QtGui.QApplication.translate(
            "PatracDockWidget", "Aktualizovat", None, QtGui.QApplication.UnicodeUTF8))
