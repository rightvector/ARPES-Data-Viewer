import numpy as np
import scipy.optimize as op
import scipy.interpolate as ip
import ast, os, time, threading, copy, datetime
from math import sin, cos, sqrt, pi
import multiprocessing as mp
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject
from struct import Struct
import kspace


#decorator
def FalseRawData(func):
    '''
    Decorator setting rawdataflag.
    '''
    def wrapper(*args):
        instance = args[0]
        func(*args)
        instance.rawdataflag = False
        instance.writeProperty(False)
    return wrapper


def ArPy2Data(filepath):
    '''
    The arpy file should be exported from Igor Pro.
    '''
    base = os.path.basename(filepath)
    filename = os.path.splitext(base)[0]
    with open(filepath, "rb") as binfile:
        headerStruct = Struct("<9sss5i")
        header = headerStruct.unpack(binfile.read(headerStruct.size))
        if header[0].decode("UTF-8") != "ARPY_FILE":
            QMessageBox.information(None, "Error", filepath.split('/')[-1]+" is not a standard data file.", QMessageBox.Ok)
            return None
        else:
            #read string property
            if header[1].decode("UTF-8") == 'N':
                energyAxis = None
            else:
                energyAxis = header[1].decode("UTF-8")
            if header[2].decode("UTF-8") == 'N':
                spacemode = None
            elif header[2].decode("UTF-8") == 'A':
                spacemode = "Angular"
            elif header[2].decode("UTF-8") == 'M':
                spacemode = "Momentum"

            #read dimension
            dims = header[3]
            size = (header[4], header[5], header[6], header[7])

            #read scale
            xscale = None
            yscale = None
            zscale = None
            tscale = None
            xscale = np.zeros(size[0], dtype=np.float64)
            byte_num = binfile.readinto(xscale)
            if byte_num != 8*size[0]:
                QMessageBox.information(None, "Error", "Error in reading xscale.", QMessageBox.Ok)
                return None
            if dims > 1:
                yscale = np.zeros(size[1], dtype=np.float64)
                byte_num = binfile.readinto(yscale)
                if byte_num != 8*size[1]:
                    QMessageBox.information(None, "Error", "Error in reading yscale.", QMessageBox.Ok)
                    return None
            if dims > 2:
                zscale = np.zeros(size[2], dtype=np.float64)
                byte_num = binfile.readinto(zscale)
                if byte_num != 8*size[2]:
                    QMessageBox.information(None, "Error", "Error in reading zscale.", QMessageBox.Ok)
                    return None
            if dims > 3:
                tscale = np.zeros(size[3], dtype=np.float64)
                byte_num = binfile.readinto(tscale)
                if byte_num != 8*size[3]:
                    QMessageBox.information(None, "Error", "Error in reading tscale.", QMessageBox.Ok)
                    return None
            
            #read data
            if dims == 1:
                shape = size[0]
                item_num = size[0]
                data = np.zeros(shape, dtype=np.float32)
                byte_num = binfile.readinto(data)
            elif dims == 2:
                shape = (size[1], size[0])
                item_num = size[0]*size[1]
                data = np.zeros(shape, dtype=np.float32)
                byte_num = binfile.readinto(data)
                data = data.T
            elif dims == 3:
                shape = (size[2], size[1], size[0])   # numpy uses C order: layer first, column second, row third
                item_num = size[0]*size[1]*size[2]
                data = np.zeros(shape, dtype=np.float32)
                byte_num = binfile.readinto(data)
                data = data.transpose(2,1,0)
            elif dims == 4:
                shape = (size[3], size[2], size[1], size[0])
                item_num = size[0]*size[1]*size[2]*size[3]
                data = np.zeros(shape, dtype=np.float32)
                byte_num = binfile.readinto(data)
                data = data.transpose(3,2,1,0)
            if byte_num != 4*item_num:
                QMessageBox.information(None, "Error", "Error in reading data.", QMessageBox.Ok)
                return None
            
            spec = Spectrum(filename, data=data, xscale=xscale, yscale=yscale, zscale=zscale, tscale=tscale, spacemode=spacemode, energyAxis=energyAxis)
            spec.property["Path"]=filepath
            return spec


def Data2ArPy(Data, filepath):
    with open(filepath, "wb") as binfile:
        # write header
        filestring = b"ARPY_FILE"
        if Data.energyAxis is None:
            energyaxis = b'N'
        else:
            energyaxis = bytes(Data.energyAxis.encode('UTF-8'))
        if Data.spacemode is None:
            spacemode = b'N'
        elif Data.spacemode == "Angular":
            spacemode = b'A'
        elif Data.spacemode == "Momentum":
            spacemode = b'M'
        dims = Data.dims
        xsize = Data.dimension[0]
        if dims > 1:
            ysize = Data.dimension[1]
        else:
            ysize = 0
        if dims > 2:
            zsize = Data.dimension[2]
        else:
            zsize = 0
        if dims > 3:
            tsize = Data.dimension[3]
        else:
            tsize = 0
        headerStruct = Struct("<9sss5i")
        binfile.write(headerStruct.pack(filestring, energyaxis, spacemode, dims, xsize, ysize, zsize, tsize))

        # write scale
        xscale = Data.xscale.astype(np.float64)
        binfile.write(xscale.tobytes(order='F'))
        if dims > 1:
            yscale = Data.yscale.astype(np.float64)
            binfile.write(yscale.tobytes(order='F'))
        if dims > 2:
            zscale = Data.zscale.astype(np.float64)
            binfile.write(zscale.tobytes(order='F'))
        if dims > 3:
            tscale = Data.tscale.astype(np.float64)
            binfile.write(tscale.tobytes(order='F'))

        # write data
        data = Data.data.astype(np.float32)
        binfile.write(data.tobytes(order='F'))


