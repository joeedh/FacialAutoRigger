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
  
  