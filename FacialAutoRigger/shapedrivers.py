import bpy, bmesh
from mathutils import *
from math import *

from .data import basePositions;
from .utils import getMeshObject, DAGSortBones, decompose_path

def makeShapeDrivers(ob, LR_sign=1):
  arm = ob.data
  print(ob, arm)
  
  facerig = arm.facerig
  meshob = facerig.meshob
  
  bm = bmesh.new()
  bm.from_mesh(meshob.data)
  
  mm = [Vector([1e17, 1e17, 1e17]), Vector([-1e17, -1e17, -1e17])]
  
  for v in bm.verts:
    co = meshob.matrix_world @ v.co
    for i in range(3):
      mm[0][i] = min(mm[0][i], co[i]);
      mm[1][i] = max(mm[1][i], co[i]);
  
  size = mm[1] - mm[0]
  print("MM", size)
  
  base = "key_blocks["
  anim = meshob.data.shape_keys.animation_data
  
  def findOrMakeVar(fc, name, target):
    var = None
    for v in fc.driver.variables:
      if v.name == name:
        var = v
        break
    
    if var is None:
      var = fc.driver.variables.new()
      var.name = name
    
    var.type = "TRANSFORMS"
    var.targets[0].id = ob
    var.targets[0].bone_target = target
    var.targets[0].transform_space = "LOCAL_SPACE"
    
    return var 
    
  keys = ["LOC_X", "LOC_Y", "LOC_Z"]
    
  def addShapeDriver(keyname, target, axis, min, max):
    path = "key_blocks[\"" + keyname + "\"].value"
    fc = None
    
    for d in anim.drivers:
      if d.data_path == path:
        fc = d
        break 
  
    if not fc:
      fc = anim.drivers.new(path)
      print("creating new driver")
    
    print(fc)
    fc.extrapolation = "CONSTANT"
    
    for i in range(5):
      for kp in list(fc.keyframe_points):
        try:
          fc.keyframe_points.remove(kp)
        except:
          print("failed to remove keyframe point?")
    
    fc.keyframe_points.insert(min, 0);
    fc.keyframe_points.insert(max, 1);
    fc.driver.type = "AVERAGE"
    
    var = findOrMakeVar(fc, "v", target)
    var.targets[0].transform_type = keys[axis]
    
    return (fc, var)
  
  def addShapeDriver2(keyname, target, axis1, axis2, min, max, sign, sign2=1.0):
    fc, var = addShapeDriver(keyname, target, axis1, min, max)
    fc.driver.type = "SCRIPTED"
    
    var2 = findOrMakeVar(fc, "v2", target)
    var2.targets[0].transform_type = keys[axis2]
    
    fc.driver.expression = "v*%.1f - max(v2*%.1f, 0.0)" % (sign2, sign)
    
    return (fc, var)
  
  def addShapeDriver3(keyname, target, axis1, axis2, min, max, sign, sign2=1.0):
    fc, var = addShapeDriver(keyname, target, axis1, min, max)
    fc.driver.type = "SCRIPTED"
    
    var2 = findOrMakeVar(fc, "v2", target)
    var2.targets[0].transform_type = keys[axis2]
    
    fc.driver.expression = "v*%.1f - max(v2*%.1f, 0.0)" % (sign2, sign)
    
    return (fc, var)
  fac = size[2]*0.1
  
  addShapeDriver("Zip", "Zip", 1, 0, fac);
  addShapeDriver("Purse", "Mouth", 2, 0, fac);
  
  fac = size[0]*0.1*LR_sign
  addShapeDriver3("Wide.L", "Mouth", 2, 0, 0, fac, LR_sign, -1.0);
  addShapeDriver3("Wide.R", "Mouth", 2, 0, 0, fac, -LR_sign, -1.0);
  
  addShapeDriver2("UpperLip.L", "Mouth", 1, 0, 0, fac, LR_sign)
  addShapeDriver2("UpperLip.R", "Mouth", 1, 0, 0, fac, -LR_sign)

  addShapeDriver2("LowerLip.L", "Mouth", 1, 0, 0, fac, LR_sign, -1.0)
  addShapeDriver2("LowerLip.R", "Mouth", 1, 0, 0, fac, -LR_sign, -1.0)
  
  