def Ig2Py2Data(filepath):
    '''
    The Ig2py file should be exported from Igor Pro.
    '''
    base = os.path.basename(filepath)
    filename = os.path.splitext(base)[0]
    with open(filepath) as txtfile:
        filestr = txtfile.readlines()
        if len(filestr) == 0 or filestr[0].rstrip() != "#Igor to Python":
            QMessageBox.information(None, "Error", filepath.split('/')[-1]+" is not a standard data file.", QMessageBox.Ok)
            return None
        else:
            #read property
            headeridx = filestr.index("[Header]\n")
            ProStr = "{"
            i = 1
            while not len(filestr[headeridx+i].rstrip()) == 0:
                ProStr += filestr[headeridx+i].rstrip()+","
                i += 1
            ProStr += "\"Location\":\""+filepath+"\","
            ProStr += "}"

            #read scale
            ScaleStr = ""
            scaleidx = filestr.index("[Scale]\n")
            i = 1
            while not len(filestr[scaleidx+i].rstrip()) == 0:
                ScaleStr += filestr[scaleidx+i]
                i += 1
            
            #read data
            dataidx = filestr.index("[Data]\n")
            DataStr = ""
            for line in filestr[dataidx+1:]:
                DataStr += line
            spec = Spectrum(filename, propstr=ProStr, scalestr=ScaleStr, datastr=DataStr)
            return spec


def scale2pnt(value, scale):
    return (np.abs(scale - value)).argmin()


def Angle2Kx_single(energy, angle):
    if energy > 0:
        return 0.512*np.sqrt(energy)*np.sin(angle*np.pi/180)
    else:
        return np.nan


def Angle2Ky_single(energy, phi, theta):
    if energy > 0:
        return 0.512*np.sqrt(energy)*np.sin(theta*np.pi/180)*np.cos(phi*np.pi/180)
    else:
        return np.nan


def Angle2Kx_v_single(energy, phi, alpha, theta):
    if energy > 0:
        return 0.512*np.sqrt(energy)*(np.sin(phi*np.pi/180)*np.cos(alpha*np.pi/180)*np.cos(theta*np.pi/180)+np.sin(alpha*np.pi/180)*np.cos(phi*np.pi/180))
    else:
        return np.nan


def Angle2Ky_v_single(energy, alpha, theta):
    if energy > 0:
        return 0.512*np.sqrt(energy)*(np.cos(alpha*np.pi/180)*np.sin(theta*np.pi/180))
    else:
        return np.nan


def Angle2KxKy_func(x, *args):
    # x = (alpha, theta)        units of alpha and theta are rad
    # args = (phi, px, py)      px and py are normalized by energy
    alpha, theta = x.tolist()
    phi, px, py = args
    return [sin(alpha+phi)-sin(phi)*cos(alpha)*(1-cos(theta))-px, cos(alpha)*sin(theta)-py]


def Angle2KxKy_jac(x, *args):
    alpha, theta = x.tolist()
    phi, px, py = args
    return [
        [cos(alpha+phi)+sin(phi)*sin(alpha)*(1-cos(theta)), -sin(phi)*cos(alpha)*sin(theta)],
        [-sin(alpha)*sin(theta), cos(alpha)*cos(theta)]
        ]


def K2Angle_array(energy, k):
    if (energy > 0).all():
        return np.arcsin(k/0.512/np.sqrt(energy))*180/np.pi


def Kx2Angle_array(energy, kx):
    "wave vector to phi"
    if energy > 0:
        sinphi = kx/0.512/np.sqrt(energy)
        return np.arcsin(sinphi)*180/np.pi


def KxKy2Angle_array(energy, kx, ky):
    "wave vector to theta"
    if energy > 0:
        sinphi = kx/0.512/np.sqrt(energy)
        phi_arc = np.arcsin(sinphi)
        sintheta = ky/0.512/np.sqrt(energy)/np.cos(phi_arc)
        mask_plus = (sintheta > 1)
        mask_minus = (sintheta < -1)
        sintheta[mask_plus] = 1
        sintheta[mask_minus] = -1
        return np.arcsin(sintheta)*180/np.pi


@FalseRawData
def transpose2D(Data):
    Data.data = Data.data.T
    x, y = Data.dimension
    Data.dimension=(y, x)
    Data.xmin, Data.ymin = Data.ymin, Data.xmin
    Data.xmax, Data.ymax = Data.ymax, Data.xmax
    Data.xstep, Data.ystep = Data.ystep, Data.xstep
    Data.xscale, Data.yscale = Data.yscale, Data.xscale
    if Data.energyAxis == 'X':
        Data.energyAxis = 'Y'
    elif Data.energyAxis == 'Y':
        Data.energyAxis = 'X'


