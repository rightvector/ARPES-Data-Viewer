'''
This module aims to implement Reading and Writing operation for Igor files (.pxp, .pxt, .ibw).
'''

# Currently, we only realize data reading and writing for version 5 header. Only wave data are read into memory.

import struct
from struct import Struct
import os, platform
import numpy as np
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt
from Data import Spectrum

RECTYPE_MASK = 0x7FFF
MAXDIMS = 4
POINTER_FORMAT = 'l'  # 32 bit, Igor Pro always use 32-bit pointer in the header structure, even for 64-bit Igor Pro 8.
#POINTER_FORMAT = 'q'  # 64 bit

type_format = {      # ignore the complex and text wave
    2:'f',
    4:'d',
    8:'h',
    0x10:'i',
    0x20:'l'
}

npType = {
    2:np.float32,
    4:np.float64,
    8:np.int8,
    0x10:np.int16,
    0x20:np.int32
}

typeCode = {
    np.float32:2,
    np.float64:4,
    np.int8:8,
    np.int16:0x10,
    np.int32:0x20
}

typeSize = {
    np.float32:4,
    np.float64:8,
    np.int8:1,
    np.int16:2,
    np.int32:4
}

platformCode = {
    "Macintosh":1,
    "Windows":2
}


# Header struct
RecordHeader = Struct('<Hhl')
PlatformInfo = Struct('<hhd244s')


def IgorPackedFile2Data(filepath, useFilename):
    base = os.path.basename(filepath)
    filename = os.path.splitext(base)[0]
    datalist = []
    with open(filepath, "rb") as binfile:
        while True:
            record_bytes = binfile.read(RecordHeader.size)
            if record_bytes == b'':
                break
            else:
                header = RecordHeader.unpack(record_bytes)
                recordType, version, datanum = header

            if recordType == 3:
                # check version
                HeaderVersion, = struct.unpack('<h', binfile.read(struct.calcsize('<h')))
                binHeaderStruct = toBinHeader(HeaderVersion)
                waveHeaderStruct = toWaveHeader(HeaderVersion)
                if binHeaderStruct is None or waveHeaderStruct is None:
                    QMessageBox.information(None, "Error", "This is a Version {} Igor File.".format(HeaderVersion), QMessageBox.Ok)
                    break

                # read binheader
                binHeader = binHeaderStruct.unpack(binfile.read(binHeaderStruct.size))		
                checksum = binHeader[0]			
                wfmSize = binHeader[1]					
                formulaSize = binHeader[2]
                noteSize = binHeader[3]
                dataEUnitsSize = binHeader[4]
                dimEUnitsSize = binHeader[5:9]
                dimLabelsSize = binHeader[9:13]
                sIndicesSize = binHeader[13]
                optionsSize1 = binHeader[14]
                optionsSize2 = binHeader[15]

                # read waveheader
                waveHeader = waveHeaderStruct.unpack(binfile.read(waveHeaderStruct.size))
                npnts = waveHeader[3]
                type_code = waveHeader[4]
                waveName = waveHeader[8].decode('utf-8')
                dimsize = (waveHeader[11], waveHeader[12], waveHeader[13], waveHeader[14])
                dimdelta = (waveHeader[15], waveHeader[16], waveHeader[17], waveHeader[18])
                dimoffset = (waveHeader[19], waveHeader[20], waveHeader[21], waveHeader[22])
                if dimsize[1] == 0: # 1D
                    datashape = (dimsize[0],)
                    dim = 1
                elif dimsize[2] == 0: # 2D
                    datashape = (dimsize[1], dimsize[0])
                    dim = 2
                elif dimsize[3] == 0: # 3D
                    datashape = (dimsize[2], dimsize[1], dimsize[0])
                    dim = 3
                else:  # 4D
                    datashape = (dimsize[3], dimsize[2], dimsize[1], dimsize[0])
                    dim = 4

                # read data
                data = np.zeros(datashape, dtype=npType[type_code])
                binfile.readinto(data)
                if dim == 2:
                    data = data.transpose(1,0)
                elif dim == 3:
                    data = data.transpose(2,1,0)
                elif dim == 4:
                    data = data.transpose(3,2,1,0)
                

                # read formula
                if formulaSize != 0:
                    binfile.read(formulaSize)

                # read note
                note=''
                if noteSize != 0:
                    notebyte = binfile.read(noteSize)
                    note = notebyte.decode()
                    note = note.replace('\r','\n')

                # read dataUnits
                if dataEUnitsSize != 0:
                    binfile.read(dataEUnitsSize)

                # read dimUnits
                for i in dimEUnitsSize:
                    if i != 0:
                        binfile.read(i)

                # read dimLabels
                for i in dimLabelsSize:
                    if i != 0:
                        binfile.read(i)

                # read sindice
                if sIndicesSize != 0:
                    binfile.read(sIndicesSize)

                # read option
                if optionsSize1 != 0:
                    binfile.read(optionsSize1)
                if optionsSize2 != 0:
                    binfile.read(optionsSize2)

                # generate spacemode and energyAxis
                spacemode = searchspacemode(note)
                energyAxis = searchenergyAxis(note)
                
                # generate scale
                xscale = None
                yscale = None
                zscale = None
                tscale = None
                xscale = np.array([dimoffset[0]+i*dimdelta[0] for i in range(dimsize[0])])
                if dim > 1:
                    yscale = np.array([dimoffset[1]+i*dimdelta[1] for i in range(dimsize[1])])
                if dim > 2:
                    zscale = np.array([dimoffset[2]+i*dimdelta[2] for i in range(dimsize[2])])
                if dim > 3:
                    tscale = np.array([dimoffset[3]+i*dimdelta[3] for i in range(dimsize[3])])

                if useFilename:
                    name = filename
                else:
                    name = waveName            
                spec = Spectrum(name, data=data, xscale=xscale, yscale=yscale, zscale=zscale, tscale=tscale, spacemode=spacemode, energyAxis=energyAxis)
                spec.note = note
                spec.property["Path"]=filepath
                datalist.append(spec)
            else:
                recordData = binfile.read(datanum)

    return datalist


