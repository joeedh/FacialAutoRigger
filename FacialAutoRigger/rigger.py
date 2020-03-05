import bpy, bmesh
from mathutils import *
from math import *

basePositions = [
  ('MouthUpper',  Vector((0.00944945216178894, -0.8715478777885437, 3.534780979156494))),
  ('MouthLower',  Vector((0.009449453093111515, -0.7684719562530518, 2.958772897720337))),
  ('Chin',  Vector((-3.798869219195922e-09, -0.4771777391433716, 2.0261588096618652))),
  ('Nose',  Vector((-0.009447156451642513, -1.2648979425430298, 4.233251571655273))),
  ('MouthCorner.L',  Vector((-0.9173001646995544, -0.21365341544151306, 3.1923158168792725))),
  ('LidLeft.L',  Vector((-0.48834308981895447, -0.1588311493396759, 4.9903974533081055))),
  ('LidRight.L',  Vector((-1.758155107498169, 0.1618182361125946, 5.14287805557251))),
  ('LidBottom.L',  Vector((-1.261229395866394, -0.0738702192902565, 4.661858558654785))),
  ('LidTop.L',  Vector((-1.0560321807861328, -0.1528165638446808, 5.427489757537842))),
  ('BrowLeft.L',  Vector((-0.20194929838180542, -0.4066941738128662, 5.945296287536621))),
  ('BrowRight.L',  Vector((-1.8342204093933105, 0.026495549827814102, 6.057717323303223))),
  ('Jawline.L',  Vector((-1.3824844360351562, 0.32070180773735046, 2.733058214187622))),
  ('Ear.L',  Vector((-2.510045051574707, 1.6904290914535522, 4.1867547035217285))),
  ('JawHinge.L',  Vector((-2.0363929271698, 1.0894230604171753, 3.1793951988220215))),
  ('Forehead.L',  Vector((-0.6915662884712219, -0.142640620470047, 6.796550273895264))),
  ('Forehead.R',  Vector((0.6915662884712219, -0.142640620470047, 6.796550273895264))),
  ('MouthCorner.R',  Vector((0.9173001646995544, -0.21365341544151306, 3.1923158168792725))),
  ('LidLeft.R',  Vector((0.48834308981895447, -0.1588311493396759, 4.9903974533081055))),
  ('LidRight.R',  Vector((1.758155107498169, 0.1618182361125946, 5.14287805557251))),
  ('LidBottom.R',  Vector((1.261229395866394, -0.0738702192902565, 4.661858558654785))),
  ('LidTop.R',  Vector((1.0560321807861328, -0.1528165638446808, 5.427489757537842))),
  ('BrowLeft.R',  Vector((0.20194929838180542, -0.4066941738128662, 5.945296287536621))),
  ('BrowRight.R',  Vector((1.8342204093933105, 0.026495549827814102, 6.057717323303223))),
  ('Jawline.R',  Vector((1.3824844360351562, 0.32070180773735046, 2.733058214187622))),
  ('Ear.R',  Vector((2.510045051574707, 1.6904290914535522, 4.1867547035217285))),
  ('JawHinge.R',  Vector((2.0363929271698, 1.0894230604171753, 3.1793951988220215))),
  ('Eye.R',  Vector((1.1010305881500244, 1.0515440702438354, 5.223787307739258))),
  ('Eye.L',  Vector((-1.1010305881500244, 1.0515440702438354, 5.223787307739258))),
]

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
        
