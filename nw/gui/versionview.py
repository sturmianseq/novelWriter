"""
novelWriter – GUI Version Tree
==============================
GUI class for the main window tree of document versions

File History:
Created: 2021-05-16 [1.4a0]

This file is a part of novelWriter
Copyright 2018–2020, Veronica Berglyd Olsen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import nw
import logging

from time import time
from datetime import datetime

from PyQt5.QtCore import Qt, QSize, pyqtSlot
from PyQt5.QtWidgets import (
    QAction, QHBoxLayout, QLineEdit, QMenu, QPushButton, QWidget, QVBoxLayout, QTreeWidget,
    QTreeWidgetItem, QAbstractItemView, QLabel
)

from nw.core import NWDoc
from nw.enum import nwAlert

logger = logging.getLogger(__name__)


class GuiVersionView(QWidget):

    def __init__(self, theParent):
        QWidget.__init__(self, theParent)

        logger.debug("Initialising GuiVersionView ...")

        self.mainConf   = nw.CONFIG
        self.theParent  = theParent
        self.theTheme   = theParent.theTheme
        self.theProject = theParent.theProject

        # Internal Variables
        self._docHandle = None

        # Build GUI
        # =========

        # Sizes
        hSp = self.mainConf.pxInt(4)
        vSp = self.mainConf.pxInt(6)
        mPx = self.mainConf.pxInt(6)

        # Header
        self.docHeader = QLabel(self.tr("None"))

        hFont = self.docHeader.font()
        hFont.setBold(True)
        hFont.setPointSizeF(1.8*self.theTheme.fontPointSize)
        self.docHeader.setFont(hFont)

        # Version Form
        self.formTitle = QLabel(self.tr("Add New Version"))

        self.versNote = QLineEdit()
        self.versNote.setPlaceholderText(self.tr("Version Note"))
        self.versNote.setMaxLength(200)

        self.versButton = QPushButton("")
        self.versButton.setIcon(self.theTheme.getIcon("add"))
        self.versButton.clicked.connect(self._createPermamentVersion)

        # The Tree
        self.treeView = GuiVersionTree(self)

        # Assemble
        self.inputBox = QHBoxLayout()
        self.inputBox.addWidget(self.versNote, 1)
        self.inputBox.addWidget(self.versButton, 0)
        self.inputBox.setContentsMargins(0, 0, 0, 0)
        self.inputBox.setSpacing(hSp)

        self.topLayout = QVBoxLayout()
        self.topLayout.addWidget(self.docHeader)
        self.topLayout.addSpacing(2*vSp)
        self.topLayout.addWidget(self.formTitle)
        self.topLayout.addLayout(self.inputBox)
        self.topLayout.setContentsMargins(mPx, mPx, mPx, mPx)
        self.topLayout.setSpacing(0)

        self.topWidget = QWidget(self)
        self.topWidget.setLayout(self.topLayout)

        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.topWidget)
        self.outerBox.addWidget(self.treeView)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setSpacing(vSp)

        self.setLayout(self.outerBox)
        self.initWidget()
        self._updateDocument(None)

        logger.debug("GuiVersionView initialisation complete")

        return

    ##
    #  Methods
    ##

    def initWidget(self):
        """Set or update widget settings.
        """
        # Scroll bars
        if self.mainConf.hideVScroll:
            self.treeView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self.treeView.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        if self.mainConf.hideHScroll:
            self.treeView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self.treeView.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        return

    def clearWidget(self):
        """Clear the data of the widget.
        """
        self._docHandle = None
        self.treeView.clearTree()
        self._updateDocument(None)
        return

    def getColumnSizes(self):
        """Return the column widths for the tree columns.
        """
        return [self.treeView.columnWidth(0)]

    ##
    #  Slots
    ##

    @pyqtSlot(str)
    def doUpdateDocument(self, tHandle):
        """The editor's document handle has changed.
        """
        logger.debug("Refreshing version widget with '%s'", tHandle)
        self._updateDocument(tHandle)
        self.treeView.populateTree(tHandle)
        return

    def _createPermamentVersion(self):
        """Create a new version of the current document.
        """
        if self._docHandle is None:
            return False

        self.theParent.saveDocument()
        nwDoc = NWDoc(self.theProject, self._docHandle)
        if not nwDoc.isValid():
            return False

        versNote = self.versNote.text().strip()
        if not versNote:
            self.theParent.makeAlert(self.tr("Please provide a version note."), nwAlert.ERROR)
            return False

        if not nwDoc.savePermanentVersion(versNote):
            self.theParent.makeAlert(self.tr("Failed to save new version."), nwAlert.ERROR)
            return False

        self.treeView.populateTree(self._docHandle)

        return True

    ##
    #  Internal Function
    ##

    def _updateDocument(self, tHandle):
        """Update the document information on the widget
        """
        self._docHandle = tHandle
        self.docHeader.setText(self.tr("None"))

        if tHandle is None:
            return

        nwItem = self.theProject.projTree[tHandle]
        if nwItem is None:
            return

        self.docHeader.setText(nwItem.itemName)

        return

# END Class GuiVersionView


class GuiVersionTree(QTreeWidget):

    C_NOTE = 0
    C_DATE = 1

    def __init__(self, theWidget):
        QTreeWidget.__init__(self, theWidget)

        logger.debug("Initialising GuiVersionTree ...")

        self.mainConf   = nw.CONFIG
        self.theParent  = theWidget.theParent
        self.theTheme   = theWidget.theTheme
        self.theProject = theWidget.theProject

        # Internal Variables
        self._lastBuild = 0
        self._docHandle = None

        # Context Menu
        self.ctxMenu = GuiVersionTreeMenu(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._rightClickMenu)

        # Build GUI
        iPx = self.theTheme.baseIconSize
        self.setIconSize(QSize(iPx, iPx))
        self.setIndentation(iPx)
        self.setColumnCount(2)
        self.setHeaderLabels([self.tr("Version Note"), self.tr("Date")])
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setExpandsOnDoubleClick(False)
        self.setDragEnabled(False)

        treeHeader = self.header()
        treeHeader.setStretchLastSection(True)
        treeHeader.setMinimumSectionSize(iPx + 6)

        # Get user's column width preferences for NAME and COUNT
        treeColWidth = self.mainConf.getVersionColWidths()
        if len(treeColWidth) <= 2:
            for colN, colW in enumerate(treeColWidth):
                self.setColumnWidth(colN, colW)

        # The last column should just auto-scale
        self.resizeColumnToContents(self.C_DATE)

        logger.debug("GuiVersionTree initialisation complete")

        return

    ##
    #  Class Methods
    ##

    def clearTree(self):
        """Clear the GUI content and the related maps.
        """
        self.clear()
        self._lastBuild = 0
        return

    ##
    #  Events
    ##

    def mousePressEvent(self, theEvent):
        """Overload mousePressEvent to clear selection if clicking the
        mouse in a blank area of the tree view, and to load a document
        for viewing if the user middle-clicked.
        """
        QTreeWidget.mousePressEvent(self, theEvent)

        if theEvent.button() == Qt.LeftButton:
            selItem = self.indexAt(theEvent.pos())
            if not selItem.isValid():
                self.clearSelection()

        # elif theEvent.button() == Qt.MiddleButton:
        #     selItem = self.itemAt(theEvent.pos())
        #     if not isinstance(selItem, QTreeWidgetItem):
        #         return

        #     tHandle = self.getSelectedHandle()
        #     if tHandle is None:
        #         return

        #     self.theParent.viewDocument(tHandle)

        return

    ##
    #  Methods
    ##

    def populateTree(self, tHandle):
        """Build the version tree from a given handle.
        """
        self._docHandle = tHandle

        nwItem = self.theProject.projTree[tHandle]
        if nwItem is None:
            return False

        self.clearTree()

        # Session Version
        # ===============

        sessDir = QTreeWidgetItem()
        sessDir.setText(self.C_NOTE, self.tr("Session Version"))
        sessDir.setData(self.C_NOTE, Qt.UserRole, "None")
        sessDir.setIcon(self.C_NOTE, self.theTheme.getIcon("proj_folder"))
        self.addTopLevelItem(sessDir)

        sessTime = datetime.fromtimestamp(self.theProject.projOpened).strftime("%x %X")
        sessNote = self.tr("Current Session")
        sessItem = QTreeWidgetItem()
        if nwItem.sessionBak:
            sessItem.setText(self.C_NOTE, sessNote)
            sessItem.setText(self.C_DATE, sessTime)
            sessItem.setToolTip(self.C_NOTE, sessNote)
            sessItem.setToolTip(self.C_DATE, sessTime)
            sessItem.setIcon(self.C_NOTE, self.theTheme.getIcon("proj_document"))
            sessItem.setData(self.C_NOTE, Qt.UserRole, "Session")
        else:
            sessItem.setText(self.C_NOTE, self.tr("None"))
            sessItem.setData(self.C_NOTE, Qt.UserRole, "None")
            sessItem.setIcon(self.C_NOTE, self.theTheme.getIcon("cross"))

        sessDir.addChild(sessItem)
        sessDir.setExpanded(True)

        # Other Versions
        # ==============

        versDir = QTreeWidgetItem()
        versDir.setText(self.C_NOTE, self.tr("Permanent Versions"))
        versDir.setData(self.C_NOTE, Qt.UserRole, "None")
        versDir.setIcon(self.C_NOTE, self.theTheme.getIcon("proj_folder"))
        self.addTopLevelItem(versDir)

        nwDoc = NWDoc(self.theProject, tHandle)
        versList = nwDoc.listVersions()
        if versList:
            for versName, versDate, versNote in versList:
                versTime = datetime.fromtimestamp(versDate).strftime("%x %X")

                versItem = QTreeWidgetItem()
                versItem.setText(self.C_NOTE, versNote)
                versItem.setText(self.C_DATE, versTime)
                versItem.setToolTip(self.C_NOTE, versNote)
                versItem.setToolTip(self.C_DATE, versTime)
                versItem.setData(self.C_NOTE, Qt.UserRole, versName)
                versItem.setIcon(self.C_NOTE, self.theTheme.getIcon("proj_document"))

                versDir.addChild(versItem)
        else:
            versItem = QTreeWidgetItem()
            versItem.setText(self.C_NOTE, self.tr("None"))
            versItem.setData(self.C_NOTE, Qt.UserRole, "None")
            versItem.setIcon(self.C_NOTE, self.theTheme.getIcon("cross"))
            versDir.addChild(versItem)

        versDir.setExpanded(True)

        self._lastBuild = time()

        return

    ##
    #  Actions
    ##

    def showVersionDocument(self, theVersion):
        """Open a version document in the main document viewer.
        """
        logger.verbose("Viewing document version %s", str(theVersion))
        self.theParent.viewDocument(self._docHandle, tVersion=theVersion)
        return

    def diffVersionDocument(self, theVersion):
        """Open the diff of a version document in the main document
        viewer. The diff is generated against the currently open
        document.
        """
        logger.verbose("Diffing document version %s", str(theVersion))
        return

    def restoreVersionDocument(self, theVersion):
        """Restore a previous version over the currently open document.
        """
        logger.verbose("Restoring document version %s", str(theVersion))
        return

    def deleteVersionDocument(self, theVersion):
        """Delete a version document.
        """
        logger.verbose("Deleting document version %s", str(theVersion))
        return

    ##
    #  Slots
    ##

    @pyqtSlot("QPoint")
    def _rightClickMenu(self, clickPos):
        """The user right clicked an element in the version tree, so we
        open a context menu in-place.
        """
        selItem = self.itemAt(clickPos)
        if isinstance(selItem, QTreeWidgetItem):
            theVersion = selItem.data(self.C_NOTE, Qt.UserRole)
            if theVersion != "None":
                self.ctxMenu.setVersion(theVersion)
                self.ctxMenu.exec_(self.viewport().mapToGlobal(clickPos))

        return

# END Class GuiVersionTree


class GuiVersionTreeMenu(QMenu):

    def __init__(self, theTree):
        QMenu.__init__(self, theTree)

        self._theTree = theTree
        self._theVersion = None

        self.viewVersion = QAction(self.tr("View Version"))
        self.viewVersion.triggered.connect(self._doViewVersion)
        self.addAction(self.viewVersion)

        self.diffVersion = QAction(self.tr("Show Version Diff"))
        self.diffVersion.triggered.connect(self._doDiffVersion)
        self.addAction(self.diffVersion)

        self.restoreVersion = QAction(self.tr("Restore Version"))
        self.restoreVersion.triggered.connect(self._doRestoreVersion)
        self.addAction(self.restoreVersion)

        self.deleteVersion = QAction(self.tr("Delete Version"))
        self.deleteVersion.triggered.connect(self._doDeleteVersion)
        self.addAction(self.deleteVersion)

        return

    def setVersion(self, theVersion):
        """Set the version ID the menu should acto on.
        """
        if theVersion == "None":
            self._theVersion = None
        else:
            self._theVersion = theVersion
        return

    ##
    #  Slots
    ##

    @pyqtSlot()
    def _doViewVersion(self):
        self._theTree.showVersionDocument(self._theVersion)
        return

    @pyqtSlot()
    def _doDiffVersion(self):
        self._theTree.diffVersionDocument(self._theVersion)
        return

    @pyqtSlot()
    def _doRestoreVersion(self):
        self._theTree.restoreVersionDocument(self._theVersion)
        return

    @pyqtSlot()
    def _doDeleteVersion(self):
        self._theTree.deleteVersionDocument(self._theVersion)
        return

# END Class GuiVersionTreeMenu
