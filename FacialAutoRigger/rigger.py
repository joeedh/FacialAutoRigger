import bpy, bmesh
from mathutils import *
from math import *

from .data import basePositions;
from .utils import getMeshObject, DAGSortBones
from .cage import makeDeformMesh, simpleMeshDeformBind, simpleMeshDeformDeform
from .rig_utils import RigMaker
from .spline import *

def genBasePositions(meta):
    arm = meta.data
    pose = meta.pose
    def bloc(name):
        if name not in arm.bones: 
            print("Error: missing bone in armature data: ", name)            
            return Vector()
        
        loc = arm.bones[name].head
        loc = pose.bones[name].matrix_channel @ loc
        return loc
    
    buf = "basePositions = [\n"
    
    for p in meta.pose.bones:
        loc = bloc(p.name)
        buf += "  ('%s',  %s),\n" % (p.name, repr(loc))
    buf += "]\n"
    
    print("\n", buf, "\n")
    return buf
        
def deformRig(scene, meta, newrig, oldrig, do_action=True, margin=0.0, use_surface_def=False):
    basePositions2 = []
    
    for name, loc0 in basePositions:
        bone = meta.data.bones[name]
        pbone = meta.pose.bones[name]
        
        loc = Vector(bone.head)
        loc = pbone.matrix_channel @ loc
        
        basePositions2.append((name, loc))
    
    ob, vimap, inflate = makeDeformMesh(scene, meta, basePositions, "base", oldrig)
    targetob, targetvimap, targetinflate = makeDeformMesh(scene, meta, basePositions2, "target", oldrig, None)

    ob.hide_viewport = False
    targetob.hide_viewport = False
    
    for i in range(2):
      #i = 1
      ob2 = ob if i else targetob
      eps = inflate if i else targetinflate
      
      bm = bmesh.new()
      bm.from_mesh(ob2.data)
      
      for v in bm.verts:
        v.co += v.normal*eps*margin
      
      bm.to_mesh(ob2.data)
      ob2.data.update()
      #break
    
    #return
    #the rig insn't technically symmetric
    #should fix, for now make sure auto x-mirror
    #is off
    
    arm = meta.data
    pose = meta.pose
    
    defob = getMeshObject("_" + meta.name + "_rigdef", scene)
    defob.location = meta.location
    defob.select_set(True)

    defob.hide_viewport = False
    
    bm2 = bmesh.new()
    
    pose2 = newrig.pose
    arm2 = newrig.data
    bones = list(arm2.bones.keys())
    blocs = []
    
    #mat = Matrix(meta.matrix_world)
    #mat.invert()
    
    #mat = mat2 @ mat
    #mat = mat @ meta.matrix_world
    #imat = Matrix(mat)
    #imat.invert()
    
    boneheads = {}
    bpy.context.view_layer.objects.active = meta
    bpy.ops.object.mode_set(mode="EDIT")
    ebones = meta.data.edit_bones
    
    for bone in ebones:
        boneheads[bone.name] = Vector(bone.head)

    def bloc(name):
        #print(boneheads)
        loc = boneheads[name]
        loc = pose.bones[name].matrix_channel @ loc
        return loc
    
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.context.view_layer.objects.active = newrig
    bpy.ops.object.mode_set(mode="EDIT")
    ebones = newrig.data.edit_bones
    matlens = {}
    
    for name in bones:
        bone = ebones[name]
        #make three edges so we can derive a linear transformation
        
        a = bm2.verts.new(bone.head)
        b = bm2.verts.new(bone.tail)
        bm2.edges.new([a, b])
        
        t1 = bone.tail - bone.head
        t1.normalize()
        
        if abs(t1[2]) > abs(t1[1]) and abs(t1[2]) > abs(t1[0]):
          t2 = Vector([1, 0, 0])
        else:
          t2 = Vector([0, 0, 1])
        
        t2 = t1.cross(t2)
        t2.normalize()
        
        t3 = t2.cross(t1)
        t3.normalize()
        
        t1 = Vector([1, 0, 0])
        t2 = Vector([0, 1, 0])
        t3 = Vector([0, 0, 1])
        
        len1 = (bone.tail - bone.head).length*0.001
        
        matlens[name] = len1
        
        t1 = t1*len1 + a.co
        t2 = t2*len1 + a.co
        t3 = t3*len1 + a.co
        
        bm2.edges.new([a, bm2.verts.new(t1)])
        bm2.edges.new([a, bm2.verts.new(t2)])
        bm2.edges.new([a, bm2.verts.new(t3)])
        
        
        #print(bone.name)
        pass
    ebones = None
    bpy.ops.object.mode_set(mode="OBJECT")
            
    #for name, loc in basePositions:
        #bm2.verts.new(loc)
        
    bm2.to_mesh(defob.data)
    defob.data.update()
    
    defob.modifiers.clear()
    if not use_surface_def:
      mod = defob.modifiers.new("_MeshDeform", "MESH_DEFORM")
      mod.object = ob
      bpy.ops.object.meshdeform_bind({
          "object" : defob,
          "active_object" : defob,
          "modifier" : "_MeshDeform"
      }, modifier="_MeshDeform")
      #"""
    
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    
    defbm = bmesh.new()
    defbm.from_mesh(defob.data)
    defbm.verts.index_update()
    
    if use_surface_def:
      bm.normal_update()
      #bmesh.ops.subdivide_edges(defbm, edges=defbm.edges, cuts=32, use_grid_fill=True)
      bindcos = simpleMeshDeformBind(bm, defbm)
    
    bm.verts.index_update()
    bm.verts.ensure_lookup_table()
    
    for v in bm.verts:
        co2 = targetob.data.vertices[v.index].co
        #v.co += (co2 - v.co)*0.5
        v.co = co2
        
        pass
            
    bm.normal_update()
        
    bm.to_mesh(ob.data)
    ob.data.update()
    
    dgraph = bpy.context.evaluated_depsgraph_get()
    
    if not use_surface_def:
      bm2 = bmesh.new()
      bm2.from_object(defob, dgraph, deform=True, cage=True)
    else:
      bm2 = defbm.copy()
      bm2.verts.index_update()
      
      simpleMeshDeformDeform(bm, bm2, bindcos)
      
      bm2.to_mesh(defob.data)
      defob.data.update()
    
    #bm2 = bmesh.new()
    #bm2.from_object(defob, dgraph, deform=True, cage=True)
    
    #for i, v in bm.verts:
    
    bm2.verts.ensure_lookup_table()
    bpy.context.view_layer.objects.active = newrig
    
    bpy.ops.object.mode_set(mode="EDIT")
    ebones = newrig.data.edit_bones
    pbones = newrig.pose.bones
    
    #linear cage transformation matrices
    bonemats = {}
    
    for i, name in enumerate(bones):
        bone = ebones[name]
        blen2 = matlens[name]
        
        offset = bm2.verts[i*5].co - bone.head;
        
        old = Vector(bone.head)
        oldtail = Vector(bone.tail)
        bone.head = bm2.verts[i*5].co
        bone.tail = bm2.verts[i*5+1].co
        
        dx = (bm2.verts[i*5+2].co - bone.head) / blen2
        dy = (bm2.verts[i*5+3].co - bone.head) / blen2
        dz = (bm2.verts[i*5+4].co - bone.head) / blen2
        
        mat = Matrix([
        [dx[0], dy[0], dz[0]],
        [dx[1], dy[1], dz[1]],
        [dx[2], dy[2], dz[2]]
        ])
        #mat.transpose();
        try:
          pass
          #mat.invert()
        except ValueError:
          print("matrix inversion failure", mat)
          
        mat.resize_4x4()
        
        #mat = Matrix()
        #print(mat)
        bonemats[name] = mat
        
        pbone = pbones[bone.name]
        loc, quat, scale = mat.decompose()
        #scale = (scale[0] + scale[1] + scale[2])/3.0
        scale = min(min(scale[0], scale[1]), scale[2])
        
        #pbone.custom_shape_scale *= scale
        
        
        #mat = Matrix.Translation(offset)
        #print(Matrix.Translation(offset))
        #print("=====", "\n", mat)
        
        #mat.transpose()
        #mat.invert()
        #print(dx, dy, dz, mat)
        #print("\n", mat @ Vector(), "\n", bone.head)
    
    if do_action:
      src_action = bpy.data.actions["FacialPoses"]
      
      action = newrig.animation_data.action
      if action is None or action == src_action:
        action = src_action.copy()
      newrig.animation_data.action = action
      
      def getpath(bone, property):
        return 'pose.bones["%s"].%s' % (bone.name, property)
      
      def getcurve(action, bone, property, array_index=0):
        path = getpath(bone, property)
        
        srcfc = None
        for fc in src_action.fcurves:
          if fc.data_path == path and fc.array_index == array_index:
            srcfc = fc
            break
          
        if srcfc is None:
          raise RuntimeError("failed to find source fcurce")
          
        for fc in action.fcurves:
          if fc.data_path == path and fc.array_index == array_index:
            for i, key in enumerate(fc.keyframe_points):
              fc.keyframe_points[i].co = srcfc.keyframe_points[i].co
              
            return fc


      for pbone in newrig.pose.bones:
        fcx = getcurve(action, pbone, "location", 0)
        fcy = getcurve(action, pbone, "location", 1)
        fcz = getcurve(action, pbone, "location", 2)
        
        if fcx is None:
          print("no animation key for bone", pbone.name)
          continue
        
        mat = bonemats[pbone.name]
        
        l = len(fcx.keyframe_points)
        if len(fcy.keyframe_points) != l or len(fcz.keyframe_points) != l:
          axis = ""
          if len(fcy.keyframe_points) != l:
            axis += " 1"
          if len(fcz.keyframe_points) != l:
            axis += " 2"
            
          print("ERROR missing axis keyframe data for axis" + axis)
          print(len(fcx.keyframe_points), len(fcy.keyframe_points), len(fcz.keyframe_points))
        
        #continue
        kx = fcx.keyframe_points
        ky = fcy.keyframe_points
        kz = fcz.keyframe_points
        
        for i in range(len(kx)):
          co = Vector([kx[i].co[1], ky[i].co[1], kz[i].co[1]])
          #print(co, co - (mat @ co))
          co = mat @ co
          
          kx[i].co[1] = co[0]
          ky[i].co[1] = co[1]
          kz[i].co[1] = co[2]
        
        fcx.update()
        fcy.update()
        fcz.update()
      
    for i in range(len(newrig.data.layers)):
        newrig.data.layers[i] = True
        
    bpy.ops.armature.calculate_roll(type="GLOBAL_NEG_Y")
    
    ebones = None
    bpy.ops.object.mode_set(mode="OBJECT")
    
    #bpy.ops.object.mode_set(mode="POSE")
    #bpy.context.view_layer.objects.active = defob
    
