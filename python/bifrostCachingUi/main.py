'''
Created on 17/12/2015

@author: dtrazzi
'''
import os

import pysideuic
import xml.etree.ElementTree as xml
from cStringIO import StringIO

import maya.cmds as cmds
import maya.OpenMayaUI as mui
import maya.mel as mel

import shiboken
from PySide import QtGui, QtCore
from PySide.QtGui import QApplication, QMainWindow, QMessageBox

uiFile = "/Users/dtrazzi/Documents/GitHub/BifrostTools/python/bifrostCachingUi/bifrostCachingUi.ui"

def wrapinstance(ptr, base=None):
  #'wrap a long pointer as a QtObject'
    if ptr is None:
        return None
    ptr = long(ptr) #Ensure type
    if globals().has_key('shiboken'):
        if base is None:
            qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
            metaObj = qObj.metaObject()
            cls = metaObj.className()
            superCls = metaObj.superClass().className()
            if hasattr(QtGui, cls):
                base = getattr(QtGui, cls)
            elif hasattr(QtGui, superCls):
                base = getattr(QtGui, superCls)
            else:
                base = QtGui.QWidget
        return shiboken.wrapInstance(long(ptr), base)
    elif globals().has_key('sip'):
        base = QtCore.QObject
        return sip.wrapinstance(long(ptr), base)
    else:
        return None

def loadUiType(uiFile):
    #'load a .ui file in memory'
    parsed = xml.parse(uiFile)
    widget_class = parsed.find('widget').get('class')
    form_class = parsed.find('class').text

    with open(uiFile, 'r') as f:
        o = StringIO()
        frame = {}

        pysideuic.compileUi(f, o, indent=0)
        pyc = compile(o.getvalue(), '<string>', 'exec')
        exec pyc in frame

        # Fetch the base_class and form class based on their type
        # in the xml from designer
        form_class = frame['Ui_%s'%form_class]
        base_class = eval('QtGui.%s'%widget_class)

    return form_class, base_class

def getMayaWindow():
    #'get the maya main window as a QMainWindow instance'
    ptr = mui.MQtUtil.mainWindow()
    return wrapinstance(long(ptr), QtGui.QMainWindow)

#load ui file
form_class, base_class = loadUiType(uiFile)
class MyWindow(form_class, base_class):
    def __init__(self, parent=getMayaWindow()):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)

        self.button_a.clicked.connect(self.addItem)
        self.button_b.clicked.connect(self.removeItem)

    def addItem(self):
        print "Clicked button A!"

    def removeItem(self):
        print "Clicked button B!"
            
def run():
    global my_window
    try:
        my_window.close()
        my_window.deleteLater()
    except: pass
    my_window = MyWindow()
    my_window.show()
    
run()