def Data2IgorPackedFile(Datalist, filepath):
    with open(filepath, "wb") as binfile:
        version = 5
        binHeaderStruct = toBinHeader(version)
        waveHeaderStruct = toWaveHeader(version)
        
        for Data in Datalist:
            # begin to write wave record
            dataPnts = 1
            for i in range(Data.dims):
                dataPnts *= Data.dimension[i]
            dataTypeSize = typeSize[Data.data.dtype.type]
            dataSize = dataPnts*dataTypeSize
            noteSize = len(Data.note)

            # write Record header
            binfile.write(RecordHeader.pack(3, 0, dataSize+noteSize+struct.calcsize('<h')+binHeaderStruct.size+waveHeaderStruct.size))  # '<h' for the version field

            #write version
            binfile.write(struct.pack("<h", version))

            #calculate wave header
            waveHeaderParas = toWaveHeaderParas(Data)
            waveHeaderBytes = waveHeaderStruct.pack(*waveHeaderParas)

            #first calculate checksum, here we only write wfmsize and notesize into file
            extraParas = tuple([0]*(4+2*MAXDIMS))
            binHeaderBytes = binHeaderStruct.pack(0, waveHeaderStruct.size+dataSize, 0, noteSize, *extraParas)
            checkSumBytes = struct.pack("<h", version)+binHeaderBytes+waveHeaderBytes
            shortBytesLen = int(len(checkSumBytes)/2)
            checkSum = -np.array(struct.unpack("<{}h".format(shortBytesLen), checkSumBytes), dtype=np.int16).sum()
            checkSum = -32768 + ((checkSum+32768) % 65536) # to avoid overflow for 16 bit SHORT format
            binHeaderBytes = binHeaderStruct.pack(checkSum, waveHeaderStruct.size+dataSize, 0, noteSize, *extraParas)

            #write header
            binfile.write(binHeaderBytes)
            binfile.write(waveHeaderBytes)

            #write data and note
            binfile.write(Data.data.tobytes('F'))
            binfile.write(Data.note.encode('utf-8'))


def toBinHeader(version):
    if version == 5:
        BinHeader5_Format = '<h{}l'.format(7+MAXDIMS*2)
        return Struct(BinHeader5_Format)
    else:
        return None


