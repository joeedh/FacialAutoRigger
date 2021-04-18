from math import *
from mathutils import *


"""
on factor;
off period;

procedure bez(a, b);
  a + (b - a)*s;

lin := bez(k1, k2);
quad := bez(lin, sub(k2=k3, k1=k2, lin));
cubic := bez(quad, sub(k3=k4, k2=k3, k1=k2, quad));

on fort;

lin;
df(lin, s);

quad;
df(quad, s);
df(quad, s, 2);

cubic;
df(cubic, s);
df(cubic, s, 2);

off fort;
"""

class BezFuncs:
  def __init__(self):
    pass
  
  def evaluate(self, ks, s):
    pass
  
  def dv(self, ks, s):
    pass
  
  def dv2(self, ks, s):
    pass
    
  def curvature(self, ks, s):  
    dv1 = self.dv(ks, s)
    dv2 = self.dv2(ks, s)
    
    ret = dv1[0]*dv2[1] - dv1[1]*dv2[0]
    div = dv2.dot(dv2)**(3 / 2)
    
    if div == 0.0: 
      return 100000000.0 * sign(ret)
    else:
      return ret / div;
    
class Lin (BezFuncs):
  def eval(self, ks, s):
    k1 = ks[0]; k2 = ks[1];
    return k1 + (k2 - k1)*s;
  
  def dv(self, ks, s):
    k1 = ks[0]; k2 = ks[1];
    return k2 - k1;
  
  def dv2(self, ks, s):
    return 0.0

class Quad (BezFuncs):
  def eval(self, ks, s):
    k1 = ks[0]; k2 = ks[1]; k3 = ks[2]
    return ((k1-k2)*s-k1-((k2-k3)*s-k2))*s-((k1-k2)*s-k1)
  
  def dv(self, ks, s):
    k1 = ks[0]; k2 = ks[1]; k3 = ks[2]
    return 2*(k1*s-k1-2*k2*s+k2+k3*s);
  
  def dv2(self, ks, s):
    k1 = ks[0]; k2 = ks[1]; k3 = ks[2]
    return 2*(k1-k2-(k2-k3))

class Cubic (BezFuncs):
  def eval(self, ks, s):
    k1 = ks[0]; k2 = ks[1]; k3 = ks[2]; k4 = ks[3]
    return -(k1*s**3-3*k1*s**2+3*k1*s-k1-3*k2*s**3+6*k2*s**2-3*k2*s+3*k3*s**3-3*k3*s**2-k4*s**3);
  
  def dv(self, ks, s):
    k1 = ks[0]; k2 = ks[1]; k3 = ks[2]; k4 = ks[3]
    return -3*((s-1)**2*k1-k4*s**2+(3*s-2)*k3*s-(3*s-1)*(s-1)*k2)
  
  def dv2(self, ks, s):
    k1 = ks[0]; k2 = ks[1]; k3 = ks[2]; k4 = ks[3]
    return -6*(k1*s-k1-3*k2*s+2*k2+3*k3*s-k3-k4*s)

bezfuncs = [
  0, 0, Lin(), Quad(), Cubic()
];

class BezCurve (list):
  def __init__(self):
    list.__init__(self)
    
    self.order = 4
    
    for i in range(self.order):
      self.append(Vector())
    
    self._axes = None
    self.update()
      
  def update(self):
    self._axes = [
      [], [], []
    ];
    
    for i in range(len(self)):
      self._axes[0].append(self[i][0])
      self._axes[1].append(self[i][1])
      self._axes[2].append(self[i][2])
    
    return self
    
  def evaluate(self, s):
    ret = Vector()
    
    for i in range(3):
      ret[i] = bezfuncs[self.order].evaluate(self._axes[i], s)
    return ret
    
  def dv(self, s):
    ret = Vector()
    
    for i in range(3):
      ret[i] = bezfuncs[self.order].dv(self._axes[i], s)
    return ret

  def dv2(self, s):
    ret = Vector()
    
    for i in range(3):
      ret[i] = bezfuncs[self.order].dv2(self._axes[i], s)
    return ret
    
  def curvature(self, s):
    ret = Vector()
    
    for i in range(3):
      ret[i] = bezfuncs[self.order].curvature(self._axes[i], s)
    return ret
    
  #def setCurvature(self, k1, k2):
  #    pass
  
cubic_eval = Cubic()

