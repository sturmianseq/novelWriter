# -*- coding: utf-8 -*-
"""novelWriter GUI Config Editor

 novelWriter – GUI Config Editor
=================================
 Class holding the config dialog

 File History:
 Created: 2019-06-10 [0.1.5]

 This file is a part of novelWriter
 Copyright 2020, Veronica Berglyd Olsen

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see https://www.gnu.org/licenses/.
"""

import logging
import nw

from os import path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QWidget, QTabWidget,
    QDialogButtonBox, QSpinBox, QGroupBox, QComboBox, QMessageBox, QCheckBox,
    QGridLayout, QFontComboBox, QPushButton, QFileDialog, QFormLayout
)

from nw.additions import QSwitch, QConfigLayout
from nw.tools import NWSpellCheck, NWSpellSimple, NWSpellEnchant
from nw.constants import nwAlert, nwQuotes

logger = logging.getLogger(__name__)

class GuiConfigEditor(QDialog):

    def __init__(self, theParent, theProject):
        QDialog.__init__(self, theParent)

        logger.debug("Initialising ConfigEditor ...")

        self.mainConf   = nw.CONFIG
        self.theParent  = theParent
        self.theProject = theProject
        self.outerBox   = QHBoxLayout()
        self.innerBox   = QVBoxLayout()

        self.setWindowTitle("Preferences")
        self.guiDeco = self.theParent.theTheme.loadDecoration("settings",(64,64))

        self.tabGeneral = GuiConfigEditGeneralTab(self.theParent)
        self.tabMain    = GuiConfigEditGeneral(self.theParent)
        self.tabEditor  = GuiConfigEditEditor(self.theParent)

        self.tabWidget = QTabWidget()
        self.tabWidget.setMinimumWidth(600)
        self.tabWidget.addTab(self.tabGeneral, "General")
        self.tabWidget.addTab(self.tabMain, "General")
        self.tabWidget.addTab(self.tabEditor, "Editor")

        self.setLayout(self.outerBox)
        self.outerBox.addWidget(self.guiDeco, 0, Qt.AlignTop)
        self.outerBox.addLayout(self.innerBox)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self._doSave)
        self.buttonBox.rejected.connect(self._doClose)

        self.innerBox.addWidget(self.tabWidget)
        self.innerBox.addWidget(self.buttonBox)

        self.show()

        logger.debug("ConfigEditor initialisation complete")

        return

    ##
    #  Buttons
    ##

    def _doSave(self):

        logger.verbose("ConfigEditor save button clicked")

        validEntries = True
        needsRestart = False

        retA, retB = self.tabGeneral.saveValues()
        validEntries &= retA
        needsRestart |= retB

        retA, retB = self.tabMain.saveValues()
        validEntries &= retA
        needsRestart |= retB

        retA, retB = self.tabEditor.saveValues()
        validEntries &= retA
        needsRestart |= retB

        if needsRestart:
            msgBox = QMessageBox()
            msgBox.information(
                self, "Preferences",
                "Some changes will not be applied until<br>%s has been restarted." % nw.__package__
            )

        if validEntries:
            self.accept()

        return

    def _doClose(self):
        logger.verbose("ConfigEditor close button clicked")
        self.close()
        return

# END Class GuiConfigEditor