@FalseRawData
def transpose3D(Data):
    Data.data = Data.data.transpose(1,0,2)
    x, y, z = Data.dimension
    Data.dimension=(y, x, z)
    Data.xmin, Data.ymin = Data.ymin, Data.xmin
    Data.xmax, Data.ymax = Data.ymax, Data.xmax
    Data.xstep, Data.ystep = Data.ystep, Data.xstep
    Data.xscale, Data.yscale = Data.yscale, Data.xscale
    if Data.energyAxis == 'X':
        Data.energyAxis = 'Y'
    elif Data.energyAxis == 'Y':
        Data.energyAxis = 'X'


@FalseRawData
def changeZAxis3D(Data, ZAxis):
    if ZAxis == 'X':
        Data.data = Data.data.transpose(1,2,0)
        x, y, z = Data.dimension
        Data.dimension=(y, z, x)
        Data.xmin, Data.ymin, Data.zmin = Data.ymin, Data.zmin, Data.xmin
        Data.xmax, Data.ymax, Data.zmax = Data.ymax, Data.zmax, Data.xmax
        Data.xstep, Data.ystep, Data.zstep = Data.ystep, Data.zstep, Data.xstep
        Data.xscale, Data.yscale, Data.zscale = Data.yscale, Data.zscale, Data.xscale
        if Data.energyAxis == 'X':
            Data.energyAxis = 'Z'
        elif Data.energyAxis == 'Y':
            Data.energyAxis = 'X'
        elif Data.energyAxis == 'Z':
            Data.energyAxis = 'Y'
    elif ZAxis == 'Y':
        Data.data = Data.data.transpose(2,0,1)
        x, y, z = Data.dimension
        Data.dimension=(z, x, y)
        Data.xmin, Data.ymin, Data.zmin = Data.zmin, Data.xmin, Data.ymin
        Data.xmax, Data.ymax, Data.zmax = Data.zmax, Data.xmax, Data.ymax
        Data.xstep, Data.ystep, Data.zstep = Data.zstep, Data.xstep, Data.ystep
        Data.xscale, Data.yscale, Data.zscale = Data.zscale, Data.xscale, Data.yscale
        if Data.energyAxis == 'X':
            Data.energyAxis = 'Y'
        elif Data.energyAxis == 'Y':
            Data.energyAxis = 'Z'
        elif Data.energyAxis == 'Z':
            Data.energyAxis = 'X'


@FalseRawData
def mirror2D(Data, axis):
    if axis == 'X':
        Data.data = Data.data[::-1, :]
        Data.xmin, Data.xmax = -1*Data.xmax, -1*Data.xmin 
        Data.xscale = -Data.xscale[::-1]
    elif axis == 'Y':
        Data.data = Data.data[:, ::-1]
        Data.ymin, Data.ymax = -1*Data.ymax, -1*Data.ymin
        Data.yscale = -Data.yscale[::-1]


@FalseRawData
def mirror3D(Data, axis):
    if axis == 'X':
        Data.data = Data.data[::-1, :, :]
        Data.xmin, Data.xmax = -1*Data.xmax, -1*Data.xmin 
        Data.xscale = -Data.xscale[::-1]
    elif axis == 'Y':
        Data.data = Data.data[:, ::-1, :]
        Data.ymin, Data.ymax = -1*Data.ymax, -1*Data.ymin
        Data.yscale = -Data.yscale[::-1]


@FalseRawData
def normal2D(Data, axis):
    if axis == 'X':
        for i in range(Data.data.shape[1]):
            XDC = Data.data[:, i]
            mask = np.isnan(XDC)
            if len(XDC[~mask]) > 1:
                minvalue = XDC[~mask].min()
                maxvalue = XDC[~mask].max()
                if maxvalue > minvalue:
                    XDC = (XDC-minvalue)/(maxvalue-minvalue)
                    Data.data[:, i] = XDC
                else:
                    Data.data[:, i] = np.nan
            else:
                Data.data[:, i] = np.nan
    elif axis == 'Y':
        for i in range(Data.data.shape[0]):
            YDC = Data.data[i, :]
            mask = np.isnan(YDC)
            if len(YDC[~mask]) > 1:
                minvalue = YDC[~mask].min()
                maxvalue = YDC[~mask].max()
                if maxvalue > minvalue:
                    YDC = (YDC-minvalue)/(maxvalue-minvalue)
                    Data.data[i, :] = YDC
                else:
                    Data.data[i, :] = np.nan
            else:
                Data.data[i, :] = np.nan


