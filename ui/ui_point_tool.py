from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from ui_result import Ui_Result

class PointMapTool(QgsMapTool):
  def __init__(self, canvas):
      self.canvas = canvas
      QgsMapTool.__init__(self, self.canvas)
      self.reset()
      self.dialog = Ui_Result()
      self.DATAPATH = ''

  def reset(self):
      self.point = None

  def setDataPath(self, DATAPATH):
      self.DATAPATH = DATAPATH

  def canvasPressEvent(self, e):
      self.point = self.toMapCoordinates(e.pos())

  def canvasReleaseEvent(self, e):
      if self.point is not None:
          print "Point: ", self.point.x()
          self.dialog.setPoint(self.point)
          self.dialog.setDataPath(self.DATAPATH)
          self.dialog.show()

  #def deactivate(self):
  #    super(PointMapTool, self).deactivate()
  #    self.emit(SIGNAL("deactivated()"))