class GuiConfigEditGeneralTab(QWidget):

    def __init__(self, theParent):
        QWidget.__init__(self, theParent)

        self.mainConf  = nw.CONFIG
        self.theParent = theParent
        self.theTheme  = theParent.theTheme

        # The Form
        self.mainForm = QConfigLayout()
        self.mainForm.setHelpTextStyle(self.theTheme.helpText)
        self.setLayout(self.mainForm)

        # GUI Settings
        # ============
        self.mainForm.addGroupLabel("GUI")

        ## Select Theme
        self.selectTheme = QComboBox()
        self.selectTheme.setMinimumWidth(200)
        self.theThemes = self.theTheme.listThemes()
        for themeDir, themeName in self.theThemes:
            self.selectTheme.addItem(themeName, themeDir)
        themeIdx = self.selectTheme.findData(self.mainConf.guiTheme)
        if themeIdx != -1:
            self.selectTheme.setCurrentIndex(themeIdx)

        self.mainForm.addRow("Colour theme", self.selectTheme)

        ## Syntax Highlighting
        self.selectSyntax = QComboBox()
        self.selectSyntax.setMinimumWidth(200)
        self.theSyntaxes = self.theTheme.listSyntax()
        for syntaxFile, syntaxName in self.theSyntaxes:
            self.selectSyntax.addItem(syntaxName, syntaxFile)
        syntaxIdx = self.selectSyntax.findData(self.mainConf.guiSyntax)
        if syntaxIdx != -1:
            self.selectSyntax.setCurrentIndex(syntaxIdx)

        self.mainForm.addRow("Syntax highlight theme", self.selectSyntax)

        ## Dark Icons
        self.preferDarkIcons = QSwitch()
        self.preferDarkIcons.setChecked(self.mainConf.guiDark)
        self.mainForm.addRow(
            "Prefer icons for dark backgrounds",
            self.preferDarkIcons,
            "May improve the look of icons on dark themes"
        )

        # AutoSave Settings
        # =================
        self.mainForm.addGroupLabel("Automatic Save")

        self.autoSaveDoc = QSpinBox(self)
        self.autoSaveDoc.setMinimum(5)
        self.autoSaveDoc.setMaximum(600)
        self.autoSaveDoc.setSingleStep(1)
        self.autoSaveDoc.setValue(self.mainConf.autoSaveDoc)
        self.backupPathRow = self.mainForm.addRow(
            "Save interval for the currently open document",
            self.autoSaveDoc,
            theUnit="seconds"
        )

        self.autoSaveProj = QSpinBox(self)
        self.autoSaveProj.setMinimum(5)
        self.autoSaveProj.setMaximum(600)
        self.autoSaveProj.setSingleStep(1)
        self.autoSaveProj.setValue(self.mainConf.autoSaveProj)
        self.backupPathRow = self.mainForm.addRow(
            "Save interval for the currently open project",
            self.autoSaveProj,
            theUnit="seconds"
        )

        # Backup Settings
        # ===============
        self.mainForm.addGroupLabel("Project Backup")

        ## Backup Path
        self.backupPath = self.mainConf.backupPath
        self.backupGetPath = QPushButton(self.theTheme.getIcon("folder"),"Select Folder")
        self.backupGetPath.clicked.connect(self._backupFolder)
        self.backupPathRow = self.mainForm.addRow(
            "Backup storage location",
            self.backupGetPath,
            "Path: %s" % self.backupPath
        )

        ## Run when closing
        self.backupOnClose = QSwitch()
        self.backupOnClose.setChecked(self.mainConf.backupOnClose)
        self.backupOnClose.toggled.connect(self._toggledBackupOnClose)
        self.mainForm.addRow(
            "Run backup when closing project",
            self.backupOnClose,
            "This option can be overridden in project settings"
        )

        ## Ask before backup
        self.askBeforeBackup = QSwitch()
        self.askBeforeBackup.setChecked(self.mainConf.askBeforeBackup)
        self.mainForm.addRow(
            "Ask before running backup",
            self.askBeforeBackup
        )

        return

    def saveValues(self):

        validEntries = True
        needsRestart = False

        guiTheme        = self.selectTheme.currentData()
        guiSyntax       = self.selectSyntax.currentData()
        guiDark         = self.preferDarkIcons.isChecked()
        autoSaveDoc     = self.autoSaveDoc.value()
        autoSaveProj    = self.autoSaveProj.value()
        backupPath      = self.backupPath
        backupOnClose   = self.backupOnClose.isChecked()
        askBeforeBackup = self.askBeforeBackup.isChecked()

        # Check if restart is needed
        needsRestart |= self.mainConf.guiTheme != guiTheme

        self.mainConf.guiTheme        = guiTheme
        self.mainConf.guiSyntax       = guiSyntax
        self.mainConf.guiDark         = guiDark
        self.mainConf.autoSaveDoc     = autoSaveDoc
        self.mainConf.autoSaveProj    = autoSaveProj
        self.mainConf.backupPath      = backupPath
        self.mainConf.backupOnClose   = backupOnClose
        self.mainConf.askBeforeBackup = askBeforeBackup

        self.mainConf.confChanged = True

        return validEntries, needsRestart

    ##
    #  Slots
    ##

    def _backupFolder(self):

        currDir = self.backupPath
        if not path.isdir(currDir):
            currDir = ""

        dlgOpt  = QFileDialog.Options()
        dlgOpt |= QFileDialog.ShowDirsOnly
        dlgOpt |= QFileDialog.DontUseNativeDialog
        newDir = QFileDialog.getExistingDirectory(
            self,"Backup Directory",currDir,options=dlgOpt
        )
        if newDir:
            self.backupPath = newDir
            self.mainForm.setHelpText(self.backupPathRow, "Path: %s" % self.backupPath)
            return True

        return False

    def _toggledBackupOnClose(self, theState):
        """If "backup on close" is disabled, also disable "ask before
        backup".
        """
        if not theState:
            self.askBeforeBackup.setChecked(False)
        return

