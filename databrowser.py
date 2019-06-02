'''
Data Browser Module
'''

from PyQt5.QtWidgets import (QWidget, QMenu, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem, 
QAbstractItemView, QHeaderView, QStyleFactory, QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout)
from PyQt5.QtGui import QFont, QColor, QCursor, QBrush, QIcon
from PyQt5.QtCore import Qt, QSize, QTimer
import copy


class DataBrowser(QWidget):
    def __init__(self, Win):
        super(DataBrowser, self).__init__()

        #MainWindow
        self.Win = Win

        #Data List
        self.DataList = DataList(self)

        #Info List
        self.InfoList = InfoList(self)

        #Layout
        self.box = QVBoxLayout()
        self.box.addWidget(self.DataList, 70)
        self.box.addWidget(self.InfoList, 30)
        self.setLayout(self.box)

        self.minWidth = 250
        self.setMinimumWidth(self.minWidth)


class DataList(QTreeWidget):
    def __init__(self, Browser):
        super(DataList, self).__init__(size=QSize(100, 100))

        self.Browser = Browser
        self.noteWin = NoteWin()
        self.SelectionModeFlag = True  # True for single-selection, False for multi-selection

        #Property
        self.setColumnCount(1)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAnimated(True)

        #header item
        header = self.header()
        header.setStyleSheet("QHeaderView::section {border-top:0px solid #D8D8D8;border-left:0px solid #D8D8D8;border-right:0px solid #D8D8D8;border-bottom: 1px solid #D8D8D8;background-color:white;padding:4px;color: rgb(79,93,115);}")
        headeritem = self.headerItem()
        font = QFont("Arial Rounded MT Bold")
        font.setPointSize(13)
        font.setBold(True)
        headeritem.setFont(0, font)
        headeritem.setText(0, "Data Browser")
        headeritem.setTextAlignment(0, Qt.AlignVCenter | Qt.AlignHCenter)

        #Data item
        font = QFont("Arial Rounded MT Bold")
        font.setPointSize(11)
        font.setBold(True)
        brush = QBrush()
        brush.setColor(QColor(79,93,115))
        self.oneDlist = DataItem(self, "1D Data", True)
        self.oneDlist.setFlags(self.oneDlist.flags() ^ Qt.ItemIsSelectable)
        self.oneDlist.setFont(0, font)
        self.oneDlist.setForeground(0, brush)
        self.oneDlist.setIcon(0, QIcon("./image/1D.ico"))
        self.twoDlist = DataItem(self, "2D Data", True)
        self.twoDlist.setFlags(self.twoDlist.flags() ^ Qt.ItemIsSelectable)
        self.twoDlist.setFont(0, font)
        self.twoDlist.setForeground(0, brush)
        self.twoDlist.setIcon(0, QIcon("./image/2D.ico"))
        self.threeDlist = DataItem(self, "3D Data", True)
        self.threeDlist.setFlags(self.threeDlist.flags() ^ Qt.ItemIsSelectable)
        self.threeDlist.setFont(0, font)
        self.threeDlist.setForeground(0, brush)
        self.threeDlist.setIcon(0, QIcon("./image/3D.ico"))
        self.fourDlist = DataItem(self, "4D Data", True)
        self.fourDlist.setFlags(self.fourDlist.flags() ^ Qt.ItemIsSelectable)
        self.fourDlist.setFont(0, font)
        self.fourDlist.setForeground(0, brush)
        self.fourDlist.setIcon(0, QIcon("./image/4D.ico"))
        self.SpecList = (self.oneDlist, self.twoDlist, self.threeDlist, self.fourDlist)

        #for key event
        self.setFocusPolicy(Qt.ClickFocus)

        #Set Context Menu
        self.contextMenu = QMenu(self)
        delAction = self.contextMenu.addAction("Delete")
        delAction.setIcon(QIcon("./image/delete.ico"))     
        delAction.triggered.connect(self.delDataItem)
        renameAction = self.contextMenu.addAction("Rename")
        renameAction.setIcon(QIcon("./image/rename.ico"))     
        renameAction.triggered.connect(self.renameItem)
        copyAction = self.contextMenu.addAction("Copy")
        copyAction.setIcon(QIcon("./image/copy.ico"))     
        copyAction.triggered.connect(self.copyItem)
        noteAction = self.contextMenu.addAction("Note")
        noteAction.setIcon(QIcon("./image/note.ico"))
        noteAction.triggered.connect(self.showNote)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        #Signal to Slot
        self.itemSelectionChanged.connect(self.OnSelection_wrap)
    
    def showContextMenu(self, pos): 
        if self.itemAt(pos) and self.itemAt(pos).parent():
            self.contextMenu.move(QCursor.pos())
            self.contextMenu.show()

    def OnSelection_wrap(self):
        #This slot is used to avoiding some unexpected signal from other action like delete.
        QTimer.singleShot(10, lambda: self.OnSelection())
    
    def OnSelection(self):
        current_item = self.currentItem()
        if  current_item is None: # No selection
            self.Browser.InfoList.setRowCount(0)
            self.Browser.Win.setData(None)
            self.Browser.Win.exportAct.setEnabled(False)
        elif current_item.isFather:  # click top-level item
            self.Browser.InfoList.setRowCount(0)
            self.Browser.Win.setData(None)
            self.Browser.Win.exportAct.setEnabled(False)
        else:
            if self.SelectionModeFlag: #single selection 
                currentdata = current_item.Data
                self.Browser.InfoList.setProperty(currentdata.property)
                self.Browser.Win.setData(currentdata)
                self.Browser.Win.exportAct.setEnabled(True)
            elif self.SelectionModeFlag: #multiple selection
                self.Browser.Win.exportAct.setEnabled(False)

    def addDataItem(self, data):
        dim = data.dims
        itemtoadd = DataItem(self.SpecList[dim-1], data.name, False)
        itemtoadd.setFont(0, QFont("Arial", 10))
        colorlist = [QColor(0,0,0), QColor(80,180,0), QColor(0,150,210), QColor(128,0,210)]
        itemtoadd.setForeground(0, QBrush(colorlist[dim-1]))
        itemtoadd.setItemData(data)
        self.expandItem(self.SpecList[dim-1])
    
    def delDataItem(self):
        if len(self.selectedItems()) > 0:
            for item in self.selectedItems():
                self.noteWin.close()
                index = self.itemIndex(item)
                item.parent().takeChild(index)

    def renameItem(self):
        current_item = self.currentItem()
        if not current_item.isFather and not current_item is None:
            current_item.setFlags(current_item.flags() | Qt.ItemIsEditable)
            self.editItem(current_item, 0)
            current_item.setFlags(current_item.flags() ^ Qt.ItemIsEditable)
            lineEditor = self.itemWidget(current_item, 0)
            lineEditor.selectAll()
            lineEditor.editingFinished.connect(self.setDataName)

    def setDataName(self):
        self.currentItem().Data.name = self.currentItem().text(0)

    def copyItem(self):
        current_item = self.currentItem()
        if not current_item.isFather and not current_item is None:
            self.addDataItem(copy.deepcopy(current_item.Data))

    def showNote(self):
        self.noteWin.setItem(self.currentItem())
        self.noteWin.clear()
        self.noteWin.setNote()
        self.noteWin.show()

    def itemIndex(self, item):
        if not item.isFather:
            fatheritem = item.parent()
            index = fatheritem.indexOfChild(item)
        return index

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete:
            self.delDataItem()
        elif e.key() == Qt.Key_F2:
            self.renameItem()


