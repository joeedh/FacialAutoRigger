import bpy, bmesh
from mathutils import *
from math import *
import bpy

def saveBpyContext(ctx=None):
  ctx = bpy.context if ctx is None else ctx
  
  def idref(id):
    return id.name if id is not None else None
    
  def modesave(ob):
    return ob.mode if ob is not None else None
    
  ret = {}
  if ctx.active_object is not None:
    ret["active_object"] = [ctx.active_object.name, ctx.active_object.mode]
  else:
    ret["active_object"] = None
    
  ret["scene"] = idref(ctx.scene)
  sel = ret["selected_objects"] = []
  
  for ob in ctx.selected_objects:
    sel.append([idref(ob), ob.mode])
  
  return ret

def ensureObjectMode(ctx=None):
  ctx = bpy.context if ctx is None else ctx
  
  if ctx.active_object and ctx.active_object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
    
def setActiveOb(ctx, ob, autoSel=True):
  ctx.view_layer.objects.active = ob
  if autoSel and not ob.select_get(view_layer=ctx.view_layer):
    ob.select_set(True)

def loadBpyContext(rctx, ctx=None):
  ctx = bpy.context if ctx is None else ctx
  
  ensureObjectMode(ctx)
  bpy.ops.object.select_all(action="DESELECT")
  
  mode = "OBJECT"
  
  for obname, mode2 in rctx["selected_objects"]:
    ob = bpy.data.objects[obname]
    if not ob: continue
    
    ob.select_set(True)
    mode = mode2
  
  if rctx["active_object"]:
    obname, mode = rctx["active_object"]
    print(obname)
    
    ob = bpy.data.objects[obname]
    if ob:
      ctx.view_layer.objects.active = ob
      
  if mode != "OBJECT":
    bpy.ops.object.mode_set(mode=mode)
  
def decompose_path(context, path):
  
  #a = path[:path.find(".")]
  #b = None
  #path = path[len(a)+1:]
  
  nlist = [""]
  
  #root = [a, None, ".", None]
  #node = [a, None, "", None]
  #word = ""
  
  for c in path:
    if c in ["."]:
      if len(nlist[-1]) == 0:
        nlist = nlist[:-1]
      nlist.append(c)
      nlist.append("")
    elif c == "]":
      #nlist.append(c)
      nlist.insert(len(nlist)-1, '[')
      #nlist.append(']')
      nlist.append("")
      pass
    elif c == "[":
      nlist.append("")
      #nlist.append("")
      continue
    else:
      nlist[-1] += c
  
  #print(nlist)
  vlist = []
  trace = []
  
  obj = context
  i = 0
  while i < len(nlist):
    if i > 0:
      prev = nlist[i-1]
    else:
      prev = None
    
    #print("item", nlist[i])
    #print("prev", prev)
    
    item = nlist[i]
    
    trace.append(item)
    vlist.append(obj)
    
    if prev is None or prev == ".":
      try:
        obj = getattr(obj, nlist[i])
      except:
        obj = None
    elif prev == "[":
      if "'" not in item and '"' not in item:
        item = int(item)
        
      try:
        obj = obj[item]
      except IndexError:
        obj = None
        
      pass
    i += 2
    
  vlist.append(obj)
  
  #obj = getattr(obj, k)
  #print("vlist", vlist)
  #print("object", obj)
  return trace, vlist
  
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
  
def getMeshObject(name, scene):
    print("NAME", name)
    
    if name not in bpy.data.objects:
        ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
        cll = bpy.context.scene.collection
        cll.objects.link(ob)
    
    ob = bpy.data.objects[name]
    if ob.name not in scene.objects:
      scene.collection.objects.link(ob)
      print("OB " + name + " is NOT IN SCENE! adding...");
    return ob
    
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
