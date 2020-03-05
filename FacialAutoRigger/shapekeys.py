import bpy, bmesh
from mathutils import *
from math import *

no_vgroup_add = set([
    "JawSide.R", 
    "JawSide.L"
])

keys = [
    "Basis",  #1 don't change this, it's not baked in the same way as the others
    "Zip", #2
    "Wide.L", #3
    "Wide.R", #4
    "UpperLip.L", #5
    "UpperLip.R", #6
    "LowerLip.L", #7
    "LowerLip.R", #8
    "UpperMidLip", #9
    "LowerMidLip", #10
    "UpperLid.L", #11
    "UpperLid.R", #12
    "UpperLidSquint.L", #13
    "UpperLidSquint.R", #14
    "LowerLid.L", #15
    "LowerLid.R", #16
    "LowerLidSquint.L", #17
    "LowerLidSquint.R", #18
    "Purse", #19
    "FricitiveSound", #20
    "BrowSqeeze.L", #21
    "BrowSqeeze.R", #22
    "BrowUp.L",     #23
    "BrowUp.R", #24
    "JawDown", #25
    "JawSide.R", #26
    "JawSide.L" #27
];

def get_shapekey(ob, name):
    me = ob.data
    
    if me.shape_keys is None or len(me.shape_keys.key_blocks) == 0:
        #add basis key
        ob.shape_key_add(name="Basis")
        me.shape_keys.use_relative = True
        
    if name not in me.shape_keys.key_blocks:
        ob.shape_key_add(name=name)
    
    return me.shape_keys.key_blocks[name]

def generate_facial_rig(ob, dgraph, scene):
    vgname = "FaceShapeKeyMirrorMask"
    if vgname + ".R" not in ob.vertex_groups:
        if vgname + ".R" not in ob.vertex_groups:
            ob.vertex_groups.new(name=vgname + ".R")
        if vgname + ".L" not in ob.vertex_groups:
            ob.vertex_groups.new(name=vgname + ".L")
        
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        vg = ob.vertex_groups[vgname]
        vgr = ob.vertex_groups[vgname + ".R"].index
        vgl = ob.vertex_groups[vgname + ".L"].index
        
        mdef = bm.verts.layers.deform.active

        xmin = 1000000
        xmax = -1000000
        for v in bm.verts:
            xmin = min(v.co[0], xmin)
            xmax = max(v.co[0], xmax)
        
        blend_wid = (xmax - xmin) * 0.025;
        
        for v in bm.verts:
            t = min(max(v.co[0], -blend_wid), blend_wid) / blend_wid;
            t = t*0.5 + 0.5;
            
            v[mdef][vgr] = t
            v[mdef][vgl] = 1.0 - t
            #print(v[mdef][vgi])
            #break
        
        bm.to_mesh(ob.data)
        ob.data.update()
        #return
        
    startframe = scene.frame_current
    
    was_muted = {}
    
    #mute all keys so they don't interfere with anything
    if me.shape_keys is not None:
        for skey in me.shape_keys.key_blocks:
            was_muted[skey.name] = skey.mute
            skey.mute = True
    
    defmap = []
    
    frame = 1;
    for k in keys:
        skey = get_shapekey(ob, k)
        scene.frame_set(frame)
        frame += 1
        
        skey.vertex_group = ""
        if not skey.vertex_group and k not in no_vgroup_add:
            if k.endswith(".R"):
                skey.vertex_group = vgname + ".R"
            elif k.endswith(".L"):
                skey.vertex_group = vgname + ".L"
                
        ob2 = ob.evaluated_get(dgraph)
        
        bm = bmesh.new()
        bm.from_object(ob2, dgraph, cage=True, deform=True)

        data = skey.data
        
        #if we're the first (basis) key, 
        #build correction offsets for armature
        #deformation in rest post (which is frame zero).
        if k == keys[0]:
            for i, v in enumerate(bm.verts):
                defmap.append(-(v.co - data[i].co))
        else:
            for i, v in enumerate(bm.verts):
                data[i].co = v.co + defmap[i]

    #unmute keys
    if me.shape_keys is not None:
        for skey in me.shape_keys.key_blocks:
            if skey.name in was_muted:
                skey.mute = was_muted[skey.name]
            else:
                skey.mute = False
        
            #XXX
            skey.mute = False
            
    scene.frame_set(startframe)        
    

ob = bpy.context.object
me = ob.data
bm = bmesh.new()
bm.from_mesh(me)

dgraph = bpy.context.evaluated_depsgraph_get()
scene = bpy.context.scene

generate_facial_rig(ob, dgraph, scene)
