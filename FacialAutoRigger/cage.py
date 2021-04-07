import bpy, bmesh
from mathutils import *
from math import *
from mathutils.bvhtree import *

from .data import basePositions;
from .utils import getMeshObject, setWidgetShapes

def getTangentSimple(f):
  vs = list(f.verts)
  
  t1 = vs[1].co - vs[0].co
  scale = (vs[1].co - vs[0].co).length
  
  t1 = t1.cross(f.normal)
  t1.normalize()
  
  t1 *= scale
  
  t2 = f.normal.cross(t1)
  t2.normalize()
  t2 *= scale
  
  t3 = Vector(f.normal)
  t3.normalize()
  t3 *= scale
  
  off = (vs[0].co + vs[1].co + vs[2].co) / 3.0

  mat = Matrix([
    [t1[0], t2[0], t3[0], off[0]],
    [t1[1], t2[1], t3[1], off[1]],
    [t1[2], t2[2], t3[2], off[2]],
    [0, 0, 0, 1],
  ])
  
  #mat.transpose()
  #mat.invert()
  #mat.invert()
  
  return mat
  
def simpleMeshDeformBind(cagebm, bm, eps=0.001):
  bvh = BVHTree.FromBMesh(cagebm, epsilon=eps)
  cagebm.faces.ensure_lookup_table()
  cagebm.normal_update()
  
  bm.verts.index_update()
  bindcos = {}
  
  for v in bm.verts:
    ret = bvh.find_nearest(v.co)
    
    if ret[0] is None: 
      print("simpleMeshDeformBind bind error")
      continue
    
    loc, normal, index, distance = ret
    
    f = cagebm.faces[index]
    mat = getTangentSimple(f)
    
    mat.invert()
    bindcos[v.index] = (index, mat @ v.co)
  
  return bindcos

def simpleMeshDeformDeform(cagebm, bm, bindcos):
  cagebm.faces.ensure_lookup_table()
  cagebm.normal_update()
  
  for v in bm.verts:
    index, loc = bindcos[v.index]
    
    f = cagebm.faces[index]
    mat2 = getTangentSimple(f)
    
    v.co = mat2 @ loc
    
  
def testSimpleMeshDeform(scene, rot_fac=1.0, scale_fac=1.0):
  import random
  
  bm = bmesh.new()
  ob = getMeshObject("testSimpleMeshDeform_cage", scene)
  
  bmesh.ops.create_cube(bm, size=2)
  bm.normal_update();
  
  bm2 = bmesh.new()
  bmesh.ops.create_monkey(bm2)
  bm2.normal_update();
  
  ob2 = getMeshObject("testSimpleMeshDeform_deform", scene)
  
  eul = Euler([rot_fac*random.random()*pi*2, rot_fac*random.random()*pi*2, rot_fac*random.random()*pi*2])
  rmat = eul.to_matrix()
  
  bindcos = simpleMeshDeformBind(bm, bm2)
  for v in bm.verts:
    for i in range(3):
      #v.co[i] += (random.random()-0.5)*0.5
      v.co = rmat @ v.co
      v.co *= scale_fac
      
  bm.normal_update()
  
  simpleMeshDeformDeform(bm, bm2, bindcos)
  
  bm.to_mesh(ob.data)
  ob.data.update()
  
  bm2.to_mesh(ob2.data)
  ob2.data.update()
  
  ob.select_set(True)
  ob2.select_set(True)
  
  
def fixCage(bm, inside_points, eps=0.001):
  bvh = BVHTree.FromBMesh(bm, eps)
  
def makeDeformMeshExperiment(scene, meta, basePositions, prefix, internal_rig):
  ob = getMeshObject(prefix + "_" + meta.name + "cage", scene)

  ob.location = meta.matrix_world @ Vector()

  arm = meta.data
  pose = meta.pose
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
  
  #mat = internal_rig.matrix_world
  
  """
  for bone in internal_rig.data.bones:
    bm.verts.new(bone.head)
    bm.verts.new(bone.tail)
  #"""
  
  for pbone in meta.pose.bones:
    bvert(pbone.name)
  
  bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
  bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
  
  bound = [
      Vector([100000, 100000, 100000]),
      -Vector([100000, 100000, 100000]),
  ];
  
  for v in bm.verts:
      for i in range(3):
          bound[0][i] = min(bound[0][i], v.co[i])
          bound[1][i] = max(bound[1][i], v.co[i])

  size = bound[1] - bound[0]

  
  bm.normal_update()
  eps = 0.1*max(max(size[0], size[1]), size[2])

  for v in bm.verts:
      v.co += v.normal*eps
      v.co[0] *= 1.045
  
  bm.verts.index_update()
  
  vmap = {}
  for k in vsmap:
      vmap[k] = vsmap[k].index
      
  bm.to_mesh(ob.data)
  ob.data.update()

  return ob, vmap, eps