def updateConstraints(newrig, rest_frame=0):
  dgraph = bpy.context.evaluated_depsgraph_get()
  
  #set to rest pose frame
  if rest_frame is not None:
    bpy.context.scene.frame_set(rest_frame)

  #newrig.data.pose_position = "REST"
  newrig.data.update_tag()
  
  bpy.context.view_layer.objects.active = newrig
  bpy.ops.object.mode_set(mode="POSE")
  bpy.ops.pose.select_all(action="DESELECT")
  
  influences = {}
  def getkey(bone, con):
      return bone.name + "_" + con.name

  pbones = newrig.pose.bones
  abones = newrig.data.bones

  def do_update():
      newrig.update_tag(refresh=set(["OBJECT", "DATA", "TIME"]))
      newrig.data.update_tag()
      bpy.context.view_layer.update()
      
      evalrig = newrig.evaluated_get(dgraph)
      evalpose = evalrig.pose
      return evalrig, evalpose
  
  sortnames = DAGSortBones(newrig)
  #print("--->", len(sortnames), len(newrig.pose.bones), len(newrig.data.bones))
  for stepi in range(4):
      do_update()
      
      for name in sortnames:
          pbone = newrig.pose.bones[name]
          abone = newrig.data.bones[pbone.name]
          newrig.data.bones.active = abone
          
          for con in pbone.constraints:
              if con.type == "LIMIT_DISTANCE":
                  inf = con.influence
                  con.influence = 0
                  do_update()
                  
                  #print("Doing limit distance constraint")
                  #print("Reseted stretch to", con.rest_length, "for", pbone.name)
                  
                  target = con.subtarget
                  if target not in pbones:
                    print("bad constraint target", target, "for limit-distance for", pbone.name)
                    continue
                   
                  abone2 = abones[target] 
                  pbone2 = pbones[target]
                  
                  a = pbone2.matrix @ Vector()
                  b = pbone.matrix @ Vector()
                  
                  
                  #l = (abone2.head - abone.head).length
                  l = (a - b).length
                  con.distance = l
                  
                  con.influence = inf
                  do_update()
                  
                  #print("  distance", l)
                  
              if con.type == "STRETCH_TO": # and stepi == 0:
                  #print("Reseted stretch to", con.rest_length, "for", pbone.name)
                  
                  target = con.subtarget
                  if target not in pbones:
                    print("bad constraint target", target, "for stretchto of", pbone.name)
                    continue
                   
                  abone2 = abones[target] 
                  pbone2 = pbones[target]
                  
                  a = pbone2.matrix @ Vector()
                  b = pbone.matrix @ Vector()
                  
                  
                  #l = (abone2.head - abone.head).length
                  l = (a - b).length
                  con.rest_length = l
                  do_update()
              
              #do child of constraints after first pass
              if stepi == 0:
                continue
                
              if con.type == "CHILD_OF":
                  #print("  -> doing child of for bone", pbone.name)
                  
                  key1 = getkey(pbone, con)
                  if key1 not in influences:
                      influences[key1] = con.influence
                      con.influence = 1.0
                  
                  evalrig, evalpose = do_update()

                  if con.subtarget not in pbones:
                    print("missing child off target bone '%s'" % (con.subtarget))
                    continue
                    
                  pmat = evalpose.bones[con.subtarget].matrix
                  #mymat = abone.convert_local_to_pose(pmat, abone.matrix_local)
                  
                  parent = Matrix(pmat)
                  #parent = Matrix(mymat)
                  
                  try:
                    parent.invert()
                  except ValueError:
                    print(parent, "lacks an inverse")
                    parent = Matrix(abone.matrix_local)
                    parent.invert()
                    
                    continue
                  #parent = Matrix(abone.matrix_local)
                  #parent.invert()
                  
                  #print(parent)
                  con.inverse_matrix = parent
                  
 
  for pbone in newrig.pose.bones:
      for con in pbone.constraints:
          key1 = getkey(pbone, con)
          if key1 in influences:
              con.influence = influences[key1]
              
  newrig.data.pose_position = "POSE"
  bpy.ops.object.mode_set(mode="OBJECT")
  do_update()
  
    #bpy.data.objects.remove(defob)
    #bpy.data.objects.remove(ob)
    

