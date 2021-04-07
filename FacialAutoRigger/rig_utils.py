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

  def start(self, ctx=None):
    if ctx is None:
      ctx = bpy.context
    
    self.push(ctx)
    utils.ensureObjectMode(ctx)

    utils.setActiveOb(ctx, self.ob)
    bpy.ops.object.mode_set(mode="EDIT")

  def stop(self, ctx=None):
    if ctx is None:
      ctx = bpy.context
    self.pop(ctx)

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
    pass

  def getPoseBone(self, name):
    pass

  def solveConstraints(self, iterations=3):
    pass

  def getBone(self, name, head, tail, roll=None, widget=None):
    if type(widget) is str:
      widget = self.widgets[widget]
    
    arm = self.arm
    ob = self.ob

    if name in arm.edit_bones:
      bone = arm.edit_bones[name]
    else:
      bone = arm.edit_bones.new(name)

      #blender culls zero-length bones.
      bone.head = Vector(head)
      bone.tail = Vector(tail)

      #update pose channel
      bpy.ops.object.mode_set(mode="OBJECT")
      bpy.ops.object.mode_set(mode="EDIT")

      bone = arm.edit_bones[name]
    
    bone.head = Vector(head)
    bone.tail = Vector(tail)

    return bone

  def cStretchTo(bone, target, inf=1.0):
    pass
  
  def cCopyLocation(bone, target, inf=1.0):
    pass

  def cTrackTo(bone, target, inf=1.0):
    pass

  def cLockedTrack(bone, target, inf=1.0):
    pass

  def cChildOf(bone, target, inf=1.0):
    pass

  def cLimitVolume(bone, target, inf=1.0):
    pass

  def cLimitDistance(bone, target, inf=1.0, mode="OUTSIDE", dis=None):
    if dis is None:
      dis = 0.0 #constraint will reset itself
    

  def makeChain(self, name, segs, spline, suffix="", bone_visit=None):
    spline.checkUpdate()

    slen = spline.length
    s = 0

    ds = 1.0 / segs
    chain = []

    for i in range(segs):
      head = spline.eval(s)
      tail = spline.eval(s + ds)

      name2 = "%s%i%s" % (name, i, suffix)

      bone = self.getBone(name2, head, tail)
      if i > 0:
        self.parentBone(bone, chain[i-1], True)

      chain.append(bone)
      s += ds

    self.doVisit(chain, bone_visit)

    return chain

  def doVisit(bones, visit):
    if not visit:
      return

    for i in range(len(bones)):
      visit(bones[i], i, bones)
  
  def makeBendyChain(self, name, segs, spline, suffix="", bone_visit=None, widget="default"):
    hgt = 0.25 * spline.length / segs

    ctrlchain = []

    def visit(bone, i, chain):
      name2 = "%s%i%s" % (name, i, suffix)
      head = Vector(bone.head)
      tail = Vector(head)
      tail[2] += hgt

      bone2 = self.getBone(name2, head, tail, undefined, widget)
      ctrlchain.append(bone2)

      #name2 = "%s%i

    chain = self.makeChain("DEF-"+name, segs, spline, suffix, visit)

    for i in range(len(ctrlchain)-1):
      a = ctrlchain[i]
      b = ctrlchain[i+1]
      defa = chain[i]
      defb = chain[i+1]

      self.cStretchTo(defa, b)
      self.cCopyLocation(defa, a)

    self.doVisit(chain, chain)
    self.doVisit(chain, ctrlchain)

    return ctrlchain