@FalseRawData
def crop(Data, x0, x1, y0, y1):
    if x0 < Data.xscale[scale2pnt(x0, Data.xscale)]:
        x0idx = max(scale2pnt(x0, Data.xscale) - 1, 0)
    else:
        x0idx = scale2pnt(x0, Data.xscale)
    if x1 > Data.xscale[scale2pnt(x1, Data.xscale)]:
        x1idx = min(scale2pnt(x1, Data.xscale) + 1, Data.dimension[0])
    else:
        x1idx = scale2pnt(x1, Data.xscale)
    if y0 < Data.yscale[scale2pnt(y0, Data.yscale)]:
        y0idx = max(scale2pnt(y0, Data.yscale) - 1, 0)
    else:
        y0idx = scale2pnt(y0, Data.yscale)
    if y1 > Data.yscale[scale2pnt(y1, Data.yscale)]:
        y1idx = min(scale2pnt(y1, Data.yscale) + 1, Data.dimension[1])
    else:
        y1idx = scale2pnt(y1, Data.yscale)
    if Data.dims == 2:
        Data.data = Data.data[x0idx:x1idx+1, y0idx:y1idx+1]
        Data.dimension = (x1idx-x0idx+1, y1idx-y0idx+1)
    elif Data.dims == 3:
        Data.data = Data.data[x0idx:x1idx+1, y0idx:y1idx+1, :]
        Data.dimension = Data.data.shape
    Data.xscale = Data.xscale[x0idx:x1idx+1]
    Data.yscale = Data.yscale[y0idx:y1idx+1]
    Data.xmin = Data.xscale[0]
    Data.xmax = Data.xscale[-1]
    Data.ymin = Data.yscale[0]
    Data.ymax = Data.yscale[-1]


@FalseRawData
def merge2D(Data, xnum, ynum):
    if xnum > 1 and xnum < Data.data.shape[0]:
        sliceList = []
        newxnum = int(np.ceil(Data.data.shape[0]/xnum))
        for i in range(xnum):
            subdata = Data.data[i::xnum, :]
            if subdata.shape[0] != newxnum:
                subdata = np.vstack((subdata, np.zeros(subdata.shape[1])))
            sliceList.append(subdata)
        weight = np.ones((newxnum, 1))/xnum
        if Data.data.shape[0] % xnum != 0:
            weight[-1, 0] = 1/(Data.data.shape[0] % xnum)
        Data.data = np.stack(sliceList).sum(0)*weight
        offset = Data.xmin + Data.xstep*(xnum-1)/2
        Data.xstep = xnum*Data.xstep
        Data.xscale = offset + Data.xstep*np.arange(Data.data.shape[0])
        Data.xmin = Data.xscale[0]
        Data.xmax = Data.xscale[-1]
    if ynum > 1 and ynum < Data.data.shape[1]:
        sliceList = []
        newynum = int(np.ceil(Data.data.shape[1]/ynum))
        for i in range(ynum):
            subdata = Data.data[:, i::ynum]
            if subdata.shape[1] != newynum:  # shape[1] of some data will be newynum-1
                subdata = np.hstack((subdata, np.zeros((subdata.shape[0], 1))))  # to fill these subdata by 0
            sliceList.append(subdata)
        weight = np.ones(newynum)/ynum  # different subdata have different weight in calculating sum or average value
        if Data.data.shape[1] % ynum != 0:
            weight[-1] = 1/(Data.data.shape[1] % ynum)
        Data.data = np.stack(sliceList).sum(0)*weight
        offset = Data.ymin + Data.ystep*(ynum-1)/2
        Data.ystep = ynum*Data.ystep
        Data.yscale = offset + Data.ystep*np.arange(Data.data.shape[1])
        Data.ymin = Data.yscale[0]
        Data.ymax = Data.yscale[-1]
    Data.dimension = Data.data.shape


@FalseRawData
def Tokspace2D(Data, energyaxis):
    if Data.spacemode != "Momentum":
        if Data.energyAxis == 'X' or energyaxis == 'X':
            if Data.ymin*Data.ymax < 0:
                kmin = Angle2Kx_single(Data.xmax, Data.ymin)
                kmax = Angle2Kx_single(Data.xmax, Data.ymax)
            elif Data.ymin > 0:
                kmin = Angle2Kx_single(Data.xmin, Data.ymin)
                kmax = Angle2Kx_single(Data.xmax, Data.ymax)
            elif Data.ymin < 0:
                kmin = Angle2Kx_single(Data.xmax, Data.ymin)
                kmax = Angle2Kx_single(Data.xmin, Data.ymax)
            kscale = np.linspace(kmin, kmax, len(Data.yscale))
            kgrid, energygrid = np.meshgrid(kscale, Data.xscale)
            anglegrid = K2Angle_array(energygrid, kgrid)
            if np.isnan(anglegrid).any():
                return -1
            data_k = ip.interpn((Data.xscale, Data.yscale), Data.data, np.vstack((energygrid.flatten(), anglegrid.flatten())).T, bounds_error=False, fill_value=np.nan)
            Data.data = data_k.reshape(Data.dimension[0], Data.dimension[1])
            Data.yscale = kscale
            Data.ymin, Data.ymax = kmin, kmax
            Data.ystep = (kmax-kmin)/(len(Data.yscale)-1)
        elif Data.energyAxis == 'Y' or energyaxis == 'Y':
            if Data.xmin*Data.xmax < 0:
                kmin = Angle2Kx_single(Data.ymax, Data.xmin)
                kmax = Angle2Kx_single(Data.ymax, Data.xmax)
            elif Data.xmin > 0:
                kmin = Angle2Kx_single(Data.ymin, Data.xmin)
                kmax = Angle2Kx_single(Data.ymax, Data.xmax)
            elif Data.xmin < 0:
                kmin = Angle2Kx_single(Data.ymax, Data.xmin)
                kmax = Angle2Kx_single(Data.ymin, Data.xmax)
            kscale = np.linspace(kmin, kmax, len(Data.xscale))
            kgrid, energygrid = np.meshgrid(kscale, Data.yscale)
            anglegrid = K2Angle_array(energygrid, kgrid)
            if np.isnan(anglegrid).any():
                return -1
            data_k = ip.interpn((Data.xscale, Data.yscale), Data.data, np.vstack((anglegrid.T.flatten(), energygrid.T.flatten())).T, bounds_error=False, fill_value=np.nan)
            Data.data = data_k.reshape(Data.dimension[0], Data.dimension[1])
            Data.xscale = kscale
            Data.xmin, Data.xmax = kmin, kmax
            Data.xstep = (kmax-kmin)/(len(Data.xscale)-1)
        Data.spacemode = "Momentum"
        return 0


