import bpy
from bpy.props import *

from .utils import Registrar
import re

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
  
class AddSwappableMesh(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.facerig_add_swappable_mesh"
    bl_label = "Internal Face Rigger Operator"
    bl_options = {'UNDO'}

    #path to entry to insert before
    path: StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.armature

    def execute(self, context):
        print("PATHS", self.path)
        
        arm = context.armature
        trace, values = decompose_path(arm, self.path)
        mset = values[-3]
        index = int(trace[-1])
        
        lst = [obj.object for obj in mset.objects]
        lst.insert(index, None)
        
        mset.objects.clear()
        for l in lst:
          mset.objects.add()
          mset.objects[-1].object = l
          
        
        #print(trace, values)
        
        return {'FINISHED'}

class RemSwappableMesh(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.facerig_rem_swappable_mesh"
    bl_label = "Internal Face Rigger Operator"
    bl_options = {'UNDO'}

    #path to entry to insert before
    path: StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.armature

    def execute(self, context):
        print("PATHS", self.path)
        
        arm = context.armature
        trace, values = decompose_path(arm, self.path)
        
        mset = values[-3]
        index = int(trace[-1])
        
        lst = [obj.object for obj in mset.objects]
        lst.pop(index)
        
        mset.objects.clear()
        for l in lst:
          mset.objects.add()
          mset.objects[-1].object = l
          
        
        #print(trace, values)
        
        return {'FINISHED'}

class AddSwappableMeshGroup(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.facerig_add_swappable_mesh_group"
    bl_label = "Internal Face Rigger Operator"
    bl_options = {'UNDO'}

    path: StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        print("PATH", self.path)
        
        arm = context.armature
        trace, values = decompose_path(arm, self.path)
          
        print(trace, values)
        
        lst = values[-1]
        group = lst.groups.add()
        group.name = "unnamed"
        
        return {'FINISHED'}

class RemSwappableMeshGroup(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.facerig_rem_swappable_mesh_group"
    bl_label = "Internal Face Rigger Operator"
    bl_options = {'UNDO'}
    
    path: StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.armature is not None

    def execute(self, context):
        print("PATHS", self.path)
        
        return {'FINISHED'}

def makeSwappableDriver(basepath, mswap, arm, obj, ctrlpath, i):
  anim = obj.animation_data
  
  def getFCurve(path):
    for d in anim.drivers:
      if d.data_path == ctrlpath:
        return d
    
    return anim.drivers.new(ctrlpath)
    
  path = basepath + ".active"
  print("yay")
  print(basepath)
  print(path)
  print(ctrlpath)
  
  fc = getFCurve(path)
  #if fc.driver is None:
  #  fc.driver_add()
  
  driver = fc.driver
  
  vars = driver.variables
  for j in range(len(vars)):
    vars.remove(vars[0])
  
  showall = vars.new()
  showall.name = "show_all"
  showall.type = "SINGLE_PROP"
  showall = showall.targets[0]
  
  active = vars.new()
  active.name = "active"
  active.type = "SINGLE_PROP"
  active = active.targets[0]
  
  showall.id_type = "ARMATURE"
  showall.id = arm
  active.id_type = "ARMATURE"
  active.id = arm
  
  showall.data_path = basepath + ".show_all"
  active.data_path = basepath + ".active"
  
  driver.type = "SCRIPTED"
  driver.expression = "active != %i and not show_all" % (i)
  
  print(fc)
  
def makeSwappableDrivers(basepath, mswap, arm):
  for i, group in enumerate(mswap.groups):
    for ob in group.objects:
      ob = ob.object
      
      if ob.animation_data is None:
        ob.animation_data_create()
      
      makeSwappableDriver(basepath, mswap, arm, ob, "hide_viewport", i)
      makeSwappableDriver(basepath, mswap, arm, ob, "hide_render", i)
      
    
class MakeSwappableMeshDrivers(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.facerig_make_swap_drivers"
    bl_label = "Internal Face Rigger Operator"
    bl_options = {'UNDO'}
    
    path: StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.armature is not None

    def execute(self, context):
        print("PATHS", self.path)
        
        arm = context.armature
        
        trace, values = decompose_path(arm, self.path)
        mswap = values[-1]
        
        print(trace, values)
        print("making drivers!", mswap)
        makeSwappableDrivers("facerig." + trace[-1], mswap, arm)
        
        return {'FINISHED'}
    
    
bpy_exports = Registrar([
  AddSwappableMesh,
  RemSwappableMesh,
  AddSwappableMeshGroup,
  RemSwappableMeshGroup,
  MakeSwappableMeshDrivers
])
