import maya.cmds as cmds
import json

def main():
    renderer = getRenderer()

def vrayMain():
    lightDict = getLightsInfosVray()
    jsonData = openJson()
    jsonToLightsVray(lightDict, jsonData)

def arnoldMain():
	lightDict = getLightsInfos()
	jsonData = openJson()
	jsonToLights(lightDict, jsonData)

def jsonToLights(lightDict, jsonData):
	'''
	Checking the modified parameters in the json dict
	And making the changed on the lights in Maya
	'''
	for lightShader in lightDict:
		# Setting key error in order to avoid hidden lights in 3D scene causing issues
		try :
			isVisible = (jsonData[lightShader])
			#print(lightShader, isVisible)
			if (jsonData[lightShader]["exposure"] != 0):
				#print("Will need to change exposure on : {}".format(lightDict[lightShader].keys()))
				changeExposure(lightDict[lightShader], lightDict[lightShader].keys(), jsonData[lightShader]["exposure"])
			if (jsonData[lightShader]["color"] != [1.0,1.0,1.0]):
				#print("Will need to change color on : {}".format(lightDict[lightShader].keys()))
				changeColor(lightDict[lightShader], lightDict[lightShader].keys(), jsonData[lightShader]["color"])
			if (jsonData[lightShader]["hidden"] != False):
				#print("Will need to turn visibility off on : {}".format(lightDict[lightShader].keys()))
				changeVisibility(lightDict[lightShader], lightDict[lightShader].keys(), jsonData[lightShader]["hidden"])
		except KeyError:
			pass

def jsonToLightsVray(lightDict, jsonData):
    '''
    Applying the changes from the json data to the actual Vray lights
    '''
    # Uncomment for debugging purposes, printing the contents of lightDict and Json Data
    '''
    for light in jsonData:
        print(light)
        print(jsonData[light])

    for lightShader in lightDict:
        print(lightShader)
        print(lightDict[lightShader])
    '''

    for lightShader in lightDict:
        jsonLight = lightShader[5:]
        isVisible = (jsonData[jsonLight])
        for light in lightDict[lightShader]:
            #print(light)
            #print(lightDict[lightShader])
            #print(light, lightDict[lightShader][light])
            if (jsonData[jsonLight]["exposure"] != 0):
                #print("Will need to change exposure on : {}".format(lightDict[lightShader].keys()))
                changeExposureVray(lightDict[lightShader], lightDict[lightShader].keys(), jsonData[jsonLight]["exposure"])
            if (jsonData[jsonLight]["color"] != [1.0,1.0,1.0]):
                #print("Will need to change color on : {}".format(lightDict[lightShader].keys()))
                changeColorVray(lightDict[lightShader], lightDict[lightShader].keys(), jsonData[jsonLight]["color"])
            if (jsonData[jsonLight]["hidden"] != False):
                #print("Will need to change visibilty on : {}".format(lightDict[lightShader].keys()))
                changeVisibility(lightDict[lightShader], lightDict[lightShader].keys(), jsonData[jsonLight]["hidden"])

def changeVisibility(lightDict, lights, value):
    '''
    For every light in the lights list, makes sure their visibility is set to 0
    '''
    for light in lights:
        # If the light is a VRayLightDomeShape a a Vray sky is connected to it, we need to set the mult of the vraysky to 0
        # Otherwise it will still be output to the beauty, even though the Domelight will be empty and have no data
        if (cmds.objectType(light) == "VRayLightDomeShape"):
            connection = cmds.listConnections("{}.domeTex".format(light), t="VRaySky", d=False, s=True)
            for node in connection:
                cmds.setAttr("{}.intensityMult".format(node), 0)
        # Getting the parent of the shape
        transform = cmds.listRelatives(light, parent=True, type="transform", f = True)
        for parent in transform:
            cmds.setAttr("{}.visibility".format(parent), 0.0000)