@FalseRawData
def merge3D(Data, xnum, ynum, znum):
    if xnum > 1 and xnum < Data.data.shape[0]:
        sliceList = []
        newxnum = int(np.ceil(Data.data.shape[0]/xnum))
        for i in range(xnum):
            subdata = Data.data[i::xnum, :, :]
            if subdata.shape[0] != newxnum:
                subdata = np.vstack((subdata, np.zeros((1, subdata.shape[1], subdata.shape[2]))))
            sliceList.append(subdata)
        weight = np.ones((newxnum, 1, 1))/xnum
        if Data.data.shape[0] % xnum != 0:
            weight[-1, 0, 0] = 1/(Data.data.shape[0] % xnum)
        Data.data = np.stack(sliceList).sum(0)*weight
        offset = Data.xmin + Data.xstep*(xnum-1)/2
        Data.xstep = xnum*Data.xstep
        Data.xscale = offset + Data.xstep*np.arange(Data.data.shape[0])
        Data.xmin = Data.xscale[0]
        Data.xmax = Data.xscale[-1]
    if ynum > 1 and ynum < Data.data.shape[1]:
        sliceList = []
        newynum = int(np.ceil(Data.data.shape[1]/ynum))
        for i in range(ynum):
            subdata = Data.data[:, i::ynum, :]
            if subdata.shape[1] != newynum:
                subdata = np.vstack((subdata.transpose(1,0,2), np.zeros((1, subdata.shape[0], subdata.shape[2])))).transpose(1,0,2)
            sliceList.append(subdata)
        weight = np.ones((1, newynum, 1))/ynum
        if Data.data.shape[1] % ynum != 0:
            weight[0, -1, 0] = 1/(Data.data.shape[1] % ynum)
        Data.data = np.stack(sliceList).sum(0)*weight
        offset = Data.ymin + Data.ystep*(ynum-1)/2
        Data.ystep = ynum*Data.ystep
        Data.yscale = offset + Data.ystep*np.arange(Data.data.shape[1])
        Data.ymin = Data.yscale[0]
        Data.ymax = Data.yscale[-1]
    if znum > 1 and znum < Data.data.shape[2]:
        sliceList = []
        newznum = int(np.ceil(Data.data.shape[2]/znum))
        for i in range(znum):
            subdata = Data.data[:, :, i::znum]
            if subdata.shape[2] != newznum:
                subdata = np.vstack((subdata.transpose(2,0,1), np.zeros((1, subdata.shape[0], subdata.shape[1])))).transpose(1,2,0)
            sliceList.append(subdata)
        weight = np.ones((1, 1, newznum))/znum
        if Data.data.shape[2] % znum != 0:
            weight[0, 0, -1] = 1/(Data.data.shape[2] % znum)
        Data.data = np.stack(sliceList).sum(0)*weight
        offset = Data.zmin + Data.zstep*(znum-1)/2
        Data.zstep = znum*Data.zstep
        Data.zscale = offset + Data.zstep*np.arange(Data.data.shape[2])
        Data.zmin = Data.zscale[0]
        Data.zmax = Data.zscale[-1]
    Data.dimension = Data.data.shape


def interpzcut(argslist):
    #argslist = [data, energy, kxgrid, kygrid, xscale, yscale]
    try:
        shape = argslist[2].shape
        phigrid = Kx2Angle_array(argslist[1], argslist[2])
        thetagrid = KxKy2Angle_array(argslist[1], argslist[2], argslist[3])
        if np.isnan(phigrid).all() or np.isnan(thetagrid).all():
            data_k = np.array([np.nan])
        else:
            data_k = ip.interpn((argslist[4], argslist[5]), argslist[0], np.vstack((phigrid.flatten(), thetagrid.flatten())).T, bounds_error=False, fill_value=np.nan).reshape(shape)
    finally:
        return data_k