# END Class GuiConfigEditGeneralTab

class GuiConfigEditGeneral(QWidget):

    def __init__(self, theParent):
        QWidget.__init__(self, theParent)

        self.mainConf  = nw.CONFIG
        self.theParent = theParent
        self.theTheme  = theParent.theTheme
        self.outerBox  = QGridLayout()

        # Spell Checking
        self.spellLang     = QGroupBox("Spell Checker", self)
        self.spellLangForm = QGridLayout(self)
        self.spellLang.setLayout(self.spellLangForm)

        self.spellLangList = QComboBox(self)
        self.spellToolList = QComboBox(self)
        self.spellToolList.addItem("Internal (difflib)",        NWSpellCheck.SP_INTERNAL)
        self.spellToolList.addItem("Spell Enchant (pyenchant)", NWSpellCheck.SP_ENCHANT)
        self.spellToolList.addItem("SymSpell (symspellpy)",     NWSpellCheck.SP_SYMSPELL)

        theModel   = self.spellToolList.model()
        idEnchant  = self.spellToolList.findData(NWSpellCheck.SP_ENCHANT)
        idSymSpell = self.spellToolList.findData(NWSpellCheck.SP_SYMSPELL)
        theModel.item(idEnchant).setEnabled(self.mainConf.hasEnchant)
        theModel.item(idSymSpell).setEnabled(self.mainConf.hasSymSpell)

        self.spellToolList.currentIndexChanged.connect(self._doUpdateSpellTool)
        toolIdx = self.spellToolList.findData(self.mainConf.spellTool)
        if toolIdx != -1:
            self.spellToolList.setCurrentIndex(toolIdx)
        self._doUpdateSpellTool(0)

        self.spellBigDoc = QSpinBox(self)
        self.spellBigDoc.setMinimum(10)
        self.spellBigDoc.setMaximum(10000)
        self.spellBigDoc.setSingleStep(10)
        self.spellBigDoc.setToolTip((
            "Disable spell checking when loading large documents. "
            "Spell checking will only run on paragraphs you edit."
        ))
        self.spellBigDoc.setValue(self.mainConf.bigDocLimit)

        self.spellLangForm.addWidget(QLabel("Provider"),   0, 0)
        self.spellLangForm.addWidget(self.spellToolList,   0, 1, 1, 3)
        self.spellLangForm.addWidget(QLabel("Language"),   1, 0)
        self.spellLangForm.addWidget(self.spellLangList,   1, 1, 1, 3)
        self.spellLangForm.addWidget(QLabel("Size limit"), 2, 0)
        self.spellLangForm.addWidget(self.spellBigDoc,     2, 1)
        self.spellLangForm.addWidget(QLabel("kb"),         2, 2)
        self.spellLangForm.setColumnStretch(4, 1)

        # Assemble
        self.outerBox.addWidget(self.spellLang,  1, 0)
        self.outerBox.setColumnStretch(1, 1)
        self.outerBox.setRowStretch(4, 1)
        self.setLayout(self.outerBox)

        return

    def saveValues(self):

        validEntries = True
        needsRestart = False

        spellTool       = self.spellToolList.currentData()
        spellLanguage   = self.spellLangList.currentData()
        bigDocLimit     = self.spellBigDoc.value()

        self.mainConf.spellTool       = spellTool
        self.mainConf.spellLanguage   = spellLanguage
        self.mainConf.bigDocLimit     = bigDocLimit

        self.mainConf.confChanged = True

        return validEntries, needsRestart

    ##
    #  Internal Functions
    ##

    def _disableComboItem(self, theList, theValue):
        theIdx = theList.findData(theValue)
        theModel = theList.model()
        anItem = theModel.item(1)
        anItem.setFlags(anItem.flags() ^ Qt.ItemIsEnabled)
        return theModel

    def _doUpdateSpellTool(self, currIdx):
        spellTool = self.spellToolList.currentData()
        self._updateLanguageList(spellTool)
        return

    def _updateLanguageList(self, spellTool):
        """Updates the list of available spell checking dictionaries
        available for the selected spell check tool. It will try to
        preserve the language choice, if the language exists in the
        updated list.
        """
        if spellTool == NWSpellCheck.SP_ENCHANT:
            theDict = NWSpellEnchant()
        else:
            theDict = NWSpellSimple()

        self.spellLangList.clear()
        for spTag, spName in theDict.listDictionaries():
            self.spellLangList.addItem(spName, spTag)

        spellIdx = self.spellLangList.findData(self.mainConf.spellLanguage)
        if spellIdx != -1:
            self.spellLangList.setCurrentIndex(spellIdx)

        return

