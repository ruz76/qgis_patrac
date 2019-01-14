# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import os.path
import csv

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_PatracDockWidget(object):
    def setupUi(self, PatracDockWidget):
        PatracDockWidget.setObjectName(_fromUtf8("PatracDockWidget"))
        PatracDockWidget.resize(302, 182)

        self.pluginPath = PatracDockWidget.pluginPath

        # for i in inspect.getmembers(PatracDockWidget):
        #     # Ignores anything starting with underscore
        #     # (that is, private and protected attributes)
        #     if not i[0].startswith('_'):
        #         # Ignores methods
        #         if not inspect.ismethod(i[1]):
        #             print(i)

        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))

        self.tabLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.tabLayout.setObjectName(_fromUtf8("tabLayout"))

        self.tabWidget = QtGui.QTabWidget()
        self.tabGuide = QtGui.QWidget()
        self.tabWidget.addTab(self.tabGuide, QtGui.QApplication.translate("tabGuide", "Průvodce", None, QtGui.QApplication.UnicodeUTF8))

        self.tabExpert = QtGui.QWidget()
        self.tabWidget.addTab(self.tabExpert, "Expert")

        self.verticalLayout = QtGui.QVBoxLayout(self.tabExpert)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabExpert.setLayout(self.verticalLayout)

        self.tabHelp = QtGui.QWidget()
        self.tabWidget.addTab(self.tabHelp, u"Nápověda")
        self.setHelpTab()

        self.verticalGuideLayout = QtGui.QVBoxLayout(self.tabGuide)
        self.verticalGuideLayout.setObjectName(_fromUtf8("verticalGuideLayout"))
        self.tabGuide.setLayout(self.verticalGuideLayout)

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

        self.tbtnReportExportSectors = QtGui.QPushButton(self.dockWidgetContents)
        self.tbtnReportExportSectors.setObjectName(_fromUtf8("tbtnReportExportSectors"))
        self.tbtnReportExportSectors.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "report_export_sectors.png")));
        self.tbtnReportExportSectors.setIconSize(QSize(32, 32));
        self.tbtnReportExportSectors.setFixedSize(QSize(42, 42));
        self.horizontalLayoutToolbar.addWidget(self.tbtnReportExportSectors)
        self.tbtnReportExportSectors.setToolTip(QtGui.QApplication.translate("PatracDockWidget", "Vytvořit report", None,
                                                                       QtGui.QApplication.UnicodeUTF8))

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
        self.tbtnInsertFinal.setToolTip(QtGui.QApplication.translate(
            "PatracDockWidget", "Zadat výsledek", None, QtGui.QApplication.UnicodeUTF8))
        self.horizontalLayoutToolbar_5.addWidget(self.tbtnInsertFinal)

        self.verticalLayout.addLayout(self.horizontalLayoutToolbar_5)

        self.setGuideSteps()

        self.tabLayout.addWidget(self.tabWidget)

        PatracDockWidget.setWidget(self.dockWidgetContents)
        self.retranslateUi(PatracDockWidget)
        QtCore.QMetaObject.connectSlotsByName(PatracDockWidget)

    def setHelpTab(self):
        self.verticalHelpLayout = QtGui.QVBoxLayout(self.tabHelp)
        self.verticalHelpLayout.setObjectName(_fromUtf8("verticalHelpLayout"))
        self.helpShow = QtGui.QPushButton(self.dockWidgetContents)
        self.helpShow.setObjectName(_fromUtf8("helpShow"))
        self.helpShow.setText(u"Zobrazit nápovědu")
        self.verticalHelpLayout.addWidget(self.helpShow)
        self.tabHelp.setLayout(self.verticalHelpLayout)

    def setGuideSteps(self):
        self.tabGuideSteps = QtGui.QTabWidget()
        self.tabGuideStep1 = QtGui.QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep1, "1")
        self.setGuideLayoutStep1()
        self.tabGuideStep2 = QtGui.QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep2, "2")
        self.setGuideLayoutStep2()
        self.tabGuideStep3 = QtGui.QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep3, "3")
        self.setGuideLayoutStep3()
        self.tabGuideStep4 = QtGui.QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep4, "4")
        self.setGuideLayoutStep4()
        self.tabGuideStep5 = QtGui.QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep5, "5")
        self.setGuideLayoutStep5()
        self.tabGuideStep6 = QtGui.QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep6, "6")
        self.setGuideLayoutStep6()
        self.tabGuideStep7 = QtGui.QWidget()
        self.tabGuideSteps.addTab(self.tabGuideStep7, "7")
        self.setGuideLayoutStep7()
        self.verticalGuideLayout.addWidget(self.tabGuideSteps)
        self.tabGuideSteps.setCurrentIndex(0)

    def setGuideLayoutStep1(self):
        self.verticalGuideLayoutStep1 = QtGui.QVBoxLayout(self.tabGuideStep1)
        self.verticalGuideLayoutStep1.setObjectName(_fromUtf8("verticalGuideLayoutStep1"))
        self.guideLabelStep1 = QtGui.QLabel(self.dockWidgetContents)
        self.guideLabelStep1.setObjectName(_fromUtf8("guideLabelStep1"))
        self.guideLabelStep1.setText(u"Zadejte název obce")
        self.guideLabelStep1.setWordWrap(True)
        self.verticalGuideLayoutStep1.addWidget(self.guideLabelStep1)
        self.guideMunicipalitySearch = QLineEdit()
        self.guideMunicipalitySearch.setMaximumWidth(280)
        self.guideMunicipalitySearch.setAlignment(Qt.AlignLeft)
        self.guideMunicipalitySearch.setPlaceholderText(u"Zadejte název obce ...")
        self.verticalGuideLayoutStep1.addWidget(self.guideMunicipalitySearch)
        self.guideStep1Next = QtGui.QPushButton(self.dockWidgetContents)
        self.guideStep1Next.setObjectName(_fromUtf8("guideStep1Next"))
        self.guideStep1Next.setText(u"Další")
        self.verticalGuideLayoutStep1.addWidget(self.guideStep1Next)
        self.tabGuideStep1.setLayout(self.verticalGuideLayoutStep1)

    def setGuideLayoutStep2(self):
        self.verticalGuideLayoutStep2 = QtGui.QVBoxLayout(self.tabGuideStep2)
        self.verticalGuideLayoutStep2.setObjectName(_fromUtf8("verticalGuideLayoutStep2"))
        self.guideLabelStep2 = QtGui.QLabel(self.dockWidgetContents)
        self.guideLabelStep2.setObjectName(_fromUtf8("guideLabelStep2"))
        self.guideLabelStep2.setText(u"Zkontrolujte zda se mapa přiblížila na vybranou obec. "
                                     u"Následně dojde k vygenerování projektu. Generování může trvat i několik minut.")
        self.guideLabelStep2.setWordWrap(True)
        self.verticalGuideLayoutStep2.addWidget(self.guideLabelStep2)
        self.guideStep2Next = QtGui.QPushButton(self.dockWidgetContents)
        self.guideStep2Next.setObjectName(_fromUtf8("guideStep2Next"))
        self.guideStep2Next.setText(u"Další")
        self.verticalGuideLayoutStep2.addWidget(self.guideStep2Next)
        self.tabGuideStep2.setLayout(self.verticalGuideLayoutStep2)

    def setGuideLayoutStep3(self):
        self.verticalGuideLayoutStep3 = QtGui.QVBoxLayout(self.tabGuideStep3)
        self.verticalGuideLayoutStep3.setObjectName(_fromUtf8("verticalGuideLayoutStep3"))
        self.guideLabelStep3 = QtGui.QLabel(self.dockWidgetContents)
        self.guideLabelStep3.setObjectName(_fromUtf8("guideLabelStep3"))
        self.guideLabelStep3.setText(u"Klikněte do mapy, kde máte hlášení o spatření osoby. Kliknout můžete vícekrát."
                                     u"Mapu si můžete přiblížit, ale následně je nutné se přepnout zpět na aktuálně aktivní ikonu.")
        self.guideLabelStep3.setWordWrap(True)
        self.verticalGuideLayoutStep3.addWidget(self.guideLabelStep3)
        self.guideStep3Next = QtGui.QPushButton(self.dockWidgetContents)
        self.guideStep3Next.setObjectName(_fromUtf8("guideStep3Next"))
        self.guideStep3Next.setText(u"Další")
        self.verticalGuideLayoutStep3.addWidget(self.guideStep3Next)
        self.tabGuideStep3.setLayout(self.verticalGuideLayoutStep3)

    def setGuideLayoutStep4(self):
        self.verticalGuideLayoutStep4 = QtGui.QVBoxLayout(self.tabGuideStep4)
        self.verticalGuideLayoutStep4.setObjectName(_fromUtf8("verticalGuideLayoutStep4"))
        self.guideLabelStep4 = QtGui.QLabel(self.dockWidgetContents)
        self.guideLabelStep4.setObjectName(_fromUtf8("guideLabelStep4"))
        self.guideLabelStep4.setText(u"Vyberte typ pohřešované osoby. Následně dojde k určení pravděpodobnosti výskytu. Výpočet může trvat i několik minut.")
        self.guideLabelStep4.setWordWrap(True)
        self.verticalGuideLayoutStep4.addWidget(self.guideLabelStep4)
        self.guideComboPerson = QtGui.QComboBox(self.dockWidgetContents)
        self.guideComboPerson.setObjectName(_fromUtf8("guideComboPerson"))
        self.guideComboPerson.addItem(_fromUtf8(u"Dítě 1-3"))
        self.guideComboPerson.addItem(_fromUtf8(u"Dítě 4-6"))
        self.guideComboPerson.addItem(_fromUtf8(u"Dítě 7-12"))
        self.guideComboPerson.addItem(_fromUtf8(u"Dítě 13-15"))
        self.guideComboPerson.addItem(_fromUtf8(u"Deprese"))
        self.guideComboPerson.addItem(_fromUtf8(u"Psychická nemoc"))
        self.guideComboPerson.addItem(_fromUtf8(u"Retardovaný"))
        self.guideComboPerson.addItem(_fromUtf8(u"Alzheimer"))
        self.guideComboPerson.addItem(_fromUtf8(u"Turista"))
        self.guideComboPerson.addItem(_fromUtf8(u"Demence"))
        self.verticalGuideLayoutStep4.addWidget(self.guideComboPerson)
        self.guideStep4Next = QtGui.QPushButton(self.dockWidgetContents)
        self.guideStep4Next.setObjectName(_fromUtf8("guideStep4Next"))
        self.guideStep4Next.setText(u"Další")
        self.verticalGuideLayoutStep4.addWidget(self.guideStep4Next)
        self.tabGuideStep4.setLayout(self.verticalGuideLayoutStep4)

    def setGuideLayoutStep5(self):
        self.verticalGuideLayoutStep5 = QtGui.QVBoxLayout(self.tabGuideStep5)
        self.verticalGuideLayoutStep5.setObjectName(_fromUtf8("verticalGuideLayoutStep5"))
        self.guideLabelStep5 = QtGui.QLabel(self.dockWidgetContents)
        self.guideLabelStep5.setObjectName(_fromUtf8("guideLabelStep5"))
        self.guideLabelStep5.setText(u"Procento případů jsem nastavil na 70%. Procento můžete změnit. "
                                     u"Zvýšení procenta však vede k delší době výpočtu a výběru větší oblasti, než je obvykle možné propátrat v rozumné době.")
        self.guideLabelStep5.setWordWrap(True)
        self.verticalGuideLayoutStep5.addWidget(self.guideLabelStep5)
        self.guideSpinEnd = QtGui.QSpinBox(self.dockWidgetContents)
        self.guideSpinEnd.setMaximum(100)
        self.guideSpinEnd.setObjectName(_fromUtf8("guideSpinEnd"))
        self.guideSpinEnd.setValue(70)
        self.verticalGuideLayoutStep5.addWidget(self.guideSpinEnd)
        self.guideStep5Next = QtGui.QPushButton(self.dockWidgetContents)
        self.guideStep5Next.setObjectName(_fromUtf8("guideStep5Next"))
        self.guideStep5Next.setText(u"Další")
        self.verticalGuideLayoutStep5.addWidget(self.guideStep5Next)
        self.tabGuideStep5.setLayout(self.verticalGuideLayoutStep5)

    def setGuideLayoutStep6(self):
        self.verticalGuideLayoutStep6 = QtGui.QVBoxLayout(self.tabGuideStep6)
        self.verticalGuideLayoutStep6.setObjectName(_fromUtf8("verticalGuideLayoutStep6"))
        self.guideLabelStep6 = QtGui.QLabel(self.dockWidgetContents)
        self.guideLabelStep6.setObjectName(_fromUtf8("guideLabelStep6"))
        self.guideLabelStep6.setText(u"Zde můžete upravit počty prostředků")
        self.guideLabelStep6.setWordWrap(True)
        self.verticalGuideLayoutStep6.addWidget(self.guideLabelStep6)
        self.loadAvailableUnits()
        self.guideStep6Next = QtGui.QPushButton(self.dockWidgetContents)
        self.guideStep6Next.setObjectName(_fromUtf8("guideStep6Next"))
        self.guideStep6Next.setText(u"Další")
        self.verticalGuideLayoutStep6.addWidget(self.guideStep6Next)
        self.tabGuideStep6.setLayout(self.verticalGuideLayoutStep6)

    def setGuideLayoutStep7(self):
        self.verticalGuideLayoutStep7 = QtGui.QVBoxLayout(self.tabGuideStep7)
        self.verticalGuideLayoutStep7.setObjectName(_fromUtf8("verticalGuideLayoutStep7"))
        self.guideLabelStep7 = QtGui.QLabel(self.dockWidgetContents)
        self.guideLabelStep7.setObjectName(_fromUtf8("guideLabelStep7"))
        self.guideLabelStep7.setText(u"Téměř dokončeno. Report obsahuje odkazy na PDF pro tisk a GPX pro GPS přijímače. PDF zatím nebyly vygenerovány. Generování PDF může trvat poměrně dlouho (řádově minuty). \nNezapomeňte zadat výsledek pátrání.")
        self.guideLabelStep7.setWordWrap(True)
        self.verticalGuideLayoutStep7.addWidget(self.guideLabelStep7)
        self.chkGenerateOverallPDF = QtGui.QCheckBox(self.dockWidgetContents)
        self.chkGenerateOverallPDF.setText(u"Vygenerovat souhrnné PDF pro tisk")
        self.verticalGuideLayoutStep7.addWidget(self.chkGenerateOverallPDF)
        #self.chkGeneratePDF = QtGui.QCheckBox(self.dockWidgetContents)
        #self.chkGeneratePDF.setText(u"Vygenerovat PDF pro tisk")
        #self.verticalGuideLayoutStep7.addWidget(self.chkGeneratePDF)
        self.guideShowReport = QtGui.QPushButton(self.dockWidgetContents)
        self.guideShowReport.setObjectName(_fromUtf8("guideInsertFinal"))
        self.guideShowReport.setText(u"Zobrazit report")
        self.verticalGuideLayoutStep7.addWidget(self.guideShowReport)

        self.horizontalLayoutToolbarGuide7 = QtGui.QHBoxLayout()
        self.horizontalLayoutToolbarGuide7.setObjectName(_fromUtf8("horizontalLayoutToolbarGuide7"))

        self.guideInsertFinal = QtGui.QPushButton(self.dockWidgetContents)
        self.guideInsertFinal.setObjectName(_fromUtf8("guideInsertFinal"))
        self.guideInsertFinal.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "set_result.png")));
        self.guideInsertFinal.setIconSize(QSize(32, 32));
        self.guideInsertFinal.setFixedSize(QSize(42, 42));
        self.guideInsertFinal.setToolTip(QtGui.QApplication.translate(
            "PatracDockWidget", "Zadat výsledek", None, QtGui.QApplication.UnicodeUTF8))
        self.horizontalLayoutToolbarGuide7.addWidget(self.guideInsertFinal)

        self.guideShowSettings = QtGui.QPushButton(self.dockWidgetContents)
        self.guideShowSettings.setObjectName(_fromUtf8("guideShowSettings"))
        self.guideShowSettings.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "settings.png")));
        self.guideShowSettings.setIconSize(QSize(32, 32));
        self.guideShowSettings.setFixedSize(QSize(42, 42));
        self.guideShowSettings.setToolTip(
            QtGui.QApplication.translate("PatracDockWidget", "Nastavení", None, QtGui.QApplication.UnicodeUTF8))
        self.horizontalLayoutToolbarGuide7.addWidget(self.guideShowSettings)

        self.verticalGuideLayoutStep7.addLayout(self.horizontalLayoutToolbarGuide7)
        self.tabGuideStep7.setLayout(self.verticalGuideLayoutStep7)

    def loadAvailableUnits(self):
        with open(self.pluginPath + "/grass/units.txt", "rb") as fileInput:
            i=0
            for row in csv.reader(fileInput, delimiter=';'):
                unicode_row = [x.decode('utf8') for x in row]
                # dog
                if i == 0:
                    self.guideDogCountLabel = QtGui.QLabel(self.dockWidgetContents)
                    self.guideDogCountLabel.setText(u"Pes")
                    self.guideDogCount = QLineEdit()
                    self.guideDogCount.setText(unicode_row[0])
                    self.horizontalDogCountLayout = QtGui.QHBoxLayout(self.tabGuideStep6)
                    self.horizontalDogCountLayout.addWidget(self.guideDogCountLabel)
                    self.horizontalDogCountLayout.addWidget(self.guideDogCount)
                    self.verticalGuideLayoutStep6.addLayout(self.horizontalDogCountLayout)
                # person
                if i == 1:
                    self.guidePersonCountLabel = QtGui.QLabel(self.dockWidgetContents)
                    self.guidePersonCountLabel.setText(u"Člověk do rojnice")
                    self.guidePersonCount = QLineEdit()
                    self.guidePersonCount.setText(unicode_row[0])
                    self.horizontalPersonCountLayout = QtGui.QHBoxLayout(self.tabGuideStep6)
                    self.horizontalPersonCountLayout.addWidget(self.guidePersonCountLabel)
                    self.horizontalPersonCountLayout.addWidget(self.guidePersonCount)
                    self.verticalGuideLayoutStep6.addLayout(self.horizontalPersonCountLayout)
                # diver
                if i == 5:
                    self.guideDiverCountLabel = QtGui.QLabel(self.dockWidgetContents)
                    self.guideDiverCountLabel.setText(u"Potápěč")
                    self.guideDiverCount = QLineEdit()
                    self.guideDiverCount.setText(unicode_row[0])
                    self.horizontalDiverCountLayout = QtGui.QHBoxLayout(self.tabGuideStep6)
                    self.horizontalDiverCountLayout.addWidget(self.guideDiverCountLabel)
                    self.horizontalDiverCountLayout.addWidget(self.guideDiverCount)
                    self.verticalGuideLayoutStep6.addLayout(self.horizontalDiverCountLayout)
                i=i+1

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
