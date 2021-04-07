import bpy
from bpy.props import *

class ArmaturePanel (bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        return context.armature

def drawSwappableList(layout, context, prop):
  ob = context.object
  arm = context.armature
  space = context.space_data
  
  facerig = arm.facerig
  
  col = layout.column()
    
  row = col.row()
  row.alignment = "LEFT"

  op = row.operator("object.facerig_add_swappable_mesh_group", text="+")
  op.path = "facerig." + prop
  
  for i, item in enumerate(getattr(facerig, prop).groups):
    #print("ITEM", item.objects, prop)
    
    row = col.row(align=True)
    row.alignment = "LEFT"
    row.prop(item, "name", text="")

    box = col.box()

    op = row.operator("object.facerig_add_swappable_mesh", text="+")
    op.path = "facerig." + prop + ".groups[%i].objects[0]" % (i)
    
    op = row.operator("object.facerig_rem_swappable_mesh_group", text="x")
    op.path = "facerig." + prop + ".groups[%i]" % (i)
    
    col2 = box.column()
    
    for j, item2 in enumerate(item.objects):
      row2 = col2.row()
      row2.alignment = "LEFT"
      row2.prop(item2, "object", text="")
      #row2.label(text="-")
      #row2.label(text="^")
      #row2.label(text="v")
      
      op = row2.operator("object.facerig_rem_swappable_mesh", text="-")
      op.path = "facerig." + prop + ".groups[%i].objects[%i]" % (i, j)
      
    #layout.prop(item, "object"
  
class DATA_PT_FaceRigPanel(ArmaturePanel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Face Auto Rigger"

    
    def draw(self, context):
      layout = self.layout
      
      ob = context.object
      arm = context.armature
      space = context.space_data

      ob = context.object
      arm = context.armature
      space = context.space_data
      
      facerig = arm.facerig
      
      col = layout.column()
      
      col.prop(arm.facerig, "meshob", text="Model");
      col.prop(arm.facerig, "rigname", text="Rig Name");
      col.prop(arm.facerig, "devmode", text="DevMode");
      
      op = col.operator("object.facerig_gen_shapekey_rig");
      op = col.operator("object.facerig_gen_shapekeys");
      op = col.operator("object.facerig_gen_vgroups");
      op = col.operator("object.facerig_update_final");  
      op = col.operator("object.facerig_make_shape_drivers")

      op = col.operator("object.facerig_make_swap_drivers", text="Make Swap Drivers")
      op.path = "facerig.teeth_models"
    
      box = layout.box()
      box.label(text="Teeth Swap Meshes")
      drawSwappableList(box, context, "teeth_models")
      
  
class DATA_PT_FaceRigCtrl(ArmaturePanel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Face Auto Rigger"

    def draw(self, context):
      layout = self.layout
      
      ob = context.object
      arm = context.armature
      space = context.space_data
    
      layout.prop(arm.facerig.teeth_models, "active")
      layout.prop(arm.facerig.teeth_models, "show_all")
      
      
from .utils import Registrar
bpy_exports = Registrar([
  DATA_PT_FaceRigPanel,
  DATA_PT_FaceRigCtrl
])