#arc length bezier, with frenel frame
class ArcLengthBez3d:
  def __init__(self):
    self.ks = [[0,0,0,0], [0,0,0,0], [0,0,0,0]]
    self.regen = 1
    self.steps = 800
    self.length = 0.0

    self.table = None
    self.tabledv = None
    self.table_t = None

    self.s = 0

  def setPoint(self, x, p):
    self.ks[0][x] = p[0]
    self.ks[1][x] = p[1]
    self.ks[2][x] = p[2]

    self.regen = 1

  def getPoint(self, x):
    p = Vector()
    p[0] = self.ks[0][x]
    p[1] = self.ks[1][x]
    p[2] = self.ks[2][x]

    return p
  
  def checkUpdate(self):
    if self.regen:
      self.update()

  def eval(self, s):
    if self.regen or not self.table:
      self.update()

    i = s / self.length
    i = min(max(i, 0.0), 0.9999999)
    i *= len(self.table)

    t = i
    i = int(i)
    t -= i
    
    tabledv = self.tabledv
    table_t = self.table_t

    if i < len(self.table) - 1:
      a = self.table[i]
      d = self.table[i+1]

      dv1 = tabledv[i]
      dv2 = tabledv[i+1]

      b = a + dv1/3.0
      c = d - dv2/3.0

      x = cubic_eval.eval([a[0], b[0], c[0], d[0]], t)
      y = cubic_eval.eval([a[1], b[1], c[1], d[1]], t)
      z = cubic_eval.eval([a[2], b[2], c[2], d[2]], t)
      
      return Vector([x, y, z])
      return a + (d - a) * t
    elif 1:
      return self.table[i]
    else:
      a = self.table[i]
      d = self.table[i]

      dv1 = tabledv[i]
      dv2 = tabledv[i]

      b = a + dv1/3.0
      c = d - dv2/3.0

      x = cubic_eval.eval([a[0], b[0], c[0], d[0]], t)
      y = cubic_eval.eval([a[1], b[1], c[1], d[1]], t)
      z = cubic_eval.eval([a[2], b[2], c[2], d[2]], t)
      
      return Vector([x, y, z])
      return a + (d - a) * t

  def safeS(self, s):
    eps = self.length / self.steps * 100.0

    if s < eps:
      s = eps
    elif s > self.length - eps:
      s = self.length - eps

    return s

  def dv(self, s):
    s = self.safeS(s)

    if self.regen or not self.table:
      self.update()

    i = s / self.length
    i = min(max(i, 0.0), 0.9999999)
    i *= len(self.table)

    t = i
    i = int(i)
    t -= i
    
    tabledv = self.tabledv
    table_t = self.table_t

    if i < len(self.table) - 1:
      a = self.table_t[i]
      b = self.table_t[i+1]

      t2 = a + (b - a) * t;

      dx = cubic_eval.dv(self.ks[0], t2);
      dy = cubic_eval.dv(self.ks[1], t2);
      dz = cubic_eval.dv(self.ks[2], t2);

      dv = Vector([dx, dy, dz])
      dv.normalize()

      return dv
    elif 1:
      return self.tabledv[i] * self.steps

  def dv_old(self, s):
    s = self.safeS(s)
    ds = 2.5 * self.length / self.steps #1.2 / self.steps

    if s > ds and s < 1.0 - ds:
      a = self.eval(s-ds)
      b = self.eval(s+ds)
      return (b - a) / (2.0 * ds)
    elif s < ds:
      a = self.eval(s)
      b = self.eval(s+ds)
      return (b - a) / ds
    else:
      a = self.eval(s-ds)
      b = self.eval(s)
      return (b - a) / ds

  def frenetFrame(self, s):
    y = self.dv(s)
    z = self.normal(s)
    x = Vector(y).cross(z)

    x.normalize()
    y.normalize()
    z.normalize()
    x = list(x)
    y = list(y)
    z = list(z)
    
    p = self.eval(s)
    w = list(p) + [1.0]

    m = Matrix([x + [0], y + [0], z + [0], w])
    m.transpose()

    return m

  def dv2(self, s):
    s = self.safeS(s)
    #to avoid slow perfect approximation of arc length parameterization, force
    #second derivative to be normal to curve (as they are for arc param curves)

    dv2 = self.dv2_intern(s)
    l = dv2.length

    dv1 = self.dv(s)
    dv2 = dv2.cross(dv1)
    dv2 = -dv2.cross(dv1)
    dv2.normalize()

    return dv2 * l

  def dv2_intern(self, s):
    ds = 0.1 * self.length / self.steps 

    if s > ds and s < 1.0 - ds:
      a = self.dv(s-ds)
      b = self.dv(s+ds)
      return (b - a) / (2.0 * ds)
    elif s < ds:
      a = self.dv(s)
      b = self.dv(s+ds)
      return (b - a) / ds
    else:
      a = self.dv(s-ds)
      b = self.dv(s)
      return (b - a) / ds

  def normal(self, s, depth=15):
    dv2 = self.dv2(s)        
    dv2.normalize()

    if dv2.length == 0:
      #try offsetting a bit
      if depth > 0:
        ds = self.length / self.steps * depth
        ds *= -1.0 if depth % 2 == 0 else 1.0

        return self.normal(s+ds, depth-1)

      print("Spline had zero derivative! Using z-axis")
      return Vector([0, 0, 1])

    return dv2
    
  def curvature(self, s):
    return self.dv2(s).length

  def update(self):
    self.regen = False

    steps = self.steps

    ##oversample curve
    steps2 = steps

    dt = 1.0 / (steps2 - 1)
    t = 0
    ks = self.ks
    s = 0
    
    table = [Vector() for x in range(steps)]
    tabledv = [Vector() for x in range(steps)]
    table_t = [0 for x in range(steps)]

    self.table = table
    self.tabledv = tabledv
    self.table_t = table_t

    tots = [0 for x in range(steps)]

    dslist = []

    for i in range(steps2):
      dvx = cubic_eval.dv(ks[0], t)
      dvy = cubic_eval.dv(ks[1], t)
      dvz = cubic_eval.dv(ks[2], t)

      #dvx2 = cubic_eval.dv2(ks[0], t)
      #dvy2 = cubic_eval.dv2(ks[1], t)
      #dvz2 = cubic_eval.dv2(ks[2], t)

      ds = (dvx*dvx + dvy*dvy + dvz*dvz)**0.5
      ds *= dt

      dslist.append(ds)

      s += ds
      t += dt
    
    self.length = s
    length = s

    s = 0
    t = 0
    for i in range(steps):
      j = int(floor(s / length * steps + 0.00001))
      j = min(max(j, 0), steps-1)

      px = cubic_eval.eval(ks[0], t)
      py = cubic_eval.eval(ks[1], t)
      pz = cubic_eval.eval(ks[2], t)

      table_t[j] += t

      table[j][0] += px
      table[j][1] += py
      table[j][2] += pz
      tots[j] += 1.0

      ds = dslist[i]
      s += ds
      t += dt

    for i in range(len(table)):
      if tots[i]:
        table[i] /= tots[i]
        table_t[i] /= tots[i]
    
    if not tots[0]:
      for i in range(len(table)):
        if tots[i]:
          tots[0] = tots[i]
          break
    
    if not tots[0]:
      print("SPLINE ERROR!");
      return

    i = 0
    while i < len(table):
      if not tots[i]:
        prev = i-1
        j = i
        while j < len(table):
          if tots[j]:
            break
          j += 1

        if j == len(table):
          j -= 1
          table[j] = table[prev]
          table_t[j] = table_t[prev]
          tots[j] = 1.0

        if i == j:
          i += 1
          continue

        dt2 = 1.0 / (j - prev)
        a = table[prev]
        b = table[j]
        t2 = 0.0

        sa = table_t[prev]
        sb = table_t[j]
        
        while i < j:
          table[i] = a + (b - a)*t2
          table_t[i] = sa + (sb - sa)*t2

          t2 += dt2
          i += 1
      
        continue
      i += 1

    dlen = self.length / self.steps
    
    for i in range(len(table_t)):
      #if i < len(table_t)-1:
      #  t = table_t[i+1]
      #else:
      t = table_t[i]

      dvx = cubic_eval.dv(ks[0], t)
      dvy = cubic_eval.dv(ks[1], t)
      dvz = cubic_eval.dv(ks[2], t)

      dv = tabledv[i]
      dv[0] = dvx;
      dv[1] = dvy;
      dv[2] = dvz;

      dv.normalize()

      dv[0] *= dlen
      dv[1] *= dlen;
      dv[2] *= dlen

    