def interpzcut_v(argslist):
    #argslist = [data, energy, kxgrid, kygrid, xscale, yscale, bias, mis, error]
    data, energy, kxgrid, kygrid, xscale, yscale, bias, mis, error = argslist
    bias *= pi/180
    kxgrid /= 0.512*sqrt(energy)
    kygrid /= 0.512*sqrt(energy)
    kxsize, kysize = kxgrid.shape
    kxlist = kxgrid.flatten().astype(np.float64)
    kylist = kygrid.flatten().astype(np.float64)
    philist = np.ones(len(kxlist), dtype=np.float64)*(xscale[0]+xscale[-1])*pi/360
    thetalist = np.ones(len(kxlist), dtype=np.float64)*(yscale[0]+yscale[-1])*pi/360
    
    # @np.vectorize
    # def solve_angles(kx, ky):
    #     phi, theta = op.fsolve(Angle2KxKy_func, [(phimin+phimax)/2, (thetamin+thetamax)/2], (bias, kx, ky), fprime=Angle2KxKy_jac, col_deriv=True, xtol=error, maxfev=mis)
    #     return phi, theta

    # t0 = datetime.datetime.now()
    #philist, thetalist = solve_angles(kxgrid.flatten(), kygrid.flatten())
    kspace.solver(philist, thetalist, bias, kxlist, kylist, error, mis)
    # t1 = datetime.datetime.now()
    # print((t1-t0).microseconds)
    philist *= 180/pi
    thetalist *= 180/pi

    if np.isnan(philist).all() or np.isnan(thetalist).all():
        data_k = np.array([np.nan])
    else:
        data_k = ip.interpn((xscale, yscale), data, np.vstack((philist, thetalist)).T, bounds_error=False, fill_value=np.nan).reshape(kxsize, kysize)
    
    return data_k


class ThetaKspace3D(threading.Thread):
    def __init__(self, data, slit, bias, dlg, core, mis, error, mainPID, s):
        super(ThetaKspace3D, self).__init__()
        self.data = data
        self.slit = slit
        self.bias = bias
        self.dlg = dlg
        self.core = core
        self.mis = mis
        self.error = error
        self.mainPID = mainPID
        self.s = s
        self.flag = True

    def run(self):
        if self.data.spacemode != "Momentum":
            while not self.dlg.isVisible():
                pass
            self.dlg.activateWindow()
            if self.slit == 'H':
                self.data.xscale += self.bias
                self.data.xmin += self.bias
                self.data.xmax += self.bias
                if self.data.xmin < 0:
                    kxmin = Angle2Kx_single(self.data.zmax, self.data.xmin)
                else:
                    kxmin = Angle2Kx_single(self.data.zmin, self.data.xmin)
                if self.data.xmax > 0:
                    kxmax = Angle2Kx_single(self.data.zmax, self.data.xmax)
                else:
                    kxmax = Angle2Kx_single(self.data.zmin, self.data.xmax)
                if self.data.ymin < 0:
                    kymin = Angle2Ky_single(self.data.zmax, 0, self.data.ymin)
                else:
                    kymin = Angle2Ky_single(self.data.zmin, max(np.abs(self.data.xmin), np.abs(self.data.xmax)), self.data.ymin)
                if self.data.ymax > 0:
                    kymax = Angle2Ky_single(self.data.zmax, 0, self.data.ymax)
                else:
                    kymax = Angle2Ky_single(self.data.zmin, max(np.abs(self.data.xmin), np.abs(self.data.xmax)), self.data.ymax)
                try:
                    kxscale = np.linspace(kxmin, kxmax, len(self.data.xscale))
                    kyscale = np.linspace(kymin, kymax, int(np.round(len(self.data.xscale)*(kymax-kymin)/(kxmax-kxmin))))
                    kxgrid, kygrid = np.meshgrid(kxscale, kyscale, indexing='ij')
                except:
                    self.s.stoped.emit(0)
                    self.flag = False
                if os.getpid() == self.mainPID and self.flag:
                    datacollector = []
                    pool = mp.Pool(self.core)
                    args = [(self.data.data[:, :, i], self.data.zscale[i], kxgrid, kygrid, self.data.xscale, self.data.yscale) for i in range(self.data.dimension[2])]
                    for i, data in enumerate(pool.imap(interpzcut, args)):
                        if (np.isnan(data)).all():
                            self.s.stoped.emit(0)
                            self.flag = False
                            pool.terminate()
                            break
                        elif not self.dlg.isVisible():
                            self.flag = False
                            pool.terminate()
                            break
                        else:
                            datacollector.append(data)
                            self.s.progress.emit(int(i*1000/len(self.data.zscale)))
                    pool.close()
                    pool.join()
                    if self.flag:
                        self.data.data = np.stack(datacollector, axis=2)
                        self.data.dimension = self.data.data.shape
                        self.data.xscale = kxscale
                        self.data.yscale = kyscale
                        self.data.xmin, self.data.xmax = kxmin, kxmax
                        self.data.ymin, self.data.ymax = kymin, kymax
                        self.data.xstep = (kxmax-kxmin)/(len(self.data.xscale)-1)
                        self.data.ystep = (kymax-kymin)/(len(self.data.yscale)-1)
                        self.data.rawdataflag = False
                        self.s.progress.emit(1000)
                        self.data.spacemode = "Momentum"
                        self.data.rawdataflag = False
                        self.data.writeProperty(False)
                        while not self.dlg.isVisible():
                            time.sleep(0.01)
                        self.s.finished.emit()
            elif self.slit == 'V':
                absthetamax = max(np.abs(self.data.ymin), np.abs(self.data.ymax))
                if self.bias >= 0:
                    if self.data.xmax + self.bias >= 0:
                        kxmax = Angle2Kx_single(self.data.zmax, self.data.xmax + self.bias)
                    else:
                        kxmax = Angle2Kx_single(self.data.zmin, self.data.xmax + self.bias)
                    if Angle2Kx_v_single(1, self.bias, self.data.xmin, absthetamax) >= 0:
                        kxmin = Angle2Kx_v_single(self.data.zmin, self.bias, self.data.xmin, absthetamax)
                    else:
                        kxmin = Angle2Kx_v_single(self.data.zmax, self.bias, self.data.xmin, absthetamax)
                else:
                    if Angle2Kx_v_single(1, self.bias, self.data.xmax, absthetamax) >= 0:
                        kxmax = Angle2Kx_v_single(self.data.zmax, self.bias, self.data.xmax, absthetamax)
                    else:
                        kxmax = Angle2Kx_v_single(self.data.zmin, self.bias, self.data.xmax, absthetamax)
                    if self.data.xmin + self.bias >= 0:
                        kxmin = Angle2Kx_single(self.data.zmin, self.data.xmin + self.bias)
                    else:
                        kxmin = Angle2Kx_single(self.data.zmax, self.data.xmin + self.bias)
                if self.data.ymax >= 0:
                    kymax = Angle2Kx_single(self.data.zmax, self.data.ymax)
                else:
                    kymax = Angle2Kx_single(self.data.zmin, self.data.ymax)
                if self.data.ymin < 0:
                    kymin = Angle2Kx_single(self.data.zmax, self.data.ymin)
                else:
                    kymin = Angle2Kx_single(self.data.zmin, self.data.ymin)
                try:
                    kxscale = np.linspace(kxmin, kxmax, len(self.data.xscale), dtype=np.float64)
                    kyscale = np.linspace(kymin, kymax, int(np.round(len(self.data.xscale)*(kymax-kymin)/(kxmax-kxmin))), dtype=np.float64)
                    kxgrid, kygrid = np.meshgrid(kxscale, kyscale, indexing='ij')
                except:
                    self.s.stoped.emit(0)
                    self.flag = False
                if os.getpid() == self.mainPID and self.flag:
                    datacollector = []
                    pool = mp.Pool(self.core)
                    args = [(self.data.data[:, :, i], self.data.zscale[i], kxgrid, kygrid, self.data.xscale, self.data.yscale, self.bias, self.mis, self.error) for i in range(self.data.dimension[2])]
                    for i, data in enumerate(pool.imap(interpzcut_v, args)):
                        if (np.isnan(data)).all():
                            self.s.stoped.emit(0)
                            self.flag = False
                            pool.terminate()
                            break
                        elif not self.dlg.isVisible():
                            self.flag = False
                            pool.terminate()
                            break
                        else:
                            datacollector.append(data)
                            self.s.progress.emit(int(i*1000/len(self.data.zscale)))
                    pool.close()
                    pool.join()
                    if self.flag:
                        self.data.data = np.stack(datacollector, axis=2)
                        self.data.dimension = self.data.data.shape
                        self.data.xscale = kxscale
                        self.data.yscale = kyscale
                        self.data.xmin, self.data.xmax = kxmin, kxmax
                        self.data.ymin, self.data.ymax = kymin, kymax
                        self.data.xstep = (kxmax-kxmin)/(len(self.data.xscale)-1)
                        self.data.ystep = (kymax-kymin)/(len(self.data.yscale)-1)
                        self.data.rawdataflag = False
                        self.s.progress.emit(1000)
                        self.data.spacemode = "Momentum"
                        self.data.rawdataflag = False
                        self.data.writeProperty(False)
                        while not self.dlg.isVisible():
                            time.sleep(0.01)
                        self.s.finished.emit()
        else:
            if os.getpid() == self.mainPID:
                while not self.dlg.isVisible():
                    time.sleep(0.01)
                self.s.finished.emit()


