import bpy
from bpy.props import *

from .utils import Registrar, RegItem

class ModelSwapListItem (bpy.types.PropertyGroup):
  object : PointerProperty(type=bpy.types.Object)
  
bpy.utils.register_class(ModelSwapListItem)

#motivated by need for seperate lower/upper teeth meshes,
#instead of swapping meshes one at a time we swap them in groups
#
class ModelSwapGroup (bpy.types.PropertyGroup):
  name    : StringProperty(default="unnamed")
  objects : CollectionProperty(type=ModelSwapListItem)
  
#XXX unfortunately seems like we can't defer
#registering this to bpy_exports
bpy.utils.register_class(ModelSwapGroup)

class ModelSwapper(bpy.types.PropertyGroup):
  groups : CollectionProperty(type=ModelSwapGroup)
  active : IntProperty()
  show_all : BoolProperty(default=False)
  
bpy.utils.register_class(ModelSwapper)
  
class FaceRigProps (bpy.types.PropertyGroup):
  teeth_models : PointerProperty(type=ModelSwapper)
  meshob : PointerProperty(type=bpy.types.Object)
  rigname : StringProperty(default="FaceRig")
  metaob : PointerProperty(type=bpy.types.Object)
  devmode : BoolProperty(default=False)
  ismeta : BoolProperty(default=True)

#XXX unfortunately seems like we can't defer
#registering this to bpy_exports
bpy.utils.register_class(FaceRigProps)
  
class OnPostRegister (RegItem):
  def reg(self):
    bpy.types.Armature.facerig = PointerProperty(type=FaceRigProps)
    
bpy_exports = Registrar([
#  ModelSwapList,
#  FaceRigProps,
  OnPostRegister()
])