def toWaveHeader(version):
    if version == 5:
        WaveHeader5_Format = '<'
        WaveHeader5_Format += POINTER_FORMAT   # 0 struct WaveHeader5 **next
        WaveHeader5_Format += 'L'  # 1 unsigned long creationDate
        WaveHeader5_Format += 'L'  # 2 unsigned long modDate
        WaveHeader5_Format += 'l'  # 3 long npnts
        WaveHeader5_Format += 'h'  # 4 short type
        WaveHeader5_Format += 'h'  # 5 short dLock
        WaveHeader5_Format += '6s' # 6 char whpad1[6]
        WaveHeader5_Format += 'h'  # 7 short whVersion
        WaveHeader5_Format += '32s' # 8 char bname[MAX_WAVE_NAME5+1]
        WaveHeader5_Format += 'l'  # 9 long whpad2
        WaveHeader5_Format += POINTER_FORMAT  # 10 struct DataFolder **dFolder
        WaveHeader5_Format += '{}l'.format(MAXDIMS)  # 11:11+4 long nDim[MAXDIMS]
        WaveHeader5_Format += '{}d'.format(MAXDIMS)  # 11+4:11+8 double sfA[MAXDIMS]
        WaveHeader5_Format += '{}d'.format(MAXDIMS)  # 11+8:11+12 double sfB[MAXDIMS]
        WaveHeader5_Format += '4s'  # 23 char dataUnits[MAX_UNIT_CHARS+1]
        for i in range(MAXDIMS):   # 24:24+4 char dimUnits[MAXDIMS][MAX_UNIT_CHARS+1]
            WaveHeader5_Format += '4s'  
        WaveHeader5_Format += 'h'  # 28 short fsValid
        WaveHeader5_Format += 'h'  # 29 short whpad3
        WaveHeader5_Format += '2d'  # 30, 31 double topFullScale,botFullScale
        WaveHeader5_Format += POINTER_FORMAT  # 32 Handle dataEUnits
        WaveHeader5_Format += '{}'.format(MAXDIMS)+POINTER_FORMAT  # 33:33+4 Handle dimEUnits[MAXDIMS]
        WaveHeader5_Format += '{}'.format(MAXDIMS)+POINTER_FORMAT  # 37:37+4 Handle dimLabels[MAXDIMS]
        WaveHeader5_Format += POINTER_FORMAT  # 41 Handle waveNoteH
        WaveHeader5_Format += 'B'  # 42 unsigned char platform
        WaveHeader5_Format += '3B'  # 43:43+3 unsigned char spare[3]
        WaveHeader5_Format += '13l'  # 46:46+13 long whUnused[13]
        WaveHeader5_Format += '2l'  # 59, 60 long vRefNum, dirID
        WaveHeader5_Format += 'h'  # 61 short aModified
        WaveHeader5_Format += 'h'  # 62 short wModified
        WaveHeader5_Format += 'h'  # 63 short swModified
        WaveHeader5_Format += 's'  # 64 char useBits
        WaveHeader5_Format += 's'  # 65 char kindBits
        WaveHeader5_Format += POINTER_FORMAT  # 66 void **formula
        WaveHeader5_Format += 'l'  # 67 long depID
        WaveHeader5_Format += 'h'  # 68 short whpad4
        WaveHeader5_Format += 'h'  # 69 short srcFldr
        WaveHeader5_Format += POINTER_FORMAT  # 70 Handle fileName
        WaveHeader5_Format += POINTER_FORMAT  # 71 long **sIndices

        return Struct(WaveHeader5_Format)
    else:
        return None


