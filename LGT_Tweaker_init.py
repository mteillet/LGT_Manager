# LGT_Tweaker_init
import time

import nuke
from PySide2 import QtCore, QtGui, QtWidgets


class SelectLpePanel(QtWidgets.QWidget):
    def __init__(self, node):
        super(SelectLpePanel, self).__init__()
        self.setWindowTitle("LGT Manager")
        self.node = node

        #self.setStyleSheet("color: white; background-color: rgb(11,11,11)")
        layout = QtWidgets.QVBoxLayout()

 
        # Getting channels from read
        channels = self.getChannelsFromRead(node)
        # Creating a dict marking true the channels detected as RGBA
        listedRgba = self.removeNonRgba(channels)
        #print(listedRgba)


        ###############
        ##  Widgets  ##
        ###############
        self.title = QtWidgets.QLabel("Select your light AOVs :")

        # List of lights for the Light AOV selection
        self.lightWidgetList =  []
        for i in listedRgba:
            # Check box if Rgba* is true
            if listedRgba[i] == True:
                tempCheckbox = QtWidgets.QCheckBox(i)
                tempCheckbox.setChecked(True)
                self.lightWidgetList.append(tempCheckbox)
            else:
                self.lightWidgetList.append(QtWidgets.QCheckBox(i))

        # Ok and Cancel Buttons
        self.ok = QtWidgets.QPushButton("Ok")
        self.ok.clicked.connect(self.validateAovs)
        self.cancel = QtWidgets.QPushButton("Cancel")
                
                

        ##############
        ##  Layout  ##
        ##############
        titleLayout = QtWidgets.QHBoxLayout()
        titleLayout.addWidget(self.title)
        
        checkLgtLayout = QtWidgets.QVBoxLayout()
        for i in self.lightWidgetList:
            checkLgtLayout.addWidget(i)

        okLayout = QtWidgets.QHBoxLayout()
        okLayout.addWidget(self.ok)
        okLayout.addWidget(self.cancel)
        
        layout.addLayout(titleLayout)
        layout.addLayout(checkLgtLayout)
        layout.addLayout(okLayout)

        self.setLayout(layout)




    ###############
    ##  BACKEND  ##
    ###############
    def getChannelsFromRead(self,read):	 
        '''
        Getting Channels from the read Node
        '''
        channels = read.channels()
        channelsCleaned = []

        current = 0
        for i in channels:
            channels[current] = (channels[current].split("."))[0]
            if channels[current] not in channelsCleaned:
                channelsCleaned.append(channels[current])
            current += 1


        return(channelsCleaned)

    def removeNonRgba(self, channels):
        '''
        Takes a list in and returns a dict with the channels beginning with RGBA as True
        '''
        cleanDir = {}
        for chan in channels:
            cleanDir[chan] = bool(chan.startswith("RGBA"))
        return cleanDir

    def validateAovs(self):
        '''
        Getting the LGT AOVs and sending them to the build nodegraph function
        '''
        print("The LGT Tweaker will proceed using the following lights : ") 
        selectedChannels = []
        for light in self.lightWidgetList:
            if light.isChecked():
                print(light.text())
                selectedChannels.append(light.text())
        self.createShuffles(selectedChannels)

    def createShuffles(self, selectedChannels):
        '''
        Takes in the channel list and creates the shuffle layout for every channel selected
        '''
        # First create a dot under the read for better clarity
        readDot = nuke.nodes.Dot(inputs=[self.node])
        # Move the dot lower
        readDot.setYpos(int(readDot["ypos"].value()) + 1000)

        # print(self.node, selectedChannels)
        shuffleNodeList = []
        exposureNodeList = []
        colorNodeList = []
        for layer in selectedChannels:
            currentShuffle = (nuke.nodes.Shuffle(label=layer, inputs=[readDot]))
            currentShuffle["in"].setValue(layer)
            currentExposure = nuke.nodes.Grade( label = str("EXP_{}".format(layer)), inputs = [currentShuffle])
            currentExposure["multiply"].setValue([1.0,1.0,1.0,1.0])
            currentColor = nuke.nodes.Grade(label = str("COL_{}".format(layer)), inputs = [currentExposure])
            currentColor["multiply"].setValue([1.0,1.0,1.0,1.0])
            # In case need to previs nodes as postage stamp :
            #currentShuffle["postage_stamp"].setValue( True )
            shuffleNodeList.append(currentShuffle)
            exposureNodeList.append(currentExposure)
            colorNodeList.append(currentColor)
        # Adding black shuffle for switching activations
        blackShuffle = nuke.nodes.Shuffle( label = "blackShuffle", inputs = [readDot])
        blackShuffle["in"].setValue(selectedChannels[0])
        #print(dir(blackShuffle))
        settings = ["red", "green", "blue"]
        for chan in settings:
            blackShuffle[chan].setValue(0)
        shuffleNodeList.append(blackShuffle)

        # Creating and merging the channels
        mergeList = []
        switchList = []
        blackSwitch = nuke.nodes.Switch(inputs = [colorNodeList[0], blackShuffle])
        blackSwitch["label"].setValue("SWT_{}".format(exposureNodeList[0]["label"].getValue()[9:]))
        blackSwitch["name"].setValue("SWT_{}".format(exposureNodeList[0]["label"].getValue()[9:]))
        blackMerge = nuke.nodes.Merge2(operation = "plus", inputs = [blackShuffle, blackSwitch])
        blackMerge["label"].setValue("MRG_{}".format(exposureNodeList[0]["label"].getValue()))
        blackMerge["name"].setValue("MRG_{}".format(exposureNodeList[0]["label"].getValue()))

        mergeList.append(blackMerge)
        switchList.append(blackSwitch)

        current = 1
        for i in exposureNodeList:
            if current == 1 :
                currentSwitch = nuke.nodes.Switch(inputs = [colorNodeList[current], blackShuffle])
                currentSwitch["label"].setValue("SWT_{}".format(exposureNodeList[current]["label"].getValue()[9:]))
                currentSwitch["name"].setValue("SWT_{}".format(exposureNodeList[current]["label"].getValue()[9:]))
                currentMerge = nuke.nodes.Merge2(operation = "plus", inputs = [mergeList[0], currentSwitch])
                currentMerge["label"].setValue("MRG_{}".format(exposureNodeList[current]["label"].getValue()))
                currentMerge["name"].setValue("MRG_{}".format(exposureNodeList[current]["label"].getValue()))
                mergeList.append(currentMerge)
                switchList.append(currentSwitch)
            else:
                if current < (len(exposureNodeList)):
                    currentSwitch = nuke.nodes.Switch(inputs = [colorNodeList[current], blackShuffle])
                    currentSwitch["label"].setValue("SWT_{}".format(exposureNodeList[current]["label"].getValue()[9:]))
                    currentSwitch["name"].setValue("SWT_{}".format(exposureNodeList[current]["label"].getValue()[9:]))
                    #print(current)
                    currentMerge = nuke.nodes.Merge2(operation = "plus", inputs = [mergeList[current-1], currentSwitch])
                    currentMerge["label"].setValue("MRG_{}".format(exposureNodeList[current]["label"].getValue()))
                    currentMerge["name"].setValue("MRG_{}".format(exposureNodeList[current]["label"].getValue()))
                    mergeList.append(currentMerge)
                    switchList.append(currentSwitch)
            current += 1

        # Create output after the merges
        outDot = nuke.nodes.Dot(inputs = [currentMerge])

        # Deselect Read
        self.node.setSelected(False)
        toSelect = []
        toSelect += shuffleNodeList
        toSelect += exposureNodeList
        toSelect += mergeList
        toSelect += colorNodeList
        toSelect += switchList
        toSelect += [outDot, readDot]
        for sel in toSelect:
            sel.setSelected(True)

        # Make group from created nodes
        LgtGroup = nuke.collapseToGroup(show=False)
        LgtGroup["name"].setValue("LGT_Tweaker_v00")

        # Create a Run Button on the node $
        pyBtn = nuke.PyScript_Knob(name="Start", command="nuke.pluginAddPath(r'P:\mteillet\LGT_tweaker');from importlib import reload;import LGTtweaker_gui as lgt;reload(lgt);lgt.main()")
        LgtGroup.addKnob(pyBtn)


# Showing the selectLpePanel class window
node = nuke.selectedNode()
p = SelectLpePanel(node)
p.show()