def changeColorVray(lightDict, lights, value):
    '''
    For every light in the light lists takes the current color
    checks if there is an input in the color
    if not mults the current color by the value
    else, plugs a color composity and uses it to mult the previous input
    by the value
    '''
    for light in lights:
        # Check if a node is connected to the color entry
        if (type(lightDict[light]["color"]) != list):
            #print("Adding a color composite node for {}".format(light))
            composite = cmds.createNode("colorComposite", skipSelect = False)
            if cmds.objectType(light) in ["spotLight", "ambientLight", "directionalLight", "pointLight", "areaLight", "volumeLight"]:
                cmds.connectAttr(lightDict[light]["color"],"{}.colorA".format(composite), force = True )
                cmds.setAttr("{}.colorB".format(composite), value[0], value[1], value[2], type = "double3")
                cmds.setAttr("{}.operation".format(composite), 3)
                cmds.connectAttr("{}.outColor".format(composite), "{}.color".format(light), force = True)
            elif cmds.objectType(light) == "VRayLightMeshLightLinking":
                # Getting the actual needed node for this type of light
                transform = cmds.listRelatives(light,type='transform',p=True)
                connections = cmds.listConnections(transform)
                for item in connections:
                    if cmds.objectType(item) == "VRayLightMesh":
                        lightMesh = item
                cmds.connectAttr(lightDict[light]["color"],"{}.colorA".format(composite), force = True )
                cmds.setAttr("{}.colorB".format(composite), value[0], value[1], value[2], type = "double3")
                cmds.setAttr("{}.operation".format(composite), 3)
                cmds.connectAttr("{}.outColor".format(composite), "{}.lightColor".format(lightMesh), force = True)
            elif cmds.objectType(light) == "VRaySunShape":
                cmds.connectAttr(lightDict[light]["color"],"{}.colorA".format(composite), force = True )
                cmds.setAttr("{}.colorB".format(composite), value[0], value[1], value[2], type = "double3")
                cmds.setAttr("{}.operation".format(composite), 3)
                cmds.connectAttr("{}.outColor".format(composite), "{}.filterColor".format(light), force = True)
            else:
                cmds.connectAttr(lightDict[light]["color"],"{}.colorA".format(composite), force = True )
                cmds.setAttr("{}.colorB".format(composite), value[0], value[1], value[2], type = "double3")
                cmds.setAttr("{}.operation".format(composite), 3)
                cmds.connectAttr("{}.outColor".format(composite), "{}.lightColor".format(light), force = True)
        else:
            color = lightDict[light]["color"][0]
            if cmds.objectType(light) in ["spotLight", "ambientLight", "directionalLight", "pointLight", "areaLight", "volumeLight"]:
                newColor = [color[0] * value[0], color[1] * value[1], color[2] * value[2]]
                cmds.setAttr("{}.color".format(light), newColor[0], newColor[1], newColor[2], type = "double3")
            elif cmds.objectType(light) == "VRayLightMeshLightLinking":
                # Getting the actual needed node for this type of light
                transform = cmds.listRelatives(light,type='transform',p=True)
                connections = cmds.listConnections(transform)
                for item in connections:
                    if cmds.objectType(item) == "VRayLightMesh":
                        lightMesh = item
                        newColor = [color[0] * value[0], color[1] * value[1], color[2] * value[2]]
                        cmds.setAttr("{}.lightColor".format(lightMesh), newColor[0], newColor[1], newColor[2], type = "double3")
            elif cmds.objectType(light) == "VRaySunShape":
                newColor = [color[0] * value[0], color[1] * value[1], color[2] * value[2]]
                cmds.setAttr("{}.filterColor".format(light), newColor[0], newColor[1], newColor[2], type = "double3")
            else:
                newColor = [color[0] * value[0], color[1] * value[1], color[2] * value[2]]
                cmds.setAttr("{}.lightColor".format(light), newColor[0], newColor[1], newColor[2], type = "double3")

def changeColor(lightDict, lights, value):
	'''
	For every light in the lights list takes the current color
	Checks if there is an input in the color
	if not, mults the current color by the value
	if there is, plugs a color composite and uses the composite
	to mult the previous input by the value
	'''
	for light in lights:
		# Check if a node is connected to the color entry
		if (type(lightDict[light]["color"]) != list):
			#print("Adding a color composite node for {}".format(light))
			composite = cmds.createNode("colorComposite", skipSelect = False)
			cmds.connectAttr(lightDict[light]["color"], "{}.colorA".format(composite), force = True)
			cmds.setAttr("{}.colorB".format(composite), value[0], value[1], value[2], type = "double3")
			cmds.setAttr("{}.operation".format(composite), 3)
			cmds.connectAttr("{}.outColor".format(composite), "{}.color".format(light), force = True)
		else:
			lightDict[light]["color"] = lightDict[light]["color"][0]
			newColor = [ lightDict[light]["color"][0]*value[0] , lightDict[light]["color"][1]*value[1]  , lightDict[light]["color"][2]*value[2] ]
			cmds.setAttr("{}.color".format(light), newColor[0], newColor[1], newColor[2], type = "double3")
	
