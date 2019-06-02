# -*- coding: utf-8 -*-
'''
This application are used for viewing ARPES data.
By Wei Yao
'''

import sys, multiprocessing
import mp_package
from PyQt5.QtWidgets import QApplication, QStyleFactory
from mainwindow import MainWindow
import numpy as np


class App(QApplication):
    '''
    MainApp class
    '''
    def __init__(self, argv):
        super(App, self).__init__(argv)
        #print(argv)
        self.MainWindow = MainWindow(self)


if __name__ == '__main__':
    multiprocessing.freeze_support() # to avoid opening mainwindow when using the feature of multiprocessing
    App = App(sys.argv)  #.instance()
    #App.setStyle(QStyleFactory.create('Fusion'))
    sys.exit(App.exec_())