import imp

from . import ops, ui, rigger, props, utils, shapekeys, data, cage
from . import spline

imp.reload(data)
imp.reload(utils)
imp.reload(spline)
imp.reload(props)
imp.reload(cage)
imp.reload(ops)
imp.reload(ui)
imp.reload(rigger)
imp.reload(shapekeys)

from .utils import Registrar

bpy_exports = Registrar([
  props.bpy_exports,
  ops.bpy_exports,
  ui.bpy_exports
]);

def register():
  global bpy_exports
  bpy_exports.register()
  
def unregister():
  global bpy_exports
  #bpy_exports.unregister()