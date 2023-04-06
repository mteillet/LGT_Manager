# LGTtweaker_gui.py
import json
import os
import re
import math

import nuke
from PySide2 import QtCore, QtGui, QtWidgets


class SelectLpePanel(QtWidgets.QWidget):
    def __init__(self):
        super(SelectLpePanel, self).__init__()
        self.setWindowTitle("LGT Tweaker")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.node = nuke.selectedNode()

        # Reading the group node in order to build the interface
        self.lightDict = self.getInfosFromGroup()

        # Uncomment for debug purposes
        # Print informations got from the lightDict parsing
        '''
        for key in self.lightDict:
            print("{} --> {}".format(key, self.lightDict[key]))
        '''

        # self.setStyleSheet("color: white; background-color: rgb(11,11,11)")

        ###############
        ##  Widgets  ##
        ###############

        # SearchBoxText
        self.searchBox = QtWidgets.QLineEdit("Filter Lights")
        self.searchBox.returnPressed.connect(self.filterLights)

        self.lightLayouts = []
        self.mainWidget = QtWidgets.QWidget()
        self.lightSettings = {}
        self.lightClicked = {}
        # Building one Layout per light using the lightDict
        for key in self.lightDict:
            self.lightSettings[key] = {}
            currentLightLayout = QtWidgets.QVBoxLayout()
            currentTitleLayout = QtWidgets.QHBoxLayout()
            currentExpLayout = QtWidgets.QHBoxLayout()
            currentColorLayout = QtWidgets.QHBoxLayout()
            currentLineLayout = QtWidgets.QVBoxLayout()
            # Setting title
            title = QtWidgets.QCheckBox(key)
            title.stateChanged.connect(self.checkboxClicked)
            font = QtGui.QFont()
            font.setBold(True)
            title.setFont(font)
            self.lightSettings[key]["hide"] = QtWidgets.QPushButton("Not Use")
            self.lightSettings[key]["hide"].setCheckable(True)
            self.getHideValue(key)
            self.lightSettings[key]["hide"].clicked.connect(self.hideClicked)
            self.lightSettings[key]["solo"] = QtWidgets.QPushButton("Solo")
            self.lightSettings[key]["solo"].setCheckable(True)
            self.lightSettings[key]["solo"].clicked.connect(self.soloClicked)
            self.lightSettings[key]["Reset"] = QtWidgets.QPushButton("Reset")
            #self.lightSettings[key]["Reset"].setStyleSheet("background-color : black")
            self.lightSettings[key]["Reset"].clicked.connect(self.resetClicked)
            currentTitleLayout.addWidget(title)
            #currentTitleLayout.addStretch()
            currentTitleLayout.addWidget(self.lightSettings[key]["hide"])
            currentTitleLayout.addWidget(self.lightSettings[key]["solo"])
            currentTitleLayout.addWidget(self.lightSettings[key]["Reset"])
            # Setting Exposure
            exposure = self.getExpValue(key)
            self.lightSettings[key]["expLabel"] = QtWidgets.QLabel("Exposure:")
            self.lightSettings[key]["expSlider"] = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self.lightSettings[key]["expSpin"] = QtWidgets.QDoubleSpinBox()
            self.lightSettings[key]["expSpin"].setMinimum(-50)
            self.lightSettings[key]["expSpin"].setMaximum(50)
            self.lightSettings[key]["expSpin"].valueChanged.connect(self.expSpinChanged)
            self.lightSettings[key]["expSpin"].setValue(exposure)
            self.lightSettings[key]["expSlider"].setMinimum(-1000)
            self.lightSettings[key]["expSlider"].setMaximum(1000)
            self.lightSettings[key]["expSlider"].setSingleStep(0.1)
            self.lightSettings[key]["expSlider"].setValue(exposure*100)
            self.lightSettings[key]["expSlider"].valueChanged.connect(self.expSliderChanged)
            currentExpLayout.addWidget(self.lightSettings[key]["expLabel"])
            currentExpLayout.addWidget(self.lightSettings[key]["expSlider"])
            currentExpLayout.addWidget(self.lightSettings[key]["expSpin"])
            # Setting Color
            color = self.getColorValue(key)
            self.lightSettings[key]["colorLabel"] = QtWidgets.QLabel("Color:")
            self.lightSettings[key]["colorR"] = QtWidgets.QDoubleSpinBox()
            self.lightSettings[key]["colorR"].setSingleStep(0.05)
            self.lightSettings[key]["colorR"].valueChanged.connect(self.colorChanged)
            self.lightSettings[key]["colorR"].setValue(color[0])
            self.lightSettings[key]["colorG"] = QtWidgets.QDoubleSpinBox()
            self.lightSettings[key]["colorG"].valueChanged.connect(self.colorChanged)
            self.lightSettings[key]["colorG"].setValue(color[1])
            self.lightSettings[key]["colorG"].setSingleStep(0.05)
            self.lightSettings[key]["colorB"] = QtWidgets.QDoubleSpinBox()
            self.lightSettings[key]["colorB"].valueChanged.connect(self.colorChanged)
            self.lightSettings[key]["colorB"].setValue(color[2])
            self.lightSettings[key]["colorB"].setSingleStep(0.05)
            self.lightSettings[key]["colorPicker"] = QtWidgets.QPushButton("Pick")
            self.lightSettings[key]["colorPicker"].clicked.connect(self.pickColor)
            # Actual Layout
            currentColorLayout.addWidget(self.lightSettings[key]["colorLabel"])
            #currentColorLayout.addStretch()
            currentColorLayout.addWidget(self.lightSettings[key]["colorR"])
            currentColorLayout.addWidget(self.lightSettings[key]["colorG"])
            currentColorLayout.addWidget(self.lightSettings[key]["colorB"])
            currentColorLayout.addWidget(self.lightSettings[key]["colorPicker"])

            # Line separator
            Line = (QLine())
            currentLineLayout.addWidget(Line)

            # Layout
            currentLightLayout.addLayout(currentTitleLayout)
            currentLightLayout.addLayout(currentExpLayout)
            currentLightLayout.addLayout(currentColorLayout)
            currentLightLayout.addLayout(currentLineLayout)
            #currentLightLayout.addStretch()
            self.lightLayouts.append(currentLightLayout)

        # Lower Bar
        self.resetAll = QtWidgets.QPushButton("Reset All Lights")
        self.resetAll.clicked.connect(self.resetAllClicked)
        self.updateAll = QtWidgets.QPushButton("Fetch New Lights")
        self.export = QtWidgets.QPushButton("Export To Maya")
        self.export.clicked.connect(self.exportClicked)

        ##############
        ##  Layout  ##
        ##############
        layout = QtWidgets.QVBoxLayout()

        # Layout Upper Bar
        upperBarLayout = QtWidgets.QHBoxLayout()
        upperBarLayout.addWidget(self.searchBox)

        # Layout Lower Bar
        lowerBarLayout = QtWidgets.QHBoxLayout()
        lowerBarLayout.addWidget(self.resetAll)
        lowerBarLayout.addWidget(self.updateAll)
        lowerBarLayout.addStretch()
        lowerBarLayout.addWidget(self.export)

        # Add individual layout to the main layout
        layout.addLayout(upperBarLayout)
        self.allLightsLayout = QtWidgets.QVBoxLayout()
        for i in self.lightLayouts:
            self.allLightsLayout.addLayout(i)
        self.mainWidget.setLayout(self.allLightsLayout)
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self.mainWidget)
        layout.addWidget(scrollArea)
        layout.addLayout(lowerBarLayout)

        self.setLayout(layout)


        '''
        for i in self.lightSettings:
            print(i)
            print(self.lightSettings[i])
        '''

    ###############
    ##  BACKEND  ##
    ###############
    def getInfosFromGroup(self):
        '''
        Gets and returns a dict containing the nodes concerning each light
        dir[light] = {merge, exposure, color}
        '''
        print("Getting what is in the group node")

        lightDict = {}

        # Fetching the light names
        for node in self.node.nodes():

            # Creating an entry in the lightDict for every light built in the node
            # EXP_
            if node["label"].getValue().startswith("RGBA_"):
                lightName = re.sub("^RGBA_", "", node["label"].getValue())
                # Avoid creating duplicate entry for lights in the dict
                if lightName not in lightDict:
                    lightDict[lightName] = {}

        # Fetching other nodes for the light Dict
        # MRG_EXP_RGBA_
        toStrip = {
            "MRG_": "merge",
            "EXP_": "exposure",
        }
        for node in self.node.nodes():
            label = node["label"].getValue()
            if label.startswith("MRG_"):
                mergeLabel = (label)
                lightDict[mergeLabel[13:]]["merge"] = node
            if label.startswith("EXP_"):
                expLabel = (label)
                lightDict[expLabel[9:]]["exposure"] = node

        return(lightDict)


    def getInWhichKey(self, widget, param):
        '''
        Finds in which light category the widget is located
        Returns the light key associated
        '''
        for key in self.lightSettings:
            if self.lightSettings[key][param] == widget:
                return(key)

    def pickColor(self):
        '''
        When a color is picked, adjust the color swatch on the picker button
        and update the RGB values on the corresponding spinBoxes
        '''
        key = self.getInWhichKey(self.sender(),"colorPicker")
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            colorF = [color.red() / 255, color.green() / 255, color.blue() / 255]
            # Updating the spinBoxes Values
            self.lightSettings[key]["colorR"].setValue(colorF[0])
            self.lightSettings[key]["colorG"].setValue(colorF[1])
            self.lightSettings[key]["colorB"].setValue(colorF[2])

            # Changing the sender button and the text to the chosen color
            if colorF != [1.0,1.0,1.0]:
                styleSheetColor = ("color: rgb({},{},{})".format(255,85,0))
            else:
                styleSheetColor = ("")
            self.lightSettings[key]["colorLabel"].setStyleSheet(styleSheetColor)
            self.updateColor(key)

    def colorChanged(self):
        '''
        When one of the RGB values are changed, update the colors and swatches
        '''
        key = self.getInWhichKey(self.sender(), "colorR")
        if not key:
            key = self.getInWhichKey(self.sender(), "colorG")
        if not key:
            key = self.getInWhichKey(self.sender(), "colorB")

        r = self.lightSettings[key]["colorR"].value()
        try:
            g = self.lightSettings[key]["colorG"].value()
        except KeyError:
            g = 1.0
        try:
            b = self.lightSettings[key]["colorB"].value()
        except KeyError:
            b = 1.0

        # Changing the sender button and the text to the chosen color
        if [r,g,b] != [1.0,1.0,1.0]:
            styleSheetColor = ("color: rgb({},{},{})".format(255,85,0))
        else:
            styleSheetColor = ("")
        self.lightSettings[key]["colorLabel"].setStyleSheet(styleSheetColor)
        self.updateColor(key)

    def updateColor(self, light):
        '''
        Update the actual exposure color node
        '''
        try :
            mult = [self.lightSettings[light]["colorR"].value(), self.lightSettings[light]["colorG"].value(), self.lightSettings[light]["colorB"].value(), 1.0]
        except KeyError:
            mult = [1.0,1.0,1.0,1.0]
        for node in self.node.nodes():
            if node["label"].getValue() == "COL_RGBA_{}".format(light):
                node["multiply"].setValue(mult)

    def getColorValue(self, light):
        '''
        Init for correct Mult Color at the build of the UI
        '''
        for node in self.node.nodes():
            if node["label"].getValue() == "COL_RGBA_{}".format(light):
                return(node["multiply"].getValue())

    def _setStyleSheet(key, knob, mode):
        style = {
            "update": ("color: rgb({},{},{})".format(255, 85, 0)),  # ? format?
            "reset": ""
        }
        self.lightSettings[key][knob].setStyleSheet(style["mode"])

    def expSliderChanged(self):
        '''
        When Exposure slider is changed, adjust the expo spinbox
        and highlight the text to show it's been changed
        QSlider values are multiplied by 0.01 in order to make it work with the double spinbox
        decimale values
        '''
        key = self.getInWhichKey(self.sender(), "expSlider")
        if self.lightSettings[key]["expSpin"].value() != self.sender().value()*0.01:
            self.lightSettings[key]["expSpin"].setValue(self.sender().value()*0.01)
            if self.sender().value() != 0:
                styleSheetColor = ("color: rgb({},{},{})".format(255,85,0))
            else:
                styleSheetColor = ("")
            self.lightSettings[key]["expLabel"].setStyleSheet(styleSheetColor)
            self.updateExposure(key)

    def expSpinChanged(self):
        '''
        When Exposure spinbox is changed, adjust the expo slider accordingly
        '''
        key = self.getInWhichKey(self.sender(), "expSpin")
        if self.lightSettings[key]["expSlider"].value() != self.sender().value()*100:
            self.lightSettings[key]["expSlider"].setValue(self.sender().value()*100)
            if self.sender().value() != 0:
                styleSheetColor = ("color: rgb({},{},{})".format(255,85,0))
            else:
                styleSheetColor = ("")
            self.lightSettings[key]["expLabel"].setStyleSheet(styleSheetColor)
            self.updateExposure(key)

    def updateExposure(self, light):
        '''
        Update the actual Exposure Node
        '''
        exp = pow(2, (self.lightSettings[light]["expSpin"].value()))
        grpName = self.node["name"].getValue()
        for node in self.node.nodes():
            if node["label"].getValue() == "EXP_RGBA_{}".format(light):
                node["multiply"].setValue([exp,exp,exp,1.0])

    def getExpValue(self, light):
        '''
        Init for correct exposure values at the build of the UI
        '''
        grpName = self.node["name"].getValue()
        for node in self.node.nodes():
            if node["label"].getValue() == "EXP_RGBA_{}".format(light):
                return( math.log( (node["multiply"].getValue()[0]) , 2) )

    def hideClicked(self):
        '''
        Toggle on or off the light visibility
        '''
        light = self.getInWhichKey(self.sender(), "hide")

        for node in self.node.nodes():
            if node["label"].getValue() == "MRG_EXP_RGBA_{}".format(light):
                if (self.sender().isChecked() == True):
                    self.sender().setStyleSheet("background-color: rgb(225,85,0)")
                    node["mix"].setValue(0.0)
                else:
                    node["mix"].setValue(1.0)
                    self.sender().setStyleSheet("")

    def getHideValue(self, light):
        '''
        Init for correct Hide values at the build of the UI
        '''
        for node in self.node.nodes():
            if (node["label"].getValue() == "MRG_EXP_RGBA_{}".format(light)):
                if (node["mix"].getValue() == 0):
                    self.lightSettings[light]["hide"].click()
                    self.lightSettings[light]["hide"].setStyleSheet("background-color: rgb(255,85,0)")

    def soloClicked(self):
        '''
        Toggle on or off the light switches
        '''
        key = self.getInWhichKey(self.sender(), "solo")
        if self.sender().isChecked():
            self.sender().setStyleSheet("background-color: rgb(255,85,0)")
        else:
            self.sender().setStyleSheet("")

        soloList = []
        lightList = []
        for light in self.lightSettings:
            lightList.append(light)
            if self.lightSettings[light]["solo"].isChecked():
                #print("{} should be displayed".format(light))
                soloList.append(light)

        if soloList:
            for node in self.node.nodes():
                if (node["label"].getValue().startswith("SWT_")):
                    nodeLight = (node["label"].getValue()[4:])
                    if nodeLight not in soloList:
                        node["which"].setValue(1)
                    else:
                        node["which"].setValue(0)
        else:
            for node in self.node.nodes():
                if (node["label"].getValue().startswith("SWT_")):
                    node["which"].setValue(0)

    def checkboxClicked(self):
        '''
        Check if other checkbox are clicked in order to modify multiple light passes at the same time
        '''
        for key in self.lightClicked:
            print(key)

    def resetClicked(self, keylist):
        '''
        Reset the current light settings to defaults
        '''
        if keylist == False:
            keylist = []
            keylist.append(self.getInWhichKey(self.sender(), "Reset"))

        for key in keylist :
            self.lightSettings[key]["expSlider"].setValue(0)
            self.lightSettings[key]["colorR"].setValue(1.0)
            self.lightSettings[key]["colorG"].setValue(1.0)
            self.lightSettings[key]["colorB"].setValue(1.0)
            if self.lightSettings[key]["hide"].isChecked():
                self.lightSettings[key]["hide"].click()

    def resetAllClicked(self):
        '''
        Reset all Lights to their default settings
        '''
        keylist = []
        for key in self.lightSettings:
            keylist.append(key)

        self.resetClicked(keylist)

    def filterLights(self):
        '''
        Filtering the light layouts based on the search from the QLineEdit field
        '''
        searchString = self.sender().text()
        if (searchString != "Filter Lights") & (searchString != ""):
            print("filtering : {}".format(searchString))
        else:
            print("No filtering")
        for layout in self.lightLayouts:
            hide = False
            for subLayout in range(layout.count()):
                lay = layout.itemAt(subLayout)
                #print(type(lay))
                if isinstance(lay, QtWidgets.QSpacerItem) == False:
                    for widg in range(lay.count()):
                        widget = (lay.itemAt(widg))
                        if isinstance(widget.widget(), QtWidgets.QCheckBox):
                            if searchString.lower() not in widget.widget().text().lower():
                                hide = True
                        if (widget.widget() != None):
                            if hide == True:
                                widget.widget().setVisible(False)
                            else:
                                widget.widget().setVisible(True)

    def exportClicked(self):
        '''
        Builds a json containing all the modified values as a dict
        Asks the user to save it as a json file in order to allow
        the lighter to import it back into maya
        '''
        exportDict = {}

        for light in self.lightSettings:
            if light not in exportDict:
                exportDict[light] = {}
            exportDict[light]["exposure"] = self.lightSettings[light]["expSpin"].value()
            exportDict[light]["color"] = [self.lightSettings[light]["colorR"].value(), self.lightSettings[light]["colorG"].value(), self.lightSettings[light]["colorB"].value()]
            exportDict[light]["hidden"] = self.lightSettings[light]["hide"].isChecked()
            print(light)
            print("Exposure is : {}".format(exportDict[light]["exposure"]))
            print("Color is : {}".format(exportDict[light]["color"]))
            print("Is hidden : {}".format(exportDict[light]["hidden"]))

        #file = nuke.scriptName()[:-3]
        # Trying to auto get the name from the nuke file, if in case it is piped
        try:
            curr_nk = nuke.Root["name"].getValue()
            name, ext = os.path.splitext(curr_nk)
            out_json = os.path.join(os.path.dirname(curr_nk, name + ".json"))
        except:
            print("couldn't get nuke root -- unpiped Nuke")
            out_json = "C:/unpipedLightTweak"

        # Getting a save destination and name from user
        destination = QtWidgets.QFileDialog.getSaveFileName(self, "Export Light Tweaks", out_json, "JSON (*.json)")[0]
        # making sure the .json has not been erased by user
        if not destination.endswith(".json"):
            destination = "{}.json".format(destination)

        with open(destination, "w") as f:
            f.write(json.dumps(exportDict, indent=4))

    def closeEvent(self, event):
        '''
        Override of the close event to reset the solo buttons before exit
        '''
        # Reset the solo buttons if they are toggled on some lights
        for light in self.lightSettings:
            if self.lightSettings[light]["solo"].isChecked():
                self.lightSettings[light]["solo"].click()

        # Finally closes the window
        event.accept()


class QLine(QtWidgets.QFrame):
    '''
    Simple class to draw separators between the light layouts
    '''
    def __init__(self):
        super(QLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


def main():
    # Showing the selectLpePanel class window
    p = SelectLpePanel()
    #print((QtWidgets.QStyleFactory.keys()))
    p.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    p.resize(500,800)
    p.show()


# Showing the selectLpePanel class window
p = SelectLpePanel()
#print((QtWidgets.QStyleFactory.keys()))
p.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
p.resize(500,800)
p.show()
