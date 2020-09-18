import bpy
from mathutils import *
from math import *
import json, random, time, os, sys
import bmesh 

from .utils import saveBpyContext, loadBpyContext, ensureObjectMode

def bpyGenericSave(source, target):
  for k in dir(source):
      if k.startswith("_"):
        continue
      
      v = getattr(source, k)
      if type(v) in [bool, int, float, str, bytes]:
          target[k] = v
      elif type(v) in [Vector, Quaternion, Euler]:
        target[k] = list(v)
      elif type(v) == Matrix:
        target[k] = [list(v2) for v2 in v]
      
def bpyGenericLoad(source, target):
  for k in source:
    v = source[k]
    
    if type(v) == list:
      if len(v) == 0:
        continue
        
      if type(v[0]) == list and len(v) in [3, 4] and len(v[0]) == len(v): #matrix?
        v = Matrix(v)
      elif len(v) in [2, 3, 4] and type(v[0]) in [int, float]: #vector?
        v = Vector(v)
      else:
        continue
    elif type(v) not in [bool, int, float, str, bytes]:
      continue
    
    try:
      setattr(target, k, v)
    except:
      print("Failed to set property", k);

def getTempObject(data, id="1"):
  name = "__tempob_" + id
  if name not in bpy.data.objects:
    bpy.data.objects.new(name, data)
  
  scene = bpy.context.scene 
  ob = bpy.data.objects[name]
  
  if ob.name not in scene.objects:
    scene.collection.objects.link(ob)
  
  ob.data = data
  
  return ob
  
def loadArmature(rarm, objs, name_suffix=""):
  rctx = saveBpyContext()
  ensureObjectMode()

  arm = bpy.data.armatures.new(rarm["name"] + name_suffix)
  name = arm.name
  del rarm["name"]

  ob = getTempObject(arm)
  
  print("ARM", arm, name, name_suffix)
  
  bpy.ops.object.select_all(action="DESELECT")
  ob.select_set(True)
  bpy.context.view_layer.objects.active = ob

  print(list(rarm.keys()))
  bpy.ops.object.mode_set(mode="EDIT")
  
  bpyGenericLoad(rarm, arm)

  print("ARM2", arm)
  arm = bpy.data.armatures[name]
  for rb in rarm["bones"]:
    print(arm)
    b = arm.edit_bones.new(rb["name"])

  for rb in rarm["bones"]:
    parent = rb["parent"]
    del rb["parent"]
    b = arm.edit_bones[rb["name"]]

    if parent is not None:
      b.parent = arm.edit_bones[parent]
    
    bpyGenericLoad(rb, b)
    
    b.tail = Vector(rb["tail"])
    b.head = Vector(rb["head"])
  
  loadBpyContext(rctx)
  return arm
  
def loadObject(rob, objs, name_suffix=""):
  print("name_suffix", name_suffix)
  data = rob["data"]
  if data["TYPE"] == "ARMATURE":
    data = loadArmature(data, objs, name_suffix)
  else:
    print("Failed to load object", rob["name"])
    return 
  
  name = rob["name"] + name_suffix
  del rob["name"]
  
  if name not in bpy.data.objects:
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
  else:
    ob = bpy.data.objects[name]
    if name not in bpy.context.scene.objects:
      bpy.context.scene.collection.objects.link(ob)
    ob.data = data
  
  ob = bpy.data.objects[name]
  bpyGenericLoad(rob, ob)
  
  return ob
  
  return bpy.data.objects[name]
  
def saveArmature(arm, refs):
  ret = {"TYPE" : "ARMATURE"}
  
  ret["bones"] = []
  bpyGenericSave(arm, ret)
  ret["name"] = arm.name
  
  for b in arm.bones:
    rb = {}
    
    if b.parent:
      rb["parent"] = b.parent.name
    else:
      rb["parent"] = None
      
    ret["bones"].append(rb)
    bpyGenericSave(b, rb)
    rb["head"] = list(b.head_local)
    rb["tail"] = list(b.tail_local)
    
  return ret
  
def saveTextCurve(tc, refs):
  ret = {"TYPE" : "TEXTCURVE"}
  ret["text_boxes"] = []
  
  bpyGenericSave(tc, ret)
  
  for tb in tc.text_boxes:
    rb = {}
    bpyGenericSave(tb, rb)
    ret["text_boxes"].append(rb)
    
  return ret
  
def savePose(pose, refs):
  ret = {"TYPE" : "POSE"}
  ret["bones"] = []
  
  for b in pose.bones:
    rb = {}
    
    if b.custom_shape is not None:
      refs.add(b.custom_shape)

    if b.parent:
      rb["parent"] = b.parent.name
    else:
      rb["parent"] = None
      
    ret["bones"].append(rb)
    bpyGenericSave(b, rb)
    
  return ret
  
def saveMesh(mesh, refs):
  bm = bmesh.new()
  bm.from_mesh(mesh)
  
  ret = {"TYPE" : "MESH", "VERTS" : [], "FACES" : [], "EDGES" : []}
  
  vs, es, fs = (ret["VERTS"], ret["FACES"], ret["EDGES"])
  
  bm.verts.index_update()
  bm.edges.index_update()
  bm.faces.index_update()
  
  for v in bm.verts:
    rv = {}
    rv["co"] = list(v.co)
    rv["normal"] = list(v.normal)
    rv["select"] = v.select
    rv["hide"] = v.hide
    rv["index"] = v.index
    vs.append(rv)
  
  for e in bm.edges:
    re = {}
    re["v1"] = e.verts[0].index
    re["v2"] = e.verts[1].index
    re["hide"] = e.hide
    re["select"] = e.select
    re["index"] = e.index
    es.append(re)
    
  for f in bm.faces:
    rf = {}
    
    rf["select"] = f.select
    rf["hide"] = f.hide
    rf["index"] = f.index
    
    vs = rf["verts"] = []
    for v in f.verts:
      vs.append(v.index)
      
  return ret

def saveData(ob, refs):
  if isinstance(ob.data, bpy.types.Armature):    
    return saveArmature(ob.data, refs)
  if isinstance(ob.data, bpy.types.Mesh):    
    return saveMesh(ob.data, refs)
  if isinstance(ob.data, bpy.types.TextCurve):    
    return saveTextCurve(ob.data, refs)
  
  print("WARNING: can't save object data for " + ob.name)
  
def saveObject(ob, refs=None):
  refs = set() if refs is None else refs
  
  ret = {}
  ret["TYPE"] = "OBJECT"
  ret["name"] = ob.name
  ret["data"] = saveData(ob, refs)
  
  if (ob.pose):
    ret["pose"] = savePose(ob.pose, refs)
  
  ret["location"] = list(ob.location)
  ret["rotation_euler"] = list(ob.rotation_euler)
  ret["scale"] = list(ob.scale)
  
  if ob.parent is not None:
    ret["parent"] = ob.parent.name
    refs.add(ob.parent)
  else:
    ret["parent"] = None
  
  return ret 
  
def saveObjects(obs):
  obs = set(obs)
  
  ret = []
  done = set()
  
  stop = False
  while not stop:
    stop = True
    for ob in list(obs):
      if ob in done: continue 
      
      stop = False
      done.add(ob)
      ret.append(saveObject(ob, obs))
      
  return ret
  
def saveInternalData():
  obs = [
      bpy.data.objects["_autorig_FaceRigBase"],
      bpy.data.objects["_autorig_MetaFaceRig"],
      bpy.data.objects["_autorig_InternalFaceRig"]
  ]

  path = os.path.split(bpy.data.filepath)[0]
  path = os.path.join(path, "FacialAutoRigger")
  path = os.path.join(path, "data.json")
  
  print(path)

  ret = json.dumps(saveObjects(obs))
  file = open(path, "w")
  file.write(ret)
  file.close()
  
def loadInternalData():
  path = os.path.split(bpy.data.filepath)[0]
  path = os.path.join(path, "FacialAutoRigger")
  path = os.path.join(path, "data.json")
  
  print(path)

  file = open(path, "r")
  ret = file.read()
  file.close()
  
  return json.loads(ret)