def makeDeformMesh(scene, meta, basePositions, prefix, internal_rig, inflate=None):
    ob = getMeshObject(prefix + "_" + meta.name + "cage", scene)
    
    ob.location = meta.matrix_world @ Vector()
    
    arm = meta.data
    pose = meta.pose
    
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
    fmid2s = [0, 0]
    fmids = [0, 0]
    
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
    
    #"""
    bound2 = [
        Vector([100000, 100000, 100000]),
        -Vector([100000, 100000, 100000]),
    ];
    for bone in meta.pose.bones:
      loc = bloc(bone)
      for j in range(3):
        bound2[0][j] = min(bound[0][j], loc[j])
        bound2[1][j] = max(bound[1][j], loc[j])
    #"""
    
    tops = []
    backs = []
    temples = []
    jawmids = []
    
    for i in range(2):
        swapside = i == 0

        if i == 1:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
            
        eye = [
            bvert("LidTop.R"),
            bvert("LidLeft.T.R"),
            bvert("LidLeft.B.R"),
            bvert("LidBottom.R"),
        ]
        bm.faces.new([
            bvert("LidRight.B.R"),
            bvert("LidRight.T.R"),
            bvert("LidTop.R"),
            bvert("LidBottom.R"),
        ])
        
        bm.faces.new(eye)
        
        #brow = [
        bvert("BrowCorner.R"),
        bvert("BrowCorner.L")
        #]
        
        forehead = bvert("Forehead.R")
        
        #"""
        bm.faces.new([
            bvert("LidTop.R"),
            #bvert("BrowCorner.R"),
            bvert("BrowMid.R"),
            bvert("BrowCenter.R"),
            bvert("LidLeft.T.R"),
        ])
        #"""
        
        #"""
        bm.faces.new([
            bvert("LidRight.T.R"),
            bvert("BrowCorner.R"),
            bvert("BrowMid.R"),
            bvert("LidTop.R"),
        ]);
        #"""
        
        
        #bm.faces.new([
        #    bvert("Nose"),
        #    bvert("LidBottom.R"),
        #    bvert("LidLeft.T.R"),
        #])
        
        ear = bvert("Ear.R");
        ear.co[0] *= 1.1;
        
        temple = bvert("Temple.R")
        temple.co[2] = (temple.co[2] - bound2[0][2])*1.25 + bound2[0][2];
        
        #temple = Vector(ear.co)
        #temple[2] = bvert("Forehead.R").co[2]
        #temple = bm.verts.new(temple)
        
        temples.append(temple)
        
        fmid = bvert("Forehead.R").co*0.5 + bvert("BrowCenter.R").co*0.5;
        fmid[2] = (fmid[2] - bound2[0][2])*1.05 + bound2[0][2];
        fmid = bm.verts.new(fmid)
        
        fmids[i] = fmid
        
        #"""
        bm.faces.new([
            #bvert("BrowMid.R"),
            bvert("BrowCorner.R"),
            temple,
            bvert("Forehead.R"),
            ])
        #"""
        
        #"""
        bm.faces.new([
            bvert("Forehead.R"),
            fmid,
            bvert("BrowCorner.R"),
        ]);
        bm.faces.new([
            bvert("BrowMid.R"),
            bvert("BrowCorner.R"),
            fmid,
        ]);
        bm.faces.new([
            bvert("BrowCenter.R"),
            bvert("BrowMid.R"),
            fmid,
        ]);
        #"""
        
        bm.faces.new([
            bvert("LidRight.T.R"),
            ear,
            temple,
            bvert("BrowCorner.R"),
        ])
        
        
        cheek = bvert("Cheek.R")
        
        #cheek = Vector(bvert("Jawline.R").co)
        #cheek += (bvert("LidBottom.R").co - cheek)*0.6
        #cheek[0] *= 1.1;
        #cheek = bm.verts.new(cheek)
        
        #"""
        bm.faces.new([
            bvert("LidBottom.R"),
            cheek,
            bvert("LidRight.B.R"),
        ])
        bm.faces.new([
          ear,
          bvert("LidRight.T.R"),
          bvert("LidRight.B.R"),
        ])
        bm.faces.new([
          ear,
          bvert("LidRight.B.R"),
          cheek
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
            bvert("LidLeft.B.R"),
            bvert("Nose"),
        ])
        bm.faces.new([
          bvert("LidLeft.B.R"),
          bvert("LidLeft.T.R"),
          bvert("Nose"), 
        ])
        
        #"""
        bm.faces.new([
            bvert("MouthLower"),
            bvert("MouthCorner.R"),
            bvert("MouthUpper"),
        ]);
        #"""
        
        jawmid = Vector(bvert("Chin").co)
        y = jawmid[1]
        y += (bvert("JawHinge.R").co[1] - y)*0.33
        
        jawmid += (bvert("JawHinge.R").co - jawmid)*0.5
        jawmid[1] = y
        jawmid = bm.verts.new(jawmid)
        
        jawmids.append(jawmid)
        
        #"""
        bm.faces.new([
            jawmid,
            bvert("MouthCorner.R"),
            bvert("MouthLower"),
            bvert("Chin"),
        ])
        #"""
        
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
         
        #"""
        bm.faces.new([
           bvert("Ear.R"),
           cheek,
           bvert("JawHinge.R"), 
        ])

        #"""
        bm.faces.new([
           #bvert("Ear.R"),
           cheek,
           bvert("Jawline.R"),            
           bvert("JawHinge.R"), 
        ])
        #"""
                
        """
        bm.faces.new([
            bvert("JawHinge.R"),
            bvert("Ear.R"),
            bvert("Jawline.R"),
            
        ])
        #"""
        
        earco = bvert("Ear.R").co
        y = earco[1]

        #back faces
        
        #estimate back of head
        if i == 0:
            for v in bm.verts:
                for j in range(3):
                    bound[0][j] = min(bound[0][j], v.co[j])
                    bound[1][j] = max(bound[1][j], v.co[j])
            
        size = bound[1] - bound[0]
        backy = bound[0][1] + size[1]*1.75;
        
        backyclose = (bound[0][1] + size[1]*0.1);
        
        #make verts
        back1 = Vector(bvert("JawHinge.R").co)
        
        back1[1] -= backyclose*2.0
        back1 = bm.verts.new(back1)
        
        back2 = Vector(bvert("Ear.R").co)
        back2[1] -= backyclose*2.0
        back2 = bm.verts.new(back2)
        
        back3 = Vector(bvert("JawHinge.R").co)
        back3[0] *= 0.75
        back3[1] = backy
        back3 = bm.verts.new(back3)
        
        back4 = Vector(bvert("Ear.R").co)
        back4[0] *= 0.75
        back4[1] = backy
        back4 = bm.verts.new(back4)
        
        #"""
        bm.faces.new([
            back1, 
            back2,
            bvert("Ear.R"),
            bvert("JawHinge.R"),
            
        ]);
        #"""
        
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
        back6[0] = size[0]*0.3*(-1 if i == 0 else 1)
        back6[2] += size[2]*0.4;
        back6[1] = backy - size[1]*0.25
        back6 = bm.verts.new(back6)
        
        fmid2 = back6.co*0.5 + bvert("Forehead.R").co*0.5
        fmid2[2] = (fmid2[2] - bound2[0][2])*1.1 + bound2[0][2]
        fmid2 = bm.verts.new(fmid2)
        
        fmid2s[i] = fmid2
        
        #"""
        bm.faces.new([
            back6,
            fmid2,
            temple,
        ]);
        bm.faces.new([
            bvert("Forehead.R"),
            temple,
            fmid2,
        ]);
        #"""
        
        #"""
        bm.faces.new([
            back6,
            temple,
            back5
        ]);
        #"""
        
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
    
    #"""
    bm.faces.new([
        bvert("Forehead.L"),        
        bvert("Forehead.R"),
        fmid2s[1],
        fmid2s[0],
        #tops[1],
        #tops[0],
    ]);
    bm.faces.new([
        fmid2s[1],
        tops[1],
        tops[0],
        fmid2s[0],
    ]);
    #"""
    
    backmid = bound[0] + Vector([
        size[0],
        size[1]*1.8,
        bvert("Chin").co[2] - size[2]*0.2,
    ])
    backmid2 = bound[0] + Vector([
        size[0],
        size[1]*2.4,
        bvert("Chin").co[2]+size[2]*0.33,
    ])
    backmid = bm.verts.new(backmid)
    neckmid = bound[0] + Vector([
        size[0],
        size[1]*1.2,
        bvert("Chin").co[2] - size[2]*1.15
    ])
    
    def quad(a, b, c, d):
      return [bm.faces.new([a, b, c, d])]
    
    
    def tri(a, b, c):
      return [bm.faces.new([a, b, c])]
      
    fs = []
    fs += quad(tops[0], tops[1], backs[1][5], backs[0][5])
    fs += quad(backs[1][4], backs[0][4], backs[0][5], backs[1][5])
    fs += quad(backs[0][4], backs[1][4], backs[1][3], backs[0][3])
    fs += tri(backs[1][3], backmid, backs[0][3])
    
    """
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
    fs = [f]
    #"""
    
    #"""
    ret = bmesh.ops.extrude_face_region(bm, geom=fs)
    
    for f in fs:
      bm.faces.remove(f)
    for e in bm.edges[:]:
      if len(e.link_faces) == 0:
        bm.edges.remove(e)
    for v in bm.verts[:]:
      if len(v.link_edges) == 0:
        bm.verts.remove(v)
        
    print(list(ret.keys()))
    print("====================================================")
    for f in ret["geom"]:
      if type(f) != bmesh.types.BMFace:
        continue
        
      for v in f.verts:
          v.co += (backmid2 - v.co)*0.25
          pass
    #bmesh.ops.triangulate(bm, faces=fs)        
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
        bvert("BrowCenter.L", True),
        bvert("BrowCenter.R", True),
        fmids[1],
        fmids[0],
        #bvert("Forehead.R", True),
        #bvert("Forehead.L", True),
    ])
    bm.faces.new([
        fmids[0],
        fmids[1],
        bvert("Forehead.R", True),
        bvert("Forehead.L", True),
    ])
    #"""
    
    #"""
    bm.faces.new([
        bvert("LidLeft.T.L", True),
        bvert("LidLeft.T.R", True),
        bvert("BrowCenter.R", True),
        bvert("BrowCenter.L", True),
    ])
    #"""
    
    bm.faces.new([
        bvert("Nose"),
        bvert("LidLeft.T.R", True),
        bvert("LidLeft.T.L", True),
    ]);
    
    #make sure we have everything
    for bone in meta.pose.bones:
        bvert(bone.name)
        pass
    
    
    #hrm, let's see what convex hull does
    """
    for f in bm.faces[:]:
      bm.faces.remove(f)
      
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
    #"""
    
    bm.normal_update()
    if inflate is None:
      eps = 0.05*max(max(size[0], size[1]), size[2])
    else:
      eps = inflate
      
    for v in bm.verts:
        v.co += v.normal*eps
    
    bm.verts.index_update()
    
    vmap = {}
    for k in vsmap:
        vmap[k] = vsmap[k].index
    
    bm.verts.index_update()
    vs = set(bm.verts)
    
    def min_elen(v):
      ret = 1000.0
      for e in v.link_edges:
        ret = min(ret, (e.verts[1].co - e.verts[0].co).length)
      return ret
      
    #"""
    ret = bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=2, use_grid_fill=True)
    vs2 = []
    
    #print("=============", ret.keys())
    for v in ret["geom"]:
      if type(v) != bmesh.types.BMVert:
        continue
        
      if v in vs: continue
      v.co += v.normal*min_elen(v)*0.35
      vs2.append(v)
    
    for step in range(1):
      bmesh.ops.smooth_vert(bm, verts=vs2, factor=0.75, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    #"""
    
    #bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.normal_update()
    
    bm.to_mesh(ob.data)
    ob.data.update()
    
    return ob, vmap, eps

