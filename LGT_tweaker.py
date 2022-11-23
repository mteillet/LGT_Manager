# LGT_tweaker_v000
import nuke
from PySide2 import QtWidgets, QtCore, QtGui
	
	
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
			if chan.startswith("RGBA") == True:
				cleanDir[chan] = True
			else:
				cleanDir[chan] = False

		return(cleanDir)

	def validateAovs(self):
		'''
		Getting the LGT AOVs and sending them to the build nodegraph function
		'''
		print("The LGT Tweaker will proceed using the following lights : ") 
		selectedChannels = []
		for i in self.lightWidgetList:
			if (i.isChecked() == True):
				print(i.text())
				selectedChannels.append(i.text())
		self.createShuffles(selectedChannels)


	def createShuffles(self, selectedChannels):
		'''
		Takes in the channel list and creates the shuffle layout for every channel selected
		'''
		# First create a dot under the read for better clarity
		readDot = nuke.nodes.Dot(inputs = [self.node])
		# Move the dot lower
		readDot.setYpos(int(readDot["ypos"].value()) + 1000)

		#print(self.node, selectedChannels)
		shuffleNodeList = []
		exposureNodeList = []
		for layer in selectedChannels:
			currentShuffle = (nuke.nodes.Shuffle( label = layer, inputs = [readDot]))
			currentShuffle["in"].setValue(layer)
			currentExposure = nuke.nodes.EXPTool( label = str("EXP_{}".format(layer)), inputs = [currentShuffle])
			currentExposure["mode"].setValue(0)
			# In case need to previs nodes as postage stamp :
			#currentShuffle["postage_stamp"].setValue( True )
			shuffleNodeList.append(currentShuffle)
			exposureNodeList.append(currentExposure)

		current = 1
		mergeList = []
		for i in exposureNodeList:
			if current == 1 :
				currentMerge = nuke.nodes.Merge2(operation = "plus", inputs = [exposureNodeList[current], exposureNodeList[current-1]])
				mergeList.append(currentMerge)
			else:
				if current < (len(exposureNodeList)):
					#print(current)
					currentMerge = nuke.nodes.Merge2(operation = "plus", inputs = [mergeList[current-2], exposureNodeList[current]])
					mergeList.append(currentMerge)
			current += 1

		# Create output after the merges
		outDot = nuke.nodes.Dot(inputs = [currentMerge])

		# Deselect Read
		self.node.setSelected(False)

		readDot.setSelected(True)
		for i in shuffleNodeList:
			i.setSelected(True)
		for n in exposureNodeList:
			n.setSelected(True)
		for m in mergeList:
			m.setSelected(True)
		outDot.setSelected(True)

		# Make group from created nodes
		LgtGroup = nuke.collapseToGroup(show=False)
		LgtGroup["name"].setValue("LGT_Tweaker_v00")

		# Creating the Ctrls on the group Node
		correctExposureNodes = []
		for node in (LgtGroup.nodes()):
			if (node["label"].getValue().startswith("EXP") == True):
				correctExposureNodes.append(node)
				# Light Name Knob
				text = nuke.Text_Knob( str("text_{}".format(node["label"].getValue())) , str(node["label"].getValue()[4:]) )
				# Solo Button
				show = nuke.Boolean_Knob("Show", "Show")
				show.setValue(1)	
				# Exposure Knob
				es = nuke.WH_Knob(node["label"].getValue(), "Exposure")
				es.setRange(-20,20)
				# Color
				col = nuke.Color_Knob("color", "color")
				# Divider
				div = nuke.Text_Knob("div", " ")
				# Adding knob to group
				LgtGroup.addKnob(text)
				LgtGroup.addKnob(show)
				LgtGroup.addKnob(es)
				LgtGroup.addKnob(col)
				LgtGroup.addKnob(div)
				# Linking knob to the corresponding Exposure on
				knobSrc= "{}.{}".format(LgtGroup["name"].getValue(), node["label"].getValue())
				knobDest = ("{}.{}".format(LgtGroup["name"].getValue() , node["name"].getValue()))
				#print(knobSrc)
				#print(knobDest)
				settings = ["red", "green", "blue"]
				for chan in settings :
					nuke.toNode(knobDest).knob(chan).setExpression(knobSrc)




# Showing the selectLpePanel class window
node = nuke.selectedNode()
p = SelectLpePanel(node)
p.show()