class Spectrum():
    def __init__(self, fname="spec", data=None, xscale=None, yscale=None, zscale=None, tscale=None, spacemode=None, energyAxis=None, propstr=None, scalestr=None, datastr=None):
        #basic data
        self.name = fname
        self.data = data
        self.xscale = xscale
        self.yscale = yscale
        self.zscale = zscale
        self.tscale = tscale
        self.spacemode = spacemode
        self.energyAxis = energyAxis

        self.dimension = (2,)
        self.dims = 1
        self.property = {}
        self.note = ""

        self.xmin = 0
        self.xmax = 0
        self.xstep = 0
        
        self.ymin = 0
        self.ymax = 0
        self.ystep = 0
        
        self.zmin = 0
        self.zmax = 0
        self.zstep = 0

        self.tmin = 0
        self.tmax = 0
        self.tstep = 0

        #raw data
        self.rawdata = None
        self.rawxscale = None
        self.rawyscale = None
        self.rawzscale = None
        self.rawtscale = None
        self.rawproperty = {}
        self.rawdataflag = True
        
        #initiate property
        self.initProp()

        #set string data
        self.setStrProperty(propstr)
        self.setStrScale(scalestr)
        self.setStrData(datastr)

    def initProp(self):
        if self.data is not None:
            self.dimension = self.data.shape
            self.dims = len(self.dimension)
            self.rawdata = np.copy(self.data)
        if self.xscale is not None:
            self.xmin = self.xscale[0]
            self.xstep = self.xscale[1]-self.xscale[0]
            self.xmax = self.xscale[-1]
            self.rawxscale = np.copy(self.xscale)
        if self.yscale is not None:
            self.ymin = self.yscale[0]
            self.ystep = self.yscale[1]-self.yscale[0]
            self.ymax = self.yscale[-1]
            self.rawyscale = np.copy(self.yscale)
        if self.zscale is not None:
            self.zmin = self.zscale[0]
            self.zstep = self.zscale[1]-self.zscale[0]
            self.zmax = self.zscale[-1]
            self.rawzscale = np.copy(self.zscale)
        if self.tscale is not None:
            self.tmin = self.tscale[0]
            self.tstep = self.tscale[1]-self.tscale[0]
            self.tmax = self.tscale[-1]
            self.rawtscale = np.copy(self.tscale)
        self.writeProperty(False)
        self.rawproperty = copy.deepcopy(self.property)

    def setStrProperty(self, StrProperty):
        if StrProperty != None:
            self.property = ast.literal_eval(StrProperty)
            self.rawproperty = copy.deepcopy(self.property)
            self.readProperty(False)
    
    def setStrScale(self, StrScale):
        if StrScale != None:
            ScaleList = StrScale.rstrip().split("\n")
            if len(ScaleList) > 0:
                self.xscale = np.fromstring(ScaleList[0], sep="\t")
                self.rawxscale = np.copy(self.xscale)
            if len(ScaleList) > 1:
                self.yscale = np.fromstring(ScaleList[1], sep="\t")
                self.rawyscale = np.copy(self.yscale)
            if len(ScaleList) > 2:
                self.zscale = np.fromstring(ScaleList[2], sep="\t")
                self.rawzscale = np.copy(self.zscale)
            if len(ScaleList) > 3:
                self.tscale = np.fromstring(ScaleList[3], sep="\t")
                self.rawtscale = np.copy(self.tscale)

    def setStrData(self, StrData):
        if StrData != None:
            self.data = np.fromstring(StrData, sep="\t")
            if self.property.get("Dimension") != None:
                self.data.shape = self.dimension
            self.rawdata = np.copy(self.data)

    def readProperty(self, readraw):
        if readraw:
            pro = self.rawproperty
        else:
            pro = self.property
        self.dimension = ast.literal_eval(pro.get("Dimension"))
        self.dims = len(self.dimension)
        self.xmin = ast.literal_eval(pro.get("XMin"))
        self.xmax = ast.literal_eval(pro.get("XMax"))
        self.xstep = ast.literal_eval(pro.get("XStep"))
        self.ymin = ast.literal_eval(pro.get("YMin"))
        self.ymax = ast.literal_eval(pro.get("YMax"))
        self.ystep = ast.literal_eval(pro.get("YStep"))
        self.zmin = ast.literal_eval(pro.get("ZMin"))
        self.zmax = ast.literal_eval(pro.get("ZMax"))
        self.zstep = ast.literal_eval(pro.get("ZStep"))
        self.tmin = ast.literal_eval(pro.get("TMin"))
        self.tmax = ast.literal_eval(pro.get("TMax"))
        self.tstep = ast.literal_eval(pro.get("TStep"))
        self.spacemode = pro.get("spacemode")
        self.energyAxis = pro.get("energyAxis")

    def writeProperty(self, writeraw):
        if writeraw:
            pro = self.rawproperty
        else:
            pro = self.property
        pro["Dimension"] = "%s" % (self.dimension,)
        pro["XMin"] = "%.6f" % self.xmin
        pro["XMax"] = "%.6f" % self.xmax
        pro["XStep"] = "%.6f" % self.xstep
        pro["YMin"] = "%.6f" % self.ymin
        pro["YMax"] = "%.6f" % self.ymax
        pro["YStep"] = "%.6f" % self.ystep
        pro["ZMin"] = "%.6f" % self.zmin
        pro["ZMax"] = "%.6f" % self.zmax
        pro["ZStep"] = "%.6f" % self.zstep
        pro["TMin"] = "%.6f" % self.tmin
        pro["TMax"] = "%.6f" % self.tmax
        pro["TStep"] = "%.6f" % self.tstep
        if self.spacemode != None:
            pro["spacemode"] = "%s" % self.spacemode
        if self.energyAxis != None:
            pro["energyAxis"] = "%s" % self.energyAxis

    def Restore(self):
        self.data = np.copy(self.rawdata)
        self.xscale = np.copy(self.rawxscale)
        if self.dims > 1:
            self.yscale = np.copy(self.rawyscale)
        if self.dims > 2:
            self.zscale = np.copy(self.rawzscale)
        if self.dims > 3:
            self.tscale = np.copy(self.rawtscale)
        self.readProperty(True)
        self.property = copy.deepcopy(self.rawproperty)
        self.rawdataflag = True

    def Save(self):
        self.rawdata = np.copy(self.data)
        self.rawxscale = np.copy(self.xscale)
        if self.dims > 1:
            self.rawyscale = np.copy(self.yscale)
        if self.dims > 2:
            self.rawzscale = np.copy(self.zscale)
        if self.dims > 3:
            self.rawtscale = np.copy(self.tscale)
        self.rawproperty = copy.deepcopy(self.property)
        self.rawdataflag = True