# END Class GuiConfigEditGeneral

class GuiConfigEditEditor(QWidget):

    def __init__(self, theParent):
        QWidget.__init__(self, theParent)

        self.mainConf  = nw.CONFIG
        self.theParent = theParent
        self.outerBox  = QGridLayout()

        # Text Style
        self.textStyle     = QGroupBox("Text Style", self)
        self.textStyleForm = QGridLayout(self)
        self.textStyle.setLayout(self.textStyleForm)

        self.textStyleFont = QFontComboBox()
        self.textStyleFont.setMaximumWidth(250)
        self.textStyleFont.setCurrentFont(QFont(self.mainConf.textFont))

        self.textStyleSize = QSpinBox(self)
        self.textStyleSize.setMinimum(5)
        self.textStyleSize.setMaximum(120)
        self.textStyleSize.setSingleStep(1)
        self.textStyleSize.setValue(self.mainConf.textSize)

        self.textStyleForm.addWidget(QLabel("Font family"), 0, 0)
        self.textStyleForm.addWidget(self.textStyleFont,    0, 1)
        self.textStyleForm.addWidget(QLabel("Size"),        0, 2)
        self.textStyleForm.addWidget(self.textStyleSize,    0, 3)
        self.textStyleForm.setColumnStretch(4, 1)

        # Text Flow
        self.textFlow     = QGroupBox("Text Flow", self)
        self.textFlowForm = QGridLayout(self)
        self.textFlow.setLayout(self.textFlowForm)

        self.textFlowFixed = QCheckBox("Max text width",self)
        self.textFlowFixed.setToolTip("Maximum width of the text.")
        self.textFlowFixed.setChecked(self.mainConf.textFixedW)

        self.textFlowMax = QSpinBox(self)
        self.textFlowMax.setMinimum(300)
        self.textFlowMax.setMaximum(10000)
        self.textFlowMax.setSingleStep(10)
        self.textFlowMax.setValue(self.mainConf.textWidth)

        self.textFlowJustify = QCheckBox("Justify text",self)
        self.textFlowJustify.setToolTip("Justify text in main document editor.")
        self.textFlowJustify.setChecked(self.mainConf.doJustify)

        self.textFlowForm.addWidget(self.textFlowFixed,   0, 0)
        self.textFlowForm.addWidget(self.textFlowMax,     0, 1)
        self.textFlowForm.addWidget(QLabel("px"),         0, 2)
        self.textFlowForm.addWidget(self.textFlowJustify, 1, 0)
        self.textFlowForm.setColumnStretch(4, 1)

        # Text Margins
        self.textMargin     = QGroupBox("Margins", self)
        self.textMarginForm = QGridLayout(self)
        self.textMargin.setLayout(self.textMarginForm)

        self.textMarginDoc = QSpinBox(self)
        self.textMarginDoc.setMinimum(0)
        self.textMarginDoc.setMaximum(2000)
        self.textMarginDoc.setSingleStep(1)
        self.textMarginDoc.setValue(self.mainConf.textMargin)

        self.textMarginTab = QSpinBox(self)
        self.textMarginTab.setMinimum(0)
        self.textMarginTab.setMaximum(200)
        self.textMarginTab.setSingleStep(1)
        self.textMarginTab.setValue(self.mainConf.tabWidth)
        self.textMarginTab.setToolTip("Requires Qt 5.9 or later.")

        self.textMarginForm.addWidget(QLabel("Document"),   0, 0)
        self.textMarginForm.addWidget(self.textMarginDoc,   0, 1)
        self.textMarginForm.addWidget(QLabel("px"),         0, 2)
        self.textMarginForm.addWidget(QLabel("Tab width"),  2, 0)
        self.textMarginForm.addWidget(self.textMarginTab,   2, 1)
        self.textMarginForm.addWidget(QLabel("px"),         2, 2)
        self.textMarginForm.setColumnStretch(4, 1)

        # Zen Mode
        self.zenMode     = QGroupBox("Zen Mode", self)
        self.zenModeForm = QGridLayout(self)
        self.zenMode.setLayout(self.zenModeForm)

        self.zenDocWidth = QSpinBox(self)
        self.zenDocWidth.setMinimum(300)
        self.zenDocWidth.setMaximum(10000)
        self.zenDocWidth.setSingleStep(10)
        self.zenDocWidth.setValue(self.mainConf.zenWidth)

        self.zenModeForm.addWidget(QLabel("Document width"), 0, 0)
        self.zenModeForm.addWidget(self.zenDocWidth,         0, 1)
        self.zenModeForm.addWidget(QLabel("px"),             0, 2)
        self.zenModeForm.setColumnStretch(3, 1)

        # Automatic Features
        self.autoReplace     = QGroupBox("Automatic Features", self)
        self.autoReplaceForm = QGridLayout(self)
        self.autoReplace.setLayout(self.autoReplaceForm)

        self.autoSelect = QCheckBox(self)
        self.autoSelect.setToolTip("Auto-select word under cursor when applying formatting.")
        self.autoSelect.setChecked(self.mainConf.autoSelect)

        self.autoReplaceMain = QCheckBox(self)
        self.autoReplaceMain.setToolTip("Auto-replace text as you type.")
        self.autoReplaceMain.setChecked(self.mainConf.doReplace)

        self.autoReplaceSQ = QCheckBox(self)
        self.autoReplaceSQ.setToolTip("Auto-replace single quotes.")
        self.autoReplaceSQ.setChecked(self.mainConf.doReplaceSQuote)

        self.autoReplaceDQ = QCheckBox(self)
        self.autoReplaceDQ.setToolTip("Auto-replace double quotes.")
        self.autoReplaceDQ.setChecked(self.mainConf.doReplaceDQuote)

        self.autoReplaceDash = QCheckBox(self)
        self.autoReplaceDash.setToolTip(
            "Auto-replace double and triple hyphens with short and long dash."
        )
        self.autoReplaceDash.setChecked(self.mainConf.doReplaceDash)

        self.autoReplaceDots = QCheckBox(self)
        self.autoReplaceDots.setToolTip("Auto-replace three dots with ellipsis.")
        self.autoReplaceDots.setChecked(self.mainConf.doReplaceDots)

        self.autoReplaceForm.addWidget(QLabel("Auto-select text"),          0, 0)
        self.autoReplaceForm.addWidget(self.autoSelect,                     0, 1)
        self.autoReplaceForm.addWidget(QLabel("Auto-replace:"),             1, 0)
        self.autoReplaceForm.addWidget(self.autoReplaceMain,                1, 1)
        self.autoReplaceForm.addWidget(QLabel("\u2192 Single quotes"),      2, 0)
        self.autoReplaceForm.addWidget(self.autoReplaceSQ,                  2, 1)
        self.autoReplaceForm.addWidget(QLabel("\u2192 Double quotes"),      3, 0)
        self.autoReplaceForm.addWidget(self.autoReplaceDQ,                  3, 1)
        self.autoReplaceForm.addWidget(QLabel("\u2192 Hyphens with dash"),  4, 0)
        self.autoReplaceForm.addWidget(self.autoReplaceDash,                4, 1)
        self.autoReplaceForm.addWidget(QLabel("\u2192 Dots with ellipsis"), 5, 0)
        self.autoReplaceForm.addWidget(self.autoReplaceDots,                5, 1)
        self.autoReplaceForm.setColumnStretch(2, 1)
        self.autoReplaceForm.setRowStretch(6, 1)

        # Quote Style
        self.quoteStyle     = QGroupBox("Quotation Style", self)
        self.quoteStyleForm = QGridLayout(self)
        self.quoteStyle.setLayout(self.quoteStyleForm)

        self.quoteSingleStyleO = QLineEdit()
        self.quoteSingleStyleO.setMaxLength(1)
        self.quoteSingleStyleO.setFixedWidth(30)
        self.quoteSingleStyleO.setAlignment(Qt.AlignCenter)
        self.quoteSingleStyleO.setText(self.mainConf.fmtSingleQuotes[0])

        self.quoteSingleStyleC = QLineEdit()
        self.quoteSingleStyleC.setMaxLength(1)
        self.quoteSingleStyleC.setFixedWidth(30)
        self.quoteSingleStyleC.setAlignment(Qt.AlignCenter)
        self.quoteSingleStyleC.setText(self.mainConf.fmtSingleQuotes[1])

        self.quoteDoubleStyleO = QLineEdit()
        self.quoteDoubleStyleO.setMaxLength(1)
        self.quoteDoubleStyleO.setFixedWidth(30)
        self.quoteDoubleStyleO.setAlignment(Qt.AlignCenter)
        self.quoteDoubleStyleO.setText(self.mainConf.fmtDoubleQuotes[0])

        self.quoteDoubleStyleC = QLineEdit()
        self.quoteDoubleStyleC.setMaxLength(1)
        self.quoteDoubleStyleC.setFixedWidth(30)
        self.quoteDoubleStyleC.setAlignment(Qt.AlignCenter)
        self.quoteDoubleStyleC.setText(self.mainConf.fmtDoubleQuotes[1])

        self.quoteStyleForm.addWidget(QLabel("Single Quotes"), 0, 0, 1, 3)
        self.quoteStyleForm.addWidget(QLabel("Open"),          1, 0)
        self.quoteStyleForm.addWidget(self.quoteSingleStyleO,  1, 1)
        self.quoteStyleForm.addWidget(QLabel("Close"),         1, 2)
        self.quoteStyleForm.addWidget(self.quoteSingleStyleC,  1, 3)
        self.quoteStyleForm.addWidget(QLabel("Double Quotes"), 2, 0, 1, 3)
        self.quoteStyleForm.addWidget(QLabel("Open"),          3, 0)
        self.quoteStyleForm.addWidget(self.quoteDoubleStyleO,  3, 1)
        self.quoteStyleForm.addWidget(QLabel("Close"),         3, 2)
        self.quoteStyleForm.addWidget(self.quoteDoubleStyleC,  3, 3)
        self.quoteStyleForm.setColumnStretch(4, 1)
        self.quoteStyleForm.setRowStretch(4, 1)

        # Writing Guides
        self.showGuides     = QGroupBox("Writing Guides", self)
        self.showGuidesForm = QGridLayout(self)
        self.showGuides.setLayout(self.showGuidesForm)

        self.showTabsNSpaces = QCheckBox("Show tabs and spaces",self)
        self.showTabsNSpaces.setChecked(self.mainConf.showTabsNSpaces)

        self.showLineEndings = QCheckBox("Show line endings",self)
        self.showLineEndings.setChecked(self.mainConf.showLineEndings)

        self.showGuidesForm.addWidget(self.showTabsNSpaces, 0, 0)
        self.showGuidesForm.addWidget(self.showLineEndings, 1, 0)

        # Assemble
        self.outerBox.addWidget(self.textStyle,   0, 0, 1, 2)
        self.outerBox.addWidget(self.textFlow,    1, 0)
        self.outerBox.addWidget(self.textMargin,  1, 1)
        self.outerBox.addWidget(self.zenMode,     2, 0)
        self.outerBox.addWidget(self.autoReplace, 3, 0, 2, 1)
        self.outerBox.addWidget(self.quoteStyle,  2, 1, 2, 1)
        self.outerBox.addWidget(self.showGuides,  4, 1)
        self.outerBox.setColumnStretch(2, 1)
        self.outerBox.setRowStretch(5, 1)
        self.setLayout(self.outerBox)

        return

    def saveValues(self):

        validEntries = True

        textFont = self.textStyleFont.currentFont().family()
        textSize = self.textStyleSize.value()

        self.mainConf.textFont = textFont
        self.mainConf.textSize = textSize

        textWidth  = self.textFlowMax.value()
        textFixedW = self.textFlowFixed.isChecked()
        doJustify  = self.textFlowJustify.isChecked()

        self.mainConf.textWidth  = textWidth
        self.mainConf.textFixedW = textFixedW
        self.mainConf.doJustify  = doJustify

        zenWidth = self.zenDocWidth.value()

        self.mainConf.zenWidth = zenWidth

        textMargin = self.textMarginDoc.value()
        tabWidth   = self.textMarginTab.value()

        self.mainConf.textMargin = textMargin
        self.mainConf.tabWidth   = tabWidth

        autoSelect      = self.autoSelect.isChecked()
        doReplace       = self.autoReplaceMain.isChecked()
        doReplaceSQuote = self.autoReplaceSQ.isChecked()
        doReplaceDQuote = self.autoReplaceDQ.isChecked()
        doReplaceDash   = self.autoReplaceDash.isChecked()
        doReplaceDots   = self.autoReplaceDash.isChecked()

        self.mainConf.autoSelect      = autoSelect
        self.mainConf.doReplace       = doReplace
        self.mainConf.doReplaceSQuote = doReplaceSQuote
        self.mainConf.doReplaceDQuote = doReplaceDQuote
        self.mainConf.doReplaceDash   = doReplaceDash
        self.mainConf.doReplaceDots   = doReplaceDots

        fmtSingleQuotesO = self.quoteSingleStyleO.text()
        fmtSingleQuotesC = self.quoteSingleStyleC.text()
        fmtDoubleQuotesO = self.quoteDoubleStyleO.text()
        fmtDoubleQuotesC = self.quoteDoubleStyleC.text()

        if self._checkQuoteSymbol(fmtSingleQuotesO):
            self.mainConf.fmtSingleQuotes[0] = fmtSingleQuotesO
        else:
            self.theParent.makeAlert(
                "Invalid quote symbol: %s" % fmtSingleQuotesO, nwAlert.ERROR
            )
            validEntries = False

        if self._checkQuoteSymbol(fmtSingleQuotesC):
            self.mainConf.fmtSingleQuotes[1] = fmtSingleQuotesC
        else:
            self.theParent.makeAlert(
                "Invalid quote symbol: %s" % fmtSingleQuotesC, nwAlert.ERROR
            )
            validEntries = False

        if self._checkQuoteSymbol(fmtDoubleQuotesO):
            self.mainConf.fmtDoubleQuotes[0] = fmtDoubleQuotesO
        else:
            self.theParent.makeAlert(
                "Invalid quote symbol: %s" % fmtDoubleQuotesO, nwAlert.ERROR
            )
            validEntries = False

        if self._checkQuoteSymbol(fmtDoubleQuotesC):
            self.mainConf.fmtDoubleQuotes[1] = fmtDoubleQuotesC
        else:
            self.theParent.makeAlert(
                "Invalid quote symbol: %s" % fmtDoubleQuotesC, nwAlert.ERROR
            )
            validEntries = False

        showTabsNSpaces = self.showTabsNSpaces.isChecked()
        showLineEndings = self.showLineEndings.isChecked()

        self.mainConf.showTabsNSpaces = showTabsNSpaces
        self.mainConf.showLineEndings = showLineEndings

        self.mainConf.confChanged = True

        return validEntries, False

    ##
    #  Internal Functions
    ##

    def _checkQuoteSymbol(self, toCheck):
        if len(toCheck) != 1:
            return False
        if toCheck in nwQuotes.SYMBOLS:
            return True
        return False

# END Class GuiConfigEditEditor