def ensureRig(name):
  if name in bpy.data.objects:
    ob = bpy.data.objects[name]
    print(ob.name, ob.name not in bpy.context.scene.objects)

    if ob.name not in bpy.context.scene.objects:
      bpy.context.scene.collection.objects.link(ob)
    return ob
  else:
    ob = bpy.data.objects.new(name, bpy.data.armatures.new(name))
    bpy.context.scene.collection.objects.link(ob)

    return ob

def copyRig(rig, name):
    #copy rig
    rigob = rig
    newname = name
            
    bpy.ops.object.select_all(action="DESELECT")

    ctx = {
        "selected_objects" : [rigob],
        "active_object" : rigob,
    }
    
    rigob.select_set(True)
    ret = bpy.ops.object.duplicate(ctx, mode="DUMMY")
    #print(ret)
    #print(ctx)
    #print(bpy.context.active_object)
    
    rig2 = bpy.context.selected_objects[0]
    #print(rig2)
    
    if newname in bpy.data.objects:
        rig3 = bpy.data.objects[newname]
        rig3.data = rig2.data
        
        bad = False
        
        for p in rig2.pose.bones:
            #XXX FOR TESTING PURPOSES always regen; change back later
            if 1: #p.name not in rig3.pose.bones:
                print("missing bone; full regen")
                bad = True
                break
            #TODO
            #hrm, what to sync?
        if bad:
            #relink modifiers
            for ob in bpy.data.objects:
              if ob.type != "MESH": continue
              for mod in ob.modifiers:
                if not hasattr(mod, "object"): continue
                if mod.object != rig3: continue
                mod.object = rig2
                
            bpy.data.objects.remove(rig3)
            rig2.name = newname
            #relink armature modifiers
        else:
            bpy.data.objects.remove(rig2)
            rig2 = rig3
            
        pass
    else:
        rig2.name = newname
    
    return rig2    