def makeDeformMesh(meta):
    ob = getMeshObject("_" + meta.name + "cage")
    
    ob.location = meta.matrix_world @ Vector()
    
    arm = meta.data
    pose = meta.pose
    
    setWidgetShapes(meta)
    bases = {}
    for name, loc in basePositions:
        bases[name] = loc
        
    def bloc(name):
        if name not in bases:
            print("Error: missing bone in armature data: ", name)            
            return Vector()
        
        return bases[name]
        """
        loc = arm.bones[name].head
        loc = pose.bones[name].matrix_channel @ loc
        return loc
        #"""
        
    bm = bmesh.new()
    vsmap = {}
    swapside = False
    
    def bvert(name, no_swap=False):
        if swapside and not no_swap and name.endswith(".R"):
            name = name[:-2] + ".L"
            
        if name in vsmap:
            return vsmap[name]
        vsmap[name] = bm.verts.new(bloc(name))
        
        return vsmap[name]

        
    bound = [
        Vector([100000, 100000, 100000]),
        -Vector([100000, 100000, 100000]),
    ];
    
    tops = []
    backs = []
    temples = []
    jawmids = []
    
    for i in range(2):
        swapside = i == 0

        if i == 1:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
            
        print(bloc("LidLeft.R"))
        eye = [
            bvert("LidLeft.R"),
            bvert("LidTop.R"),
            bvert("LidRight.R"),
            bvert("LidBottom.R")
        ]
        
        eye.reverse()
        
        bm.faces.new(eye)
        
        brow = [
            bvert("BrowRight.R"),
            bvert("BrowRight.L")
        ]
        
        forehead = bvert("Forehead.R")
        
        if 1:
            bm.faces.new([
                bvert("LidTop.R"),
                bvert("BrowRight.R"),
                bvert("BrowLeft.R"),
                bvert("LidLeft.R"),

            ])

        
        bm.faces.new([
            bvert("LidRight.R"),
            bvert("BrowRight.R"),
            bvert("LidTop.R"),
        ]);
        
        
        #bm.faces.new([
        #    bvert("Nose"),
        #    bvert("LidBottom.R"),
        #    bvert("LidLeft.R"),
        #])
        
        ear = bvert("Ear.R");
        temple = Vector(ear.co)
        temple[2] = bvert("Forehead.R").co[2]
        temple = bm.verts.new(temple)
        
        temples.append(temple)
        
        bm.faces.new([
            bvert("BrowRight.R"),
            temple,
            bvert("Forehead.R"),
            bvert("BrowLeft.R"),
            ])
        
        bm.faces.new([
            bvert("LidRight.R"),
            ear,
            temple,
            bvert("BrowRight.R"),
        ])
        
        
        cheek = Vector(bvert("Jawline.R").co)
        cheek += (bvert("LidBottom.R").co - cheek)*0.6
        cheek = bm.verts.new(cheek)
        #"""
        
        bm.faces.new([
            bvert("LidBottom.R"),
            cheek,
            ear,
            bvert("LidRight.R"),

        ])
        #"""
            
        bm.faces.new([
            bvert("Nose"),
            bvert("MouthUpper"),
            bvert("MouthCorner.R"),
            cheek
            #bvert("Jawline.R"),
        ]);
        
        #"""
        bm.faces.new([
            cheek,
            bvert("LidBottom.R"),
            bvert("LidLeft.R"),
            bvert("Nose"),
        ])
        
        bm.faces.new([
            bvert("MouthUpper"),
            bvert("MouthCorner.R"),
            bvert("MouthLower")
        ]);
        
        jawmid = Vector(bvert("Chin").co)
        y = jawmid[1]
        y += (bvert("JawHinge.R").co[1] - y)*0.33
        
        jawmid += (bvert("JawHinge.R").co - jawmid)*0.5
        jawmid[1] = y
        jawmid = bm.verts.new(jawmid)
        
        jawmids.append(jawmid)
        
        bm.faces.new([
            jawmid,
            bvert("MouthCorner.R"),
            bvert("MouthLower"),
            bvert("Chin"),
        ])
        
        #"""
        bm.faces.new([
            #bvert("JawHinge.R"),
            bvert("Jawline.R"),
            #bvert("Ear.R"),
            cheek,
            bvert("MouthCorner.R"),
            jawmid,
        ])
        #"""
        
        bm.faces.new([
           bvert("Ear.R"),
           cheek,
           bvert("Jawline.R"), 
        ])
                
        bm.faces.new([
            bvert("JawHinge.R"),
            bvert("Ear.R"),
            bvert("Jawline.R"),
            
        ])
        
        earco = bvert("Ear.R").co
        y = earco[1]

        #back faces
        
        #estimate back of head
        if i == 0:
            for v in bm.verts:
                for i in range(3):
                    bound[0][i] = min(bound[0][i], v.co[i])
                    bound[1][i] = max(bound[1][i], v.co[i])
            
        size = bound[1] - bound[0]
        backy = bound[0][1] + size[1]*1.75;
        
        backyclose = bound[0][1] + size[1]*0.1;
        
        #make verts
        back1 = Vector(bvert("JawHinge.R").co)
        back1[1] -= backyclose
        back1 = bm.verts.new(back1)
        
        back2 = Vector(bvert("Ear.R").co)
        back2[1] -= backyclose
        back2 = bm.verts.new(back2)
        
        back3 = Vector(bvert("JawHinge.R").co)
        back3[0] *= 0.75
        back3[1] = backy
        back3 = bm.verts.new(back3)
        
        back4 = Vector(bvert("Ear.R").co)
        back4[0] *= 0.75
        back4[1] = backy
        back4 = bm.verts.new(back4)
        
        bm.faces.new([
            back1, 
            back2,
            bvert("Ear.R"),
            bvert("JawHinge.R"),
            
        ]);
        
        back5 = Vector(bvert("Forehead.R").co)
        back5[1] = backy
        back5[0] = temple.co[0]
        back5 = bm.verts.new(back5)
        
        #"""
        bm.faces.new([
            back2,
            back5,
            temple,
            bvert("Ear.R"),
            #bvert("Forehead.R"),
        ])
        
        bm.faces.new([
            back5, 
            back2,
            back4
        ])
        #"""
        bm.faces.new([back1, back3, back4, back2])
        
        back6 = Vector(bvert("Forehead.R").co)
        back6 = (back6 + bvert("Forehead.L").co)*0.5
        back6[2] += size[2]*0.4;
        back6[1] = backy - size[1]*0.25
        back6 = bm.verts.new(back6)
        
        
        bm.faces.new([
            back6,
            bvert("Forehead.R"),
            temple,
        ]);
        bm.faces.new([
            back6,
            temple,
            back5
        ]);
        
        tops.append(back6)
        back = [
            None, 
            back1,
            back2,
            back3,
            back4,
            back5,
            back6
        ]
        backs.append(back)
    
    swapside = False
    
    bm.faces.new([
        bvert("Forehead.L"),        
        bvert("Forehead.R"),
        tops[1],
        tops[0],
    ]);
    
    backmid = bound[0] + Vector([
        size[0]*0.5,
        size[1]*2.0,
        bvert("Chin").co[2],
    ])
    backmid2 = bound[0] + Vector([
        size[0]*0.5,
        size[1]*2.4,
        bvert("Chin").co[2]+size[2]*0.33,
    ])
    backmid = bm.verts.new(backmid)
    neckmid = bound[0] + Vector([
        size[0],
        size[1]*1.1,
        bvert("Chin").co[2] - size[2]*0.65
    ])
    
    #"""
    f = bm.faces.new([
        tops[1],
        backs[1][5],
        backs[1][4],
        backs[1][3],
        backmid,
        backs[0][3],
        backs[0][4],
        backs[0][5],
        tops[0]
    ])
    ret = bmesh.ops.extrude_discrete_faces(bm, faces=[f])
    f = ret["faces"][0]
    for v in f.verts:
        v.co += (backmid2 - v.co)*0.25
    bmesh.ops.triangulate(bm, faces=[f])        
    #"""
    
    f = bm.faces.new([
        backmid,
#        backs[1][4],
        backs[1][3], 
        backs[1][1],
        bvert("JawHinge.R"),
        bvert("Jawline.R"),
        jawmids[1],
        bvert("Chin"),
        jawmids[0],
        bvert("Jawline.L"),
        bvert("JawHinge.L"),
        backs[0][1],
        backs[0][3],
    ])
    
    ret = bmesh.ops.extrude_discrete_faces(bm, faces=[f])
    f = ret["faces"][0]
    for v in f.verts:
        v.co += (neckmid - v.co)*0.5
    bmesh.ops.triangulate(bm, faces=[f])        
    
    #some final middle faces
    #"""
    bm.faces.new([
        bvert("BrowLeft.L", True),
        bvert("BrowLeft.R", True),
        bvert("Forehead.R", True),
        bvert("Forehead.L", True),
    ])
    #"""
    
    bm.faces.new([
        bvert("LidLeft.L", True),
        bvert("LidLeft.R", True),
        bvert("BrowLeft.R", True),
        bvert("BrowLeft.L", True),
    ])
    
    bm.faces.new([
        bvert("Nose"),
        bvert("LidLeft.R", True),
        bvert("LidLeft.L", True),
    ]);
    
    #make sure we have everything
    for bone in meta.pose.bones:
        bvert(bone.name)
        pass
    
    bm.normal_update()
    eps = 0.05*max(max(size[0], size[1]), size[2])

    for v in bm.verts:
        v.co += v.normal*eps
    
    bm.verts.index_update()
    
    vmap = {}
    for k in vsmap:
        vmap[k] = vsmap[k].index
        
    bm.to_mesh(ob.data)
    ob.data.update()
    
    return ob, vmap, eps

