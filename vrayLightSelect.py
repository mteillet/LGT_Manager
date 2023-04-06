import maya.cmds as cmds

def main():
    # Set renderer to V-Ray
    #cmds.setAttr("defaultRenderGlobals.currentRenderer", "vray", type="string")

    scene = cmds.ls()

    # Removing all the previous render elements beginning by RGBA
    for obj in scene:
        if (cmds.objectType(obj) in ["VRayRenderElementSet"]) and (obj.startswith("RGBA_")):
            cmds.delete(obj)

    vrayLgtTypes = ["VRayLightRectShape", "VRayLightSphereShape", "VRaySunShape", 
                    "VRayLightDomeShape", "VRayLightMeshLightLinking", "VRayLightIESShape", 
                    "spotLight", "ambientLight", "directionalLight", "pointLight", "areaLight", "volumeLight"]
    # Loop through all the lights in the scene
    for obj in scene:
        if cmds.objectType(obj) in vrayLgtTypes:
            print(obj)
            rndrElm = mel.eval('vrayAddRenderElement LightSelectElement;')
            rndrElm = cmds.rename(rndrElm, "RGBA_{}".format(obj))

            cmds.setAttr("RGBA_{}.vray_name_lightselect".format(obj),"RGBA_{}".format(obj), type = "string")

            # Getting the transform of the light
            transform = cmds.listRelatives(obj,type='transform',p=True)

            cmds.connectAttr("{}.instObjGroups[0]".format(transform[0]), "{}.dagSetMembers[0]".format(rndrElm))


if __name__ == "__main__":
    main()