def genShapeKeyRig(scene, meta, rest_frame=1, rigname="FaceRig"):
  oldframe = bpy.context.scene.frame_current
  
  internal_rig = bpy.data.objects["_autorig_InternalFaceRig"]
  
  name = rigname + "_skey_gen"

  newrig = copyRig(internal_rig, name)
  newrig.location = meta.location

  use_mirror_x = newrig.data.use_mirror_x
  newrig.data.use_mirror_x = False

  deformRig(scene, meta, newrig, internal_rig)
  updateConstraints(newrig, rest_frame=rest_frame)
  
  meta.select_set(True)
  bpy.context.view_layer.objects.active = newrig
  
  newrig.data.use_mirror_x = use_mirror_x
  
  bpy.context.scene.frame_set(oldframe)
  bpy.context.view_layer.update()
  
  return newrig

"""
widgets
EyeWidget : 8
NoseWidgetShape : 50
MouthWidget : 15
TweakShape2 : 200
NoseWidgetShape2 : 25
HeadShape2 : 2

"""
def generate(scene, meta, meshob, rigname="FaceRig"):
  if not meta.data.facerig.ismeta:
    meta = meta.data.facerig.metaob
    rigname = meta.data.facerig.rigname 

  name = rigname
  
  newrig = ensureRig(name)
  print("newrig", newrig, name)

  newrig.data.facerig.metaob = meta
  newrig.data.facerig.rigname = meta.data.facerig.rigname
  newrig.data.facerig.ismeta = False
  newrig.data.facerig.meshob = meta.data.facerig.meshob

  arm = newrig.data

  rigger = RigMaker(newrig, newrig.data, bpy.data.objects["DefWidget"], 1000.0)
  
  locs = {}
  loclist = []

  def interp(a, b, t):
    return a + (b - a) * t

  for b in meta.pose.bones:
    b2 = meta.data.bones[b.name]
    loc = b.matrix_channel @ b2.head
    locs[b.name] = loc 
    loclist.append(loc)

    print(b.name, loc)

  print("meta", meta)

  vmin = Vector([1e17, 1e17, 1e17])
  vmax = Vector([-1e17, -1e17, -1e17])
  for loc in loclist:
    for i in range(3):
      vmin[i] = min(vmin[i], loc[i])
      vmax[i] = max(vmax[i], loc[i])

  scale = (vmax - vmin).length

  rigger.widgetScale = scale * 0.1
  rigger.start()

  headhead = Vector([vmax[0]*0.5 + vmin[0]*0.5, vmax[1], vmin[2]])
  headtail = Vector(headhead)
  headtail[2] += (vmax[2] - vmin[2])*0.75
  rigger.getBone("Head", headhead, headtail, layers=0)

  def head():
    return arm.edit_bones["Head"]

  for side in [".L", ".R"]:
    metaeye = locs["Eye" + side]

    eye = rigger.getBone("Eye" + side, metaeye, metaeye + Vector([0,0,scale*0.2]))
    print("eye", eye) 
    eye.use_deform = False
    eye.parent = head()

    a = locs["BrowCenter" + side]
    b = locs["BrowMid" + side]
    c = locs["BrowCorner" + side]

    ta = locs["LidLeft.T" + side]
    tb = locs["LidTop" + side]
    tc = locs["LidRight.T" + side]

    ba = locs["LidLeft.B" + side]
    bb = locs["LidBottom" + side]
    bc = locs["LidRight.B" + side]

    eye_r = (ta - metaeye).length
    
    def makeChain(name, a, b, c, shape=1.0, isLid=True):
      dv = shape * (c - a) / 4.0

      spline = ArchLengthSpline3d([
        [a, a+(b-a)/3.0, b-dv, b],
        [b, b+dv, c-(c-b)/3.0, c]
      ])
      
      chain = rigger.makeBendyChain(name, 4, spline, side, deflayer=1)
      
      ctrl = rigger.getBone(name + "Main" + side, b, b + Vector([0,0,scale*0.05]), widget="default", layers=0).name
      
      if isLid:
        parent = rigger.getBone("MCH-" + name + side, a, c, widget=None, layers=11).name
        parent = arm.edit_bones[parent]
        parent.parent = head()
        parent.use_deform = False

      ctrl = arm.edit_bones[ctrl]

      ctrl.parent = head()
      ctrl.use_deform = False

      #move a little bit in front of chain to avoid numerical instability
      ctrl.head += Vector([0, -scale*0.035, 0.0])
      ctrl.tail += Vector([0, -scale*0.035, 0.0])

      rollaxis = (c - a).cross(ctrl.head - metaeye)
      rollaxis.normalize()

      if isLid:
        parent.align_roll(rollaxis)
        con = rigger.cLockedTrack(parent, ctrl)
        con.lock_axis = "LOCK_Y"
        con.track_axis = "TRACK_NEGATIVE_X"

      eye = arm.edit_bones["Eye" + side]
      
      for i, bname in enumerate(chain):
        bone = arm.edit_bones[bname]
        if isLid:
          bone.parent = parent
        else:
          bone.parent = None

          t = i / (len(chain) - 1)
          t = t*0.9 + 0.1
          t = 1.0 - abs(t-0.5)*2.0

          con = rigger.cChildOf(bone, ctrl, inf=t, name="childof_ctrl")
          con = rigger.cChildOf(bone, head(), inf=1.0-t, name="childof_head")

        if isLid:
          con = rigger.cLimitDistance(bone, eye, mode="LIMITDIST_ONSURFACE")
        else:
          con = rigger.cLimitDistance(bone, eye, mode="LIMITDIST_OUTSIDE")
          
        con.distance = 0.0

        rollaxis2 = (bone.head + bone.tail)*0.5 - ctrl.head
        rollaxis2.normalize()

        bone.align_roll(rollaxis2)

        if not isLid:
          continue

        #continue
        bname2 = "DEF-" + bname
        if bname2 not in arm.edit_bones:
          continue #last ctrl at end of chain
        bone2 = arm.edit_bones[bname2]

        rollaxis2 = bone2.head - metaeye
        bone2.align_roll(rollaxis2)

        con = rigger.cLockedTrack(bone2, "Eye" + side, name="locktomain")
        con.lock_axis = "LOCK_Y"
        con.track_axis = "TRACK_NEGATIVE_Z"
        #not working -> con.use_transform_limit = True
      
    makeChain("Brow", a, b, c, isLid=False)
    makeChain("Lid.T", ta, tb, tc)
    makeChain("Lid.B", ba, bb, bc)
    
    #create blockers
    vec = locs["Forehead" + side] - locs["BrowCenter" + side]
    co1 = a + vec*0.25
    co2 = c + vec*0.25

    blocker = rigger.getBone("DEF-Forehead" + side, co1, co2, layers=12) 
    blocker.parent = head()

    vec = locs["Cheek" + side] - locs["LidBottom" + side]
    co1 = ba + vec*0.75
    co2 = bc + vec*0.75

    blocker = rigger.getBone("DEF-Cheek" + side, co1, co2, layers=12) 
    blocker.parent = head()

    co1 = interp(locs["JawHinge" + side], locs["LidRight.B" + side], 0.5)
    co2 = interp(locs["Temple" + side], locs["BrowCorner" + side], 0.5)

    blocker = rigger.getBone("DEF-Temple" + side, co1, co2, layers=12) 
    blocker.parent = head()

  co1 = locs["BrowCenter.R"]*0.5 + locs["BrowCenter.L"]*0.5
  co2 = locs["Nose"]
  blocker = rigger.getBone("DEF-Nose", co1, co2, layers=12)
  blocker.head[1] += scale*0.04
  blocker.tail[1] += scale*0.04
  blocker.parent = head()

  main = (locs["MouthUpper"] + locs["MouthLower"])*0.5
  main[1] -= scale*0.1
  main = rigger.getBone("Mouth", main, main+Vector([0,0,scale*0.1]), widget="default", layers=0)
  main.use_deform = False
  main.parent = head()

  zip = (locs["MouthUpper"] + locs["MouthLower"])*0.5
  zip[1] -= scale*0.1
  zip = rigger.getBone("Zip", zip, zip+Vector([0,0,scale*0.025]), widget="default", layers=0)
  zip.parent = head()

  bpy.ops.object.mode_set(mode="POSE")
  rigger.resetDistances()

  updateConstraints(newrig, None)
  rigger.stop()

  bpy.ops.object.mode_set(mode="POSE")
  
  return
  
  #base_rig = bpy.data.objects["_autorig_FaceRigBase"]

  #newrig = copyRig(base_rig, name)
  newrig.location = meta.location

  newrig.data.facerig.meshob = meta.data.facerig.meshob
  newrig.data.facerig.rigname = meta.data.facerig.rigname
  
  use_mirror_x = newrig.data.use_mirror_x
  newrig.data.use_mirror_x = False

  deformRig(scene, meta, newrig, base_rig, do_action=False, margin=0, use_surface_def=True)
  updateConstraints(newrig, rest_frame=1)
  
  #meta.select_set(True)
  bpy.context.view_layer.objects.active = newrig
  bpy.ops.object.mode_set(mode="EDIT")
  
  #update EyeTarget, which lies outside the cage
  
  ebones = newrig.data.edit_bones
  #print(list(ebones.keys()))
  ft = ebones["EyeTarget"]
  
  eye1 = ebones["Eye.L"]
  eye2 = ebones["Eye.R"]
  size = (eye1.head - eye2.head).length
  
  ft.head[0] = 0
  ft.head[1] = eye1.head[1] - size*2
  ft.head[2] = eye1.head[2]
  
  ft.tail = ft.head + Vector([0, 0, size*0.5])
  
  bpy.ops.object.mode_set(mode="OBJECT")
  newrig.data.use_mirror_x = use_mirror_x
  
def generateShapeKeyRig(scene, meta, meshob, rigname="FaceRig"):
  #genBasePositions(bpy.data.objects["_autorig_MetaFaceRig"])
  newrig = genShapeKeyRig(scene, meta, rigname=rigname)
  
  mod = None
  
  for md in meshob.modifiers:
    if md.type == "ARMATURE" and md.object == newrig:
      md.show_viewport = True
      mod = md
    elif md.type == "ARMATURE" and md.object != newrig:
      md.show_viewport = False
    
  if mod is None:
    mod = meshob.modifiers.new("autorig1", "ARMATURE")
    mod.object = newrig

  bpy.ops.object.select_all(action="DESELECT")
  meshob.select_set(True)
  newrig.select_set(True)
  bpy.context.view_layer.objects.active = newrig
  
  bpy.ops.object.parent_set(type="ARMATURE_AUTO", xmirror=False)
  