def changeExposureVray(lightDict, lights, value):
    '''
    For every light in the lightlist tqkes the current intensity
    and multiplies it by the exposure value
    '''
    for light in lights:
        initialIntensity = lightDict[light]["exposure"]
        newIntensity = initialIntensity * pow(2, value)
        #print("The {} will take change from : {} to : {}".format(light, initialIntensity , newIntensity))

        if cmds.objectType(light) in ["spotLight", "ambientLight", "directionalLight", "pointLight", "areaLight", "volumeLight"]:
            cmds.setAttr("{}.intensity".format(light), newIntensity)
        elif cmds.objectType(light) == "VRayLightMeshLightLinking":
            # Getting the actual needed node for this type of light
            transform = cmds.listRelatives(light,type='transform',p=True)
            connections = cmds.listConnections(transform)
            for item in connections:
                if cmds.objectType(item) == "VRayLightMesh":
                    cmds.setAttr("{}.intensityMult".format(item), newIntensity)
        else:
            cmds.setAttr("{}.intensityMult".format(light), newIntensity)
        
def changeExposure(lightDict, lights, value):
	'''
	For every light in the lights list takes the current exposure
	And adds/substracts a value depending on the value
	'''
	for light in lights:
		#print("The {} will take : {}".format(light, value))
		newExpo = (lightDict[light]["exposure"]) + (value)
		#print(newExpo)
		# Checking if Arnold exposure or classic one
		if (cmds.objectType(light).startswith("ai") == True) & (cmds.objectType(light) != "aiMeshLight"):
			#print("arnoldLight")
			cmds.setAttr("{}.exposure".format(light), newExpo)
		else:
			#print("classicLight")
			cmds.setAttr("{}.aiExposure".format(light), newExpo)

def openJson():
	'''
	User is asked to open the Json file in a dialog window
	Returns the json file as a dict
	'''
	fileDiag = cmds.fileDialog(m=0, title = "Open JSON light Export")
	with open(fileDiag) as f:
		jsonData = json.load(f)

	# Uncomment for debugging purposes
	'''
	for light in jsonData:
		print(light)
		print(jsonData[light])
	'''	

	return(jsonData)
	
def getLightsInfosVray():
    '''
    Builds a light dictionnary from the scene parsing the maya and arnold lights
	Returns a light dictionnary in the following format
	lightsDict{LightSelectRenderElement}
			{lightsContainedInLightSelectRenderElement}
				{exposure, color}
    '''
    vrayLgtTypes = ["VRayLightRectShape", "VRayLightSphereShape", "VRaySunShape", 
                    "VRayLightDomeShape", "VRayLightMeshLightLinking", "VRayLightIESShape", 
                    "spotLight", "ambientLight", "directionalLight", "pointLight", "areaLight", "volumeLight"]
    lights = cmds.ls(type=vrayLgtTypes)
    lightDict = {}
    lpe = ""
    for light in lights:
        # Getting the light transform
        transform = cmds.listRelatives(light,type='transform',p=True)
        connections = cmds.listConnections(transform)
        # Finding the Renderelement groups
        for node in connections:
            if node.startswith("RGBA_"):
                if node not in lightDict:
                    lightDict[node] = {}
                    lightDict[node][light] = {}
                    lpe = node
                else:
                    lightDict[node][light] = {}
                    lpe = node
                    
        # Getting the light attributes -- INTENSITY
        if cmds.objectType(light) in ["spotLight", "ambientLight", "directionalLight", "pointLight", "areaLight", "volumeLight"]:
            intensity = cmds.getAttr("{}.intensity".format(light))
        elif cmds.objectType(light) == "VRayLightMeshLightLinking":
            # Getting the actual needed node for this type of light
            for item in connections:
                if cmds.objectType(item) == "VRayLightMesh":
                    intensity = cmds.getAttr("{}.intensityMult".format(item))
        else:
            intensity = cmds.getAttr("{}.intensityMult".format(light))
        lightDict[lpe][light]["exposure"] = intensity

        # Getting the light attributes -- COLOR
        if cmds.objectType(light) in ["spotLight", "ambientLight", "directionalLight", "pointLight", "areaLight", "volumeLight"]:
            hasConnection = cmds.connectionInfo("{}.color".format(light), isDestination = True)
            if hasConnection:
                connection = cmds.listConnections("{}.color".format(light), d=False, s=True, p=True)
                color = connection[0]
            else:
                color = cmds.getAttr("{}.color".format(light))
        elif cmds.objectType(light) == "VRayLightMeshLightLinking":
            # Getting the actual needed node for this type of light
            for item in connections:
                if cmds.objectType(item) == "VRayLightMesh":
                    #intensity = cmds.getAttr("{}.intensityMult".format(item))
                    hasConnection = cmds.connectionInfo("{}.lightColor".format(item), isDestination = True)
                    if hasConnection:
                        connection = cmds.listConnections("{}.lightColor".format(item), d=False, s=True, p=True)
                        color = connection[0]
                        #print("CONNECTION IS : {}".format(color))
                    else:
                        color = cmds.getAttr("{}.lightColor".format(item))
        elif cmds.objectType(light) == "VRaySunShape":
            hasConnection = cmds.connectionInfo("{}.filterColor".format(light), isDestination = True)
            if hasConnection:
                connection = cmds.listConnections("{}.filterColor".format(light), d=False, s=True, p=True)
                color = connection[0]
            else:
                color = cmds.getAttr("{}.filterColor".format(light))
        else:
            hasConnection = cmds.connectionInfo("{}.lightColor".format(light), isDestination = True)
            if hasConnection:
                connection = cmds.listConnections("{}.lightColor".format(light), d=False, s=True, p=True)
                color = connection[0]
            else:
                color = cmds.getAttr("{}.lightColor".format(light))
        lightDict[lpe][light]["color"] = color

    # For debbugging purposes, print the contents of the lightDict
    '''
    for lightPass in lightDict:
        print(lightPass)
        print(lightDict[lightPass])
    '''
    return(lightDict)

def getLightsInfos():
	'''
	Builds a light dictionnary from the scene parsing the maya and arnold lights
	Returns a light dictionnary in the following format
	lightsDict{aiAov}
			{lightsContainedInAov}
				{exposure, color}
	'''
	# listing selected object children type for debugging purposes
	'''
	for obj in cmds.ls(selection = True):
	print(cmds.objectType(obj))
	children = cmds.listRelatives(obj, children=True, fullPath=True) or []
	print(cmds.objectType(children))
	'''

	lights = cmds.ls(type =["aiAreaLight", "aiSkyDomeLight", "aiMeshLight", "aiPhotometricLight", "aiSkyDomeLight", "directionalLight", "pointLight", "spotLight", "areaLight", "volumeLight" ])
	lightDict = {}
	for light in lights:
		#print("{} is output in {}".format(light, cmds.getAttr("{}.aiAov".format(light))))
		lightgroup = cmds.getAttr("{}.aiAov".format(light))
		if lightgroup not in lightDict:
			lightDict[lightgroup] = {}
			lightDict[lightgroup][light] = {}
		else:
			lightDict[lightgroup][light] = {}

		# Getting light attributes
		if (cmds.objectType(light).startswith("ai") == True) & (cmds.objectType(light) != "aiMeshLight"):
			lightDict[lightgroup][light]["exposure"] = cmds.getAttr("{}.exposure".format(light))
		else:
			lightDict[lightgroup][light]["exposure"] = cmds.getAttr("{}.aiExposure".format(light))
		# Detects if the color has an input
		hasConnection = cmds.connectionInfo("{}.color".format(light), isDestination = True)
		if (hasConnection == True ):
			connection = cmds.listConnections("{}.color".format(light), d=False, s=True, p=True)
			lightDict[lightgroup][light]["color"] = connection[0]
		else:
			lightDict[lightgroup][light]["color"] = cmds.getAttr("{}.color".format(light))

	
	'''
	for light in lightDict:
		print(light)
		print(lightDict[light])
	'''

	return(lightDict)
        
def getRenderer():
    '''
    Trying to detect from the scene the script is ran in, if the renderer is Vray or Arnold
    '''
    renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")
    print("FOUND {} RENDERER".format(renderer.upper()))

    if renderer == "vray":
        vrayMain()
    else:
        arnoldMain()

if __name__ == "__main__":
	main()