def toWaveHeaderParas(Data):
    dataPnts = 1
    for i in range(Data.dims):
        dataPnts *= Data.dimension[i]
    wheader_paras = []
    wheader_paras.append(0)     # 0 struct WaveHeader5 **next
    wheader_paras.append(0)      # 1 unsigned long creationDate
    wheader_paras.append(0)   # 2 unsigned long modDate
    wheader_paras.append(dataPnts)   # 3 long npnts
    wheader_paras.append(typeCode[Data.data.dtype.type])     # 4 short type
    wheader_paras.append(0)   # 5 short dLock
    wheader_paras.append(b"\x00\x00\x00\x00\x00\x00")  # 6 char whpad1[6]
    wheader_paras.append(0)  # 7 short whVersion
    wheader_paras.append(Data.name[0:32].encode('utf-8'))   # 8 char bname[MAX_WAVE_NAME5+1]
    wheader_paras.append(0)   # 9 long whpad2
    wheader_paras.append(0)  # 10 struct DataFolder **dFolder
    for dim in Data.dimension:
        wheader_paras.append(dim)  # 11:11+dims long nDim[MAXDIMS]
    for _ in range(Data.dims, MAXDIMS):
        wheader_paras.append(0)    # 11+dims:11+4 
    wheader_paras.append(Data.xstep)   #  15 double sfA[MAXDIMS]
    wheader_paras.append(Data.ystep)   #  16
    wheader_paras.append(Data.zstep)   #  17
    wheader_paras.append(Data.tstep)   #  18
    if Data.xstep > 0:
        wheader_paras.append(Data.xmin)    # 19 double sfB[MAXDIMS]
    else:
        wheader_paras.append(Data.xmax)
    if Data.ystep > 0:
        wheader_paras.append(Data.ymin)    # 20
    else:
        wheader_paras.append(Data.ymax)
    if Data.zstep > 0:
        wheader_paras.append(Data.zmin)    # 21
    else:
        wheader_paras.append(Data.zmax)
    if Data.tstep > 0:
        wheader_paras.append(Data.tmin)    # 22
    else:
        wheader_paras.append(Data.tmax)
    wheader_paras.append(b"\x00\x00\x00\x00")   # 23 char dataUnits[MAX_UNIT_CHARS+1]
    for _ in range(MAXDIMS):    # 24:24+4 char dimUnits[MAXDIMS][MAX_UNIT_CHARS+1]
        wheader_paras.append(b"\x00\x00\x00\x00") 
    wheader_paras.append(0)   # 28 short fsValid
    wheader_paras.append(0)   # 29 short whpad3
    wheader_paras.append(0)   # 30,31 double topFullScale,botFullScale
    wheader_paras.append(0)
    wheader_paras.append(0)   # 32 Handle dataEUnits
    for _ in range(MAXDIMS):  # 33:33+4 Handle dimEUnits[MAXDIMS]
        wheader_paras.append(0)
    for _ in range(MAXDIMS):  # 37:37+4 Handle dimLabels[MAXDIMS]
        wheader_paras.append(0)
    wheader_paras.append(0)   # 41 Handle waveNoteH
    wheader_paras.append(platformCode[platform.system()])   # 42 unsigned char platform
    for _ in range(3):
        wheader_paras.append(0)   # 43:43+3 unsigned char spare[3]
    for _ in range(13):   # 46:46+13 long whUnused[13]
        wheader_paras.append(0)
    wheader_paras.append(0)   # 59,60 long vRefNum, dirID
    wheader_paras.append(0)
    wheader_paras.append(0)   # 61 short aModified
    wheader_paras.append(0)   # 62 short wModified
    wheader_paras.append(0)   # 63 short swModified
    wheader_paras.append(b"\x00")   # 64 char useBits
    wheader_paras.append(b"\x00")   # 65 char kindBits
    wheader_paras.append(0)   # 66 void **formula
    wheader_paras.append(0)   # 67 long depID
    wheader_paras.append(0)   # 68 short whpad4
    wheader_paras.append(0)   # 69 short srcFldr
    wheader_paras.append(0)   # 70 Handle fileName
    wheader_paras.append(0)   # 71 long **sIndices

    return tuple(wheader_paras)


def searchspacemode(note):
    itemlist = note.split('\n')
    for item in itemlist:
        if len(item.split('=')) == 2:
            key, value = item.split('=')
            if key == "spacemode":
                return value
    return None


def searchenergyAxis(note):
    itemlist = note.split('\n')
    for item in itemlist:
        if len(item.split('=')) == 2:
            key, value = item.split('=')
            if key == "energyAxis":
                return value
    return None


if __name__ == "__main__":
    #IgorPackedFile2Data("D:/and.pxt", True)
    wave = Spectrum("wave", np.arange(5, dtype=np.float64), xscale=np.arange(0, 1, 0.2, dtype=np.float64))
    Data2IgorPackedFile(wave, "D:/abc.pxt")