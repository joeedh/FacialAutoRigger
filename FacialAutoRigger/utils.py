import bpy, bmesh
from mathutils import *
from math import *
import bpy

class DagNode:
  def __init__(self, name):
    self.name = name
    self.inputs = []
    self.outputs = []
    self.tag = 0
    
def DAGSortBones(armob):
  pbones = armob.pose.bones
  abones = armob.data.bones
  
  nodes = {}
  
  for bone in pbones:
    nodes[bone.name] = DagNode(bone.name)
  
  for bone in pbones:
    node = nodes[bone.name]
    
    if bone.parent is not None:
      node.inputs.append(nodes[bone.parent.name])
      nodes[bone.parent.name].outputs.append(node)
      
    for con in bone.constraints:
      if not hasattr(con, "target") or not hasattr(con, "subtarget"):
        continue
      if con.target != armob: continue
      name = con.subtarget
      
      if name not in nodes:
        print("bad bone reference:", name, con.target)
        print("    from bone", bone.name, "constraint", con.name)
        continue
      
      node.inputs.append(nodes[name])
      nodes[name].outputs.append(node)
  
  sortlist = []
  
  TAG1 = 1
  TAG2 = 2
  
  def gettrace(t):
    ret = ""
    for n in t:
      ret += n.name + "->"
    return ret
    
  def rec(n, trace):
    n.tag |= TAG1
    
    for n2 in n.inputs:
      if not (n2.tag & TAG1):
        if n2.tag & TAG2:
          print("Cycle detected in armature", gettrace(trace))
          continue
          
        n2.tag |= TAG2
        rec(n2, trace)
        n2.tag &= ~TAG2
        
    sortlist.append(n.name)

    for n2 in n.outputs:
      if not (n2.tag & TAG1):
        if n2.tag & TAG2:
          print("Cycle detected in armature", gettrace(trace))
          continue
          
        n2.tag |= TAG2
        rec(n2, trace)
        n2.tag &= ~TAG2
    
  for name in nodes:
    node = nodes[name]
    if node.tag & TAG1: continue
    
    rec(node, [])
  
  return sortlist
  
def getMeshObject(name):
    if name not in bpy.data.objects:
        ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
        cll = bpy.context.scene.collection
        cll.objects.link(ob)

    return bpy.data.objects[name]
    
def setWidgetShapes(ob):
    widget = bpy.data.objects["MetaFaceWidget"]
    for bone in ob.pose.bones:
        bone.custom_shape = widget
        bone.use_custom_shape_bone_size = False
        if bone.name in ob.data.bones:
            ob.data.bones[bone.name].show_wire = True
        

class RegItem:
  def __init__(self):
    pass
  
  def reg(self):
    pass
  
  def unreg(self):
    pass
   
class CustomItem (RegItem):
  def __init__(self, reg, unreg):
    self.custom = [reg, unreg]
  
  def reg(self):
    self.custom[0]()
  
  def unreg(self):
    self.custom[1]()

class BPyItem (RegItem):
  def __init__(self, cls):
    self.cls = cls
  
  def reg(self):
    bpy.utils.register_class(self.cls)

  def unreg(self):
    bpy.utils.unregister_class(self.cls)
  
class Registrar (list):
  def __init__(self, list=[]):
    for l in list:
      self.add(l)
    self.registered = False
    
  def add(self, item):
    if type(item) == list:
      item = CustomItem(item[0], item[1])
    elif not isinstance(item, RegItem) and type(item) != Registrar:
      item = BPyItem(item)
    
    self.append(item)
   
  def reg(self):
    self.register()
    
  def unreg(self):
    self.unregister()
    
  def register(self):
    if self.registered:
      return
    
    self.registered = True
    
    for item in self:
      item.reg()
    
  def unregister(self):
    if not self.registered:
      return
    
    self.registered = False
    
    for item in self:
      item.unreg()
