from mathutils import *
from math import *
import time, random

from . import utils

import bpy, bmesh

def getObject(name, type):
  if name in bpy.data.objects:
    ob = bpy.data.objects[name]
  else:
    if type == "ARMATURE":
      data = bpy.data.armatures.new(name)
    elif type == "MESH":
      data = bpy.data.meshes.new(name)

    ob = bpy.data.objects.new(name, data)

  scene = bpy.context.scene
  coll = scene.collection

  if ob.name not in coll.all_objects:
    coll.objects.link(ob)

  return ob

def getArmature(name):
  return getObject(name, "ARMATURE")

class Widget:
  def __init__(self, name, ob, scale=1.0):
    self.name = name
    self.ob = ob
    self.scale = scale

class RigMaker:
  def __init__(self, ob, arm, defaultWidget, defaultWidgetScale=1.0):
    self.ob = ob
    self.arm = arm
    self.widgets = {}
    self.addWidget("default", defaultWidget, defaultWidgetScale)
    self._stack = []
    self.widgetScale = 1.0
    self.startLayers = None

  def start(self, ctx=None):
    if ctx is None:
      ctx = bpy.context
    
    self.push(ctx)
    utils.ensureObjectMode(ctx)

    utils.setActiveOb(ctx, self.ob)

    self.startLayers = list(self.ob.data.layers)
    
    for i in range(len(self.ob.data.layers)):
      self.ob.data.layers[i] = True

    #paranoia check to make sure pose bones are flushed properly
    bpy.ops.object.mode_set(mode="OBJECT")

    #now enter armature edit mode
    bpy.ops.object.mode_set(mode="EDIT")

  def stop(self, ctx=None):
    if ctx is None:
      ctx = bpy.context
    self.pop(ctx)

    if not self.startLayers:
      return

    for i in range(len(self.ob.data.layers)):
      self.ob.data.layers[i] = self.startLayers[i]

  def push(self, ctx=None):
    if ctx is None:
      ctx = bpy.context
    
    self._stack.append([ctx, utils.saveBpyContext(ctx)])
  
  def pop(self, ctx=None):
    oldctx, data = self._stack.pop()

    if ctx is None:
      ctx = oldctx
    
    utils.loadBpyContext(data, ctx)

  def addWidget(self, name, ob, scale=1.0):
    self.widgets[name] = Widget(name, ob, scale)

  def parentBone(self, bone, parent, connected=False):
    if type(parent) is str:
      parent = self.arm.edit_bones[parent]
    if type(bone) is str:
      bone = self.arm.edit_bones[bone]
    
    bone.parent = parent

  def solveConstraints(self, iterations=3):
    pass

  def getBone(self, name, head, tail, roll=None, widget=None, layers=None):
    if type(widget) is str:
      widget = self.widgets[widget]
    
    arm = self.arm
    ob = self.ob

    head = Vector(head)
    tail = Vector(tail)

    if (tail - head).length < 0.0001:
      tail += Vector([0, 0, 0.01])

    if name in arm.edit_bones:
      bone = arm.edit_bones[name]
    else:
      bone = arm.edit_bones.new(name)

      #blender culls zero-length bones.
      bone.head = Vector(head)
      bone.tail = Vector(tail)

      print(head, tail)
      
      #update pose channel
      bpy.ops.object.mode_set(mode="OBJECT")
      bpy.ops.object.mode_set(mode="EDIT")

      bone = arm.edit_bones[name]
    
    bone.head = Vector(head)
    bone.tail = Vector(tail)

    if widget is not None:
      pbone = self.poseBone(bone)
      pbone.custom_shape = widget.ob
      pbone.custom_shape_scale = widget.scale * self.widgetScale

    if layers is not None:
      bone.layers[0] = False
      
      if type(layers) == int:
        bone.layers[layers] = True
      else:
        for layer in layers:
          bone.layers[layer] = True

    return bone

  def resetDistances(self):
    cons = []
    types = set(["LIMIT_DISTANCE", "STRETCH_TO"])
        
    for bone in self.ob.pose.bones:
      print(bone.name)

      for con in bone.constraints:
        if not con.name.startswith("RIG-"):
          continue

        print("Found " + con.name, con.type)

        if con.type in ["LIMIT_DISTANCE"]:
          con.distance = 0.0
        elif con.type == "STRETCH_TO":
          con.rest_length = 0.0
          
  def _getCon(self, bone, ctype, name, subtarget=None, inf=1.0, prefix="RIG-"):
    name = prefix + name

    pbone = self.poseBone(bone)
    for c in pbone.constraints:
      if c.name == name:
        return c
    
    c = pbone.constraints.new(ctype)
    c.name = name
    c.influence = inf 

    if subtarget is not None:
      if type(subtarget) != str:
        subtarget = subtarget.name

      c.target = self.ob 
      c.subtarget = subtarget

    return c

  def cStretchTo(self, bone, target, inf=1.0, name="stretchto"):
    pbone = self.poseBone(bone)

    print("Making constraint to", bone.name, pbone.name)

    con = self._getCon(bone, "STRETCH_TO", name, subtarget=target, inf=inf)
  
    con.rest_length = 0 #flag distance reset
  
  def poseBone(self, bone):
    if type(bone) != str:
      bone = bone.name
    
    return self.ob.pose.bones[bone]
    
  def cCopyLocation(self, bone, target, inf=1.0, name="copyloc"):
    con = self._getCon(bone, "COPY_LOCATION", name, subtarget=target, inf=inf)
      
  def cTrackTo(self, bone, target, inf=1.0, name="trackto"):
    pass

  def cLockedTrack(self, bone, target, inf=1.0, name="lockedtrack"):
    con = self._getCon(bone, "LOCKED_TRACK", name, subtarget=target, inf=inf)

    return con

  def cChildOf(self, bone, target, inf=1.0, name="childof"):
    return self._getCon(bone, "CHILD_OF", name, subtarget=target, inf=inf)

  def cLimitVolume(self, bone, target, inf=1.0, name="limitvolume"):
    pass

  def cLimitDistance(self, bone, target, inf=1.0, mode="OUTSIDE", dis=0.0, name="limitdistance"):
    #if dis is None:
    #  dis = 0.0 #constraint will reset itself
    con = self._getCon(bone, "LIMIT_DISTANCE", name, subtarget=target)
    con.limit_mode = mode

    return con

  def makeChain(self, name, segs, spline, suffix="", bone_visit=None, layers=None, parentBones=True):
    spline.checkUpdate()

    slen = spline.length
    s = 0

    ds = slen / segs
    chain = []

    for i in range(segs):
      head = spline.eval(s)
      tail = spline.eval(s + ds)

      name2 = "%s%i%s" % (name, i+1, suffix)

      bone = self.getBone(name2, head, tail, layers=layers)

      if i > 0 and parentBones:
        self.parentBone(bone, chain[i-1], True)

      chain.append(name2)
      s += ds

    arm = self.arm
    chain2 = [arm.edit_bones[s] for s in chain]

    self.doVisit(chain2, bone_visit)

    return chain

  def doVisit(self, bones, visit):
    if not visit:
      return

    for i in range(len(bones)):
      visit(bones[i], i, bones)
  
  def makeBendyChain(self, name, segs, spline, suffix="", bone_visit=None, widget="default", layers=None, deflayer=10):
    hgt = 0.25 * spline.length / segs

    arm = self.arm 
    ctrlchain = []

    def visit(bone, i, chain):
      name2 = "%s%i%s" % (name, i+1, suffix)
      head = Vector(bone.head)
      tail = Vector(head)
      tail[2] += hgt

      bone2 = self.getBone(name2, head, tail, None, widget, layers=layers)
      bone2.use_deform = False
      ctrlchain.append(name2)

      #name2 = "%s%i

    chain = self.makeChain("DEF-"+name, segs, spline, suffix, visit, layers=deflayer, parentBones=False)

    deflast = arm.edit_bones[chain[-1]]

    name2 = "%s%i%s" % (name, len(chain)+1, suffix)
    head = Vector(deflast.tail)
    tail = Vector(head)
    tail[2] += hgt

    bone2 = self.getBone(name2, head, tail, None, widget, layers=layers)
    bone2.use_deform = False
    ctrlchain.append(name2)
    
    ctrlchain2 = [arm.edit_bones[s] for s in ctrlchain]
    chain2 = [arm.edit_bones[s] for s in chain]

    for i in range(len(chain)):
      a = ctrlchain2[i]
      b = ctrlchain2[i+1]
      defa = chain2[i]
      
      self.cCopyLocation(defa, a)
      self.cStretchTo(defa, b)

    
    self.doVisit(chain2, bone_visit)
    self.doVisit(ctrlchain2, bone_visit) 

    return ctrlchain