def deformRig(meta, newrig, oldrig):
    ob, vimap, inflate = makeDeformMesh(meta)
    
    #the rig insn't technically symmetric
    #should fix, for now make sure auto x-mirror
    #is off
    
    use_mirror_x = newrig.data.use_mirror_x
    newrig.data.use_mirror_x = False
    
    arm = meta.data
    pose = meta.pose
    
    setWidgetShapes(meta)
    
    def bloc(name):
        loc = arm.bones[name].head
        loc = pose.bones[name].matrix_channel @ loc
        return loc
    
    defob = getMeshObject("_" + meta.name + "_rigdef")
    defob.location = meta.location
    defob.select_set(True)
    
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

    bpy.context.view_layer.objects.active = newrig
    bpy.ops.object.mode_set(mode="EDIT")
    ebones = newrig.data.edit_bones
    
    for name in bones:
        bone = ebones[name]
        a = bm2.verts.new(bone.head)
        b = bm2.verts.new(bone.tail)
        bm2.edges.new([a, b])
        #print(bone.name)
        pass
    ebones = None
    bpy.ops.object.mode_set(mode="OBJECT")
            
    #for name, loc in basePositions:
        #bm2.verts.new(loc)
        
    bm2.to_mesh(defob.data)
    defob.data.update()
    
    defob.modifiers.clear()
    mod = defob.modifiers.new("_MeshDeform", "MESH_DEFORM")
    mod.object = ob
    
    bpy.ops.object.meshdeform_bind({
        "object" : defob,
        "active_object" : defob
    }, modifier="_MeshDeform")
    
    
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.index_update()
    bm.verts.ensure_lookup_table()
    
    for name, loc in basePositions:
        if name not in vimap:
            print("Error: missing vert map entry for bone " + name);
            continue
        
        loc = bloc(name)
        
        vert = vimap[name]
        v = bm.verts[vert]
        v.co = loc
    
    bm.normal_update()

    for v in bm.verts:
        v.co += v.normal * inflate
        
    bm.to_mesh(ob.data)
    ob.data.update()
    
    dgraph = bpy.context.evaluated_depsgraph_get()
    
    bm2 = bmesh.new()
    bm2.from_object(defob, dgraph, deform=True, cage=True)
    
    #for i, v in bm.verts:
    
    bm2.verts.ensure_lookup_table()
    bpy.context.view_layer.objects.active = newrig
    
    bpy.ops.object.mode_set(mode="EDIT")
    ebones = newrig.data.edit_bones
    
    for i, name in enumerate(bones):
        bone = ebones[name]
        bone.head = bm2.verts[i*2].co
        bone.tail = bm2.verts[i*2+1].co
    
    for i in range(len(newrig.data.layers)):
        newrig.data.layers[i] = True
        
    bpy.ops.armature.calculate_roll(type="GLOBAL_NEG_Y")
    
    ebones = None
    bpy.ops.object.mode_set(mode="OBJECT")

    #bpy.ops.object.mode_set(mode="POSE")
    #bpy.context.view_layer.objects.active = defob
    
    #set to rest pose frame, 0
    bpy.context.scene.frame_set(0)
    
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="DESELECT")
    
    influences = {}
    def getkey(bone, con):
        return bone.name + "_" + con.name
    
    for stepi in range(3):
        break
        for pbone in newrig.pose.bones:
            for con in pbone.constraints:
                key1 = getkey(pbone, con)
                ctx = {
                    "object" : newrig,
                    "constraint" : con,
                    "active_object" : newrig,
                    "active_pose_bone" : pbone,
                    "active_bone" : newrig.data.bones[pbone.name]
                }
            
                if con.type == "STRETCH_TO":
                    bpy.ops.constraints.stretchto_reset(ctx)
                    
                if con.type == "CHILD_OF":
                    print("  -> doing child of for bone", pbone.name)
                    
                    if key1 not in influences:
                        influences[key1] = con.influence
                        con.influence = 1.0
                    
                    ctx = {
                        "object" : newrig,
                        "constraint" : con,
                        "active_object" : newrig,
                        "active_pose_bone" : pbone,
                        "active_bone" : newrig.data.bones[pbone.name]
                    }
                    
                    #if 1:
                    try:
                        print(stepi, con.name)
                        bpy.ops.constraint.childof_clear_inverse(ctx, constraint=con.name, owner="BONE")
                    
                        for i in range(1):
                            bpy.ops.constraint.childof_set_inverse(ctx, constraint=con.name, owner="BONE")
                    except RuntimeError:
                        print("failed to reset child of constraint for " + pbone.name)
                        
                    #bpy.ops.constraint.childof_set_inverse(ctx, constraint=con.name, owner="BONE")
                    
                    con.influence = fac
    for pbone in newrig.pose.bones:
        for con in pbone.constraints:
            key1 = getkey(pbone, con)
            if key1 in influences:
                con.influence = influences[key1]
                
    bpy.ops.object.mode_set(mode="OBJECT")
    newrig.data.use_mirror_x = use_mirror_x
    
    bpy.data.objects.remove(defob)
    bpy.data.objects.remove(ob)
    
