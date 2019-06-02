from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import numpy as np

class Selector():
    def __init__(self, ax, canvas, x0=0, y0=0, x1=1, y1=1):
        self.Rect = Rectangle((x0, y0), x1-x0, y1-y0, color="blue", alpha=0.2, visible=False)
        self.cHandles = Line2D([x0, x1, x1, x0], [y0, y0, y1, y1], marker='o', markersize=7, mfc='w', markeredgecolor='mediumblue', ls='none', alpha=0.8, visible=False, label='_nolegend_')
        self.eHandles = Line2D([(x0+x1)/2, x1, (x0+x1)/2, x0], [y0, (y0+y1)/2, y1, (y0+y1)/2], marker='s', markersize=5, mfc='w', markeredgecolor='dodgerblue', ls='none', alpha=0.8, visible=False, label='_nolegend_')
        self.artist = [self.Rect, self.cHandles, self.eHandles]
        self.region = (x0, y0, x1, y1)
        self.active_handle = 0
        self.visible = False
        self.ax = ax
        self.canvas = canvas
        self.moveing_state = "draw"
        self.origin = (0, 0)
        self.ax.add_patch(self.Rect)
        self.ax.add_line(self.cHandles)
        self.ax.add_line(self.eHandles)

    def resize(self, x0, y0, x1, y1):
        xmin, xmax = sorted((x0, x1))
        ymin, ymax = sorted((y0, y1))
        self.region = (xmin, ymin, xmax, ymax)
        self.Rect.set_xy((xmin, ymin))
        self.Rect.set_width(xmax-xmin)
        self.Rect.set_height(ymax-ymin)
        self.cHandles.set_data([xmin, xmax, xmax, xmin], [ymin, ymin, ymax, ymax])
        self.eHandles.set_data([(xmin+xmax)/2, xmax, (xmin+xmax)/2, xmin], [ymin, (ymin+ymax)/2, ymax, (ymin+ymax)/2])

    def set_visible(self, visible):
        self.Rect.set_visible(visible)
        self.cHandles.set_visible(visible)
        self.eHandles.set_visible(visible)
        self.visible = visible

    def isinRegion(self, x, y):
        if ((self.region[0] < x < self.region[2]) and (self.region[1] < y < self.region[3])):
            return True
        else:
            return False

    def nearestCorner(self, x, y):
        x0, y0, x1, y1 = self.region
        array = np.array([[x0,y0], [(x0+x1)/2, y0], [x1,y0], [x1, (y0+y1)/2], [x1,y1], [(x0+x1)/2, y1], [x0,y1], [x0, (y0+y1)/2]])
        pts = self.ax.transData.transform(array)
        diff = pts - ((x, y))
        distance = np.sqrt(np.sum(diff ** 2, axis=1))
        self.active_handle = distance.argmin()
        return distance.min()


class Selector3D():
    def __init__(self, axz, axx, axy, canvas, x0=0, y0=0, x1=1, y1=1):
        self.axz = axz
        self.axx = axx
        self.axy = axy
        self.canvas = canvas
        self.Rectz = Rectangle((x0, y0), x1-x0, y1-y0, color="blue", alpha=0.2, visible=False)
        self.Rectx = Rectangle((x0, self.axx.get_ybound()[0]), x1-x0, self.axx.get_ybound()[1]-self.axx.get_ybound()[0], color="green", alpha=0.2, visible=False)
        self.Recty = Rectangle((self.axy.get_xbound()[0], y0), self.axy.get_xbound()[1]-self.axy.get_xbound()[0], y1-y0, color="green", alpha=0.2, visible=False)
        self.cHandles = Line2D([x0, x1, x1, x0], [y0, y0, y1, y1], marker='o', markersize=7, mfc='w', markeredgecolor='mediumblue', ls='none', alpha=0.8, visible=False, label='_nolegend_')
        self.eHandles = Line2D([(x0+x1)/2, x1, (x0+x1)/2, x0], [y0, (y0+y1)/2, y1, (y0+y1)/2], marker='s', markersize=5, mfc='w', markeredgecolor='dodgerblue', ls='none', alpha=0.8, visible=False, label='_nolegend_')
        self.artistz = [self.Rectz, self.cHandles, self.eHandles]
        self.artistx = [self.Rectx]
        self.artisty = [self.Recty]
        self.region = (x0, y0, x1, y1)
        self.active_handle = 0
        self.visible = False
        self.moveing_state = "draw"
        self.origin = (0, 0)
        self.axz.add_patch(self.Rectz)
        self.axz.add_line(self.cHandles)
        self.axz.add_line(self.eHandles)
        self.axx.add_patch(self.Rectx)
        self.axy.add_patch(self.Recty)

    def resize(self, x0, y0, x1, y1):
        xmin, xmax = sorted((x0, x1))
        ymin, ymax = sorted((y0, y1))
        self.region = (xmin, ymin, xmax, ymax)
        self.Rectz.set_xy((xmin, ymin))
        self.Rectz.set_width(xmax-xmin)
        self.Rectz.set_height(ymax-ymin)
        self.Rectx.set_xy((xmin, self.axx.get_ybound()[0]))
        self.Rectx.set_width(xmax-xmin)
        self.Rectx.set_height(self.axx.get_ybound()[1]-self.axx.get_ybound()[0])
        self.Recty.set_xy((self.axy.get_xbound()[0], ymin))
        self.Recty.set_width(self.axy.get_xbound()[1]-self.axy.get_xbound()[0])
        self.Recty.set_height(ymax-ymin)
        self.cHandles.set_data([xmin, xmax, xmax, xmin], [ymin, ymin, ymax, ymax])
        self.eHandles.set_data([(xmin+xmax)/2, xmax, (xmin+xmax)/2, xmin], [ymin, (ymin+ymax)/2, ymax, (ymin+ymax)/2])

    def set_visible(self, visible):
        self.Rectz.set_visible(visible)
        self.Rectx.set_visible(visible)
        self.Recty.set_visible(visible)
        self.cHandles.set_visible(visible)
        self.eHandles.set_visible(visible)
        self.visible = visible

    def isinRegion(self, x, y):
        if ((self.region[0] < x < self.region[2]) and (self.region[1] < y < self.region[3])):
            return True
        else:
            return False

    def isinXRegion(self, x):
        if (self.region[0] < x < self.region[2]):
            return True
        else:
            return False

    def isinYRegion(self, y):
        if (self.region[1] < y < self.region[3]):
            return True
        else:
            return False

    def nearestCorner(self, x, y):
        x0, y0, x1, y1 = self.region
        array = np.array([[x0,y0], [(x0+x1)/2, y0], [x1,y0], [x1, (y0+y1)/2], [x1,y1], [(x0+x1)/2, y1], [x0,y1], [x0, (y0+y1)/2]])
        pts = self.axz.transData.transform(array)
        diff = pts - ((x, y))
        distance = np.sqrt(np.sum(diff ** 2, axis=1))
        self.active_handle = distance.argmin()
        return distance.min()
    
