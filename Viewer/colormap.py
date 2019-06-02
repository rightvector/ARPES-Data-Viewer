from PyQt5.QtWidgets import QComboBox
from matplotlib.colors import ListedColormap
from matplotlib import cm
import glob, os
import numpy as np


cmaplist = [['viridis', 'plasma', 'inferno', 'magma', 'cividis'],
          ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 
          'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn'], 
          ['binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 
          'hot', 'afmhot', 'gist_heat', 'copper'], 
          ['PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic'], 
          ['twilight', 'twilight_shifted', 'hsv'], 
          ['ocean', 'gist_earth', 'terrain', 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 
          'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar']
         ]

cmapnamelist = ['viridis', 'plasma', 'inferno', 'magma', 'cividis', " ",
          'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 
          'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn', " ",
          'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 
          'hot', 'afmhot', 'gist_heat', 'copper', " ",
          'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic', " ", 
          'twilight', 'twilight_shifted', 'hsv', " ", 
          'ocean', 'gist_earth', 'terrain', 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 
          'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar']


class CustomComboBox(QComboBox):
    def __init__(self):
        super(CustomComboBox, self).__init__()
        indexlist = []
        for i, clist in zip(range(len(cmaplist)), cmaplist):
            self.addItems(clist)
            if i == 0:
                indexlist.append(len(clist))
            else:
                indexlist.append(indexlist[i-1]+len(clist)+1)
        for i in indexlist:
            self.insertSeparator(i)
        self.addItems(self.LoadCustomerCmap())

    def LoadCustomerCmap(self):
        cmapfilelist = glob.glob("./cmap/*.cm")
        namelist=[]
        for cmapfile in cmapfilelist:
            cmapdata = np.loadtxt(cmapfile)
            cmapname = os.path.splitext(os.path.basename(cmapfile))[0]
            cmap_1 = ListedColormap(cmapdata[:,0:3])
            cmap_2 = ListedColormap(cmapdata[:,3:6])
            cm.register_cmap(name=cmapname, cmap=cmap_1)
            cm.register_cmap(name=cmapname+"_r", cmap=cmap_2)
            namelist.append(cmapname)
        return namelist