#meta = bpy.context.object
meta = bpy.data.objects["MetaFaceRig.001"]
internal_rig = bpy.data.objects["InternalFaceRig"]

def copyRig(rig):
    #copy rig
    rigob = internal_rig
    newname = "My" + rigob.name
            
    bpy.ops.object.select_all(action="DESELECT")

    ctx = {
        "selected_objects" : [rigob],
        "active_object" : rigob,
    }
    
    ret = bpy.ops.object.duplicate(ctx, mode="DUMMY")
    print(ret)
    print(ctx)
    print(bpy.context.active_object)
    
    rig2 = bpy.context.selected_objects[0]
    print(rig2)
    
    if newname in bpy.data.objects:
        rig3 = bpy.data.objects[newname]
        rig3.data = rig2.data
        
        bad = False
        
        for p in rig2.pose.bones:
            #XXX FOR TESTING PURPOSES always regen; change back later
            if p.name not in rig3.pose.bones:
                print("missing bone; full regen")
                bad = True
                break
            #TODO
            #hrm, what to sync?
        if bad:
            bpy.data.objects.remove(rig3)
            rig2.name = newname
        else:
            bpy.data.objects.remove(rig2)
            rig2 = rig3
            
        pass
    else:
        rig2.name = newname
    
    return rig2    
    
genBasePositions(bpy.data.objects["MetaFaceRig"])
newrig = copyRig(internal_rig)
newrig.location = meta.location
deformRig(meta, newrig, internal_rig)