class ArchLengthSpline3d:
  def __init__(self, curves=[]):
    self.curves = []
    self.regen = 1
    self.length = 0

    for c in curves:
      self.addCurve(c)

    self.update()

  def render(self, bm, steps=64):
    s = 0
    self.checkUpdate()

    ds = self.length / (steps - 1)
    lastp = None
    lastv = None

    for i in range(steps):
      p = self.eval(s)
      v = bm.verts.new(p)

      if lastp:
        bm.edges.new([lastv, v])
        pass

      n = self.normal(s)
      p2 = p + n*0.2
      bm.edges.new([v, bm.verts.new(p2)])

      lastp = p
      lastv = v
      s += ds

  def addCurve(self, c):
    if type(c) is not ArcLengthBez3d:
      c2 = ArcLengthBez3d()
      c2.setPoint(0, c[0])
      c2.setPoint(1, c[1])
      c2.setPoint(2, c[2])
      c2.setPoint(3, c[3])
      c = c2

    self.curves.append(c)

  def checkUpdate(self):
    if self.regen:
      self.update()

  def getCurve(self, s):
    lastc = None
    for c in self.curves:
      if lastc and c.s >= s:
        lastc.checkUpdate()
        return lastc
      lastc = c
    
    if self.curves[-1]:
      self.curves[-1].checkUpdate()

    return self.curves[-1]
  
  def update(self):
    s = 0

    for c in self.curves:
      c.s = s
      c.update()

      s += c.length
    
    self.length = s
  
  def eval(self, s):
    c = self.getCurve(s)
    return c.eval(s - c.s)

  def dv(self, s):
    c = self.getCurve(s)
    return c.dv(s - c.s)

  def dv2(self, s):
    c = self.getCurve(s)
    return c.dv2(s - c.s)

  def curvature(self, s):
    c = self.getCurve(s)
    return c.curvature(s - c.s)

  def normal(self, s):
    c = self.getCurve(s)
    return c.normal(s - c.s)

  def frenetFrame(self, s):
    c = self.getCurve(s)
    return c.frenetFrame(s - c.s)