class InfoList(QTableWidget):
    def __init__(self, Browser):
        super(InfoList, self).__init__(size=QSize(100, 100))

        self.Browser = Browser

        self.setRowCount(0)
        self.setColumnCount(2)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setWordWrap(False)
        #self.setStyle(QStyleFactory.create('Fusion'))

        #header
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        headeritem1 = QTableWidgetItem()
        headeritem1.setText("Property")
        headeritem1.setFont(font)
        self.setHorizontalHeaderItem(0, headeritem1)
        headeritem2 = QTableWidgetItem()
        headeritem2.setText("Value")
        headeritem2.setFont(font)
        self.setHorizontalHeaderItem(1, headeritem2)
        self.verticalHeader().hide()
        header = self.horizontalHeader()
        style = "::section {border-top:0px solid #D8D8D8;border-left:0px solid #D8D8D8;border-right:1px solid #D8D8D8;border-bottom: 1px solid #D8D8D8;background-color:white;padding:4px;color: rgb(79,93,115)}"
        header.setStyleSheet(style)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

    def setProperty(self, dataproperty):
        self.setRowCount(len(dataproperty))
        for i, (key, val) in zip(range(len(dataproperty)), dataproperty.items()):
            proitem = QTableWidgetItem()
            valitem = QTableWidgetItem()
            proitem.setText(key)
            valitem.setText(val)
            self.setItem(i, 0, proitem)
            self.setItem(i, 1, valitem)


class DataItem(QTreeWidgetItem):
    def __init__(self, parent, name, isFather):
        super(DataItem, self).__init__(parent, [name])
        self.isFather = isFather
        self.Data = None

    def setItemData(self, data):
        self.Data = data


class NoteWin(QWidget):
    def __init__(self, parent=None, treeItem=None):
        super(NoteWin, self).__init__(parent=parent)
        self.item = treeItem
        self.setWindowIcon(QIcon("./image/note.ico"))
        self.setWindowTitle("Note")

        self.note = QTextEdit()

        self.SaveButton = QPushButton("Save")
        self.SaveButton.clicked.connect(self.OnSave)
        self.CancelButton = QPushButton("Cancel")
        self.CancelButton.clicked.connect(self.close)
        hbox_button = QHBoxLayout()
        hbox_button.addStretch(1)
        hbox_button.addWidget(self.SaveButton)
        hbox_button.addWidget(self.CancelButton)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.note)
        vbox.addLayout(hbox_button)
        self.setLayout(vbox)

    def OnSave(self):
        if self.item is not None:
            self.item.Data.note = self.note.toPlainText()
        self.close()

    def setItem(self, item):
        self.item = item

    def setNote(self):
        if self.item is not None:
            self.note.setPlainText(self.item.Data.note)

    def clear(self):
        self.note.clear()