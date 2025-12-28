
import math

class MockVector2:
    def __init__(self, x=0, y=0):
        if hasattr(x, '__iter__') and not isinstance(x, (str, bytes)):
            vals = list(x)
            self.x = float(vals[0])
            self.y = float(vals[1])
        elif hasattr(x, 'x') and hasattr(x, 'y'):
            self.x = float(x.x)
            self.y = float(x.y)
        else:
            self.x = float(x)
            self.y = float(y)
            
    def __iter__(self):
        yield self.x
        yield self.y
        
    def __getitem__(self, index):
        return [self.x, self.y][index]
    
    def __len__(self):
        return 2

    def __add__(self, other):
        if hasattr(other, 'x'):
            return MockVector2(self.x + other.x, self.y + other.y)
        return MockVector2(self.x + other[0], self.y + other[1])
    
    def __sub__(self, other):
        if hasattr(other, 'x'):
            return MockVector2(self.x - other.x, self.y - other.y)
        return MockVector2(self.x - other[0], self.y - other[1])
    
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return MockVector2(self.x * other, self.y * other)
        if hasattr(other, 'x'):
            return MockVector2(self.x * other.x, self.y * other.y)
        return MockVector2(self.x * other[0], self.y * other[1])

    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __repr__(self):
        return f"MockVector2({self.x}, {self.y})"

class MockVector3:
    def __init__(self, x=0, y=0, z=0):
        # Handle initialization from another MockVector3 or iterable
        if hasattr(x, '__iter__') and not isinstance(x, (str, bytes)):
            vals = list(x)
            self.x = float(vals[0])
            self.y = float(vals[1])
            self.z = float(vals[2])
        elif hasattr(x, 'x') and hasattr(x, 'y') and hasattr(x, 'z'):
            self.x = float(x.x)
            self.y = float(x.y)
            self.z = float(x.z)
        else:
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)
    
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
        
    def __getitem__(self, index):
        return [self.x, self.y, self.z][index]
    
    def __len__(self):
        return 3

    def __add__(self, other):
        if hasattr(other, 'x'):
            return MockVector3(self.x + other.x, self.y + other.y, self.z + other.z)
        return MockVector3(self.x + other[0], self.y + other[1], self.z + other[2])
    
    def __sub__(self, other):
        if hasattr(other, 'x'):
            return MockVector3(self.x - other.x, self.y - other.y, self.z - other.z)
        return MockVector3(self.x - other[0], self.y - other[1], self.z - other[2])
    
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return MockVector3(self.x * other, self.y * other, self.z * other)
        if hasattr(other, 'x'):
            return MockVector3(self.x * other.x, self.y * other.y, self.z * other.z)
        return MockVector3(self.x * other[0], self.y * other[1], self.z * other[2])

    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return MockVector3(self.x / other, self.y / other, self.z / other)
        return NotImplemented
    
    def length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self):
        l = self.length()
        if l > 0:
            self.x /= l
            self.y /= l
            self.z /= l
        return True
    
    def __repr__(self):
        return f"MockVector3({self.x}, {self.y}, {self.z})"

class MockCollisionHandlerQueue:
    def __init__(self):
        self.entries = []
    
    def getNumEntries(self):
        return len(self.entries)
    
    def sortEntries(self):
        self.entries.sort(key=lambda x: x.get_dist() if hasattr(x, 'get_dist') else 0)
        
    def getEntry(self, i):
        return self.entries[i]

class MockCollisionTraverser:
    def __init__(self, *args, **kwargs):
        pass
    def addCollider(self, node, handler):
        pass
    def removeCollider(self, node):
        pass
    def traverse(self, node):
        pass

class MockNodePath:
    def __init__(self, name="node"):
        self.name = name
        self.pos = MockVector3(0, 0, 0)
        self.hpr = MockVector3(0, 0, 0)
        self.scale = MockVector3(1, 1, 1)
        self.children = []
        self.parent = None

    def getName(self):
        return self.name

    def attachNewNode(self, name):
        node = MockNodePath(name)
        node.parent = self
        self.children.append(node)
        return node
    
    def setPos(self, *args):
        if len(args) == 1:
            self.pos = MockVector3(args[0])
        else:
            self.pos = MockVector3(*args)
    
    def getPos(self, other=None):
        return self.pos
        
    def setZ(self, z): self.pos.z = float(z)
    def setX(self, x): self.pos.x = float(x)
    def setY(self, y): self.pos.y = float(y)
    
    def setHpr(self, *args):
        if len(args) == 1:
            self.hpr = MockVector3(args[0])
        else:
            self.hpr = MockVector3(*args)
    
    def getHpr(self): return self.hpr
    def getH(self): return self.hpr.x
    def getP(self): return self.hpr.y
    def getR(self): return self.hpr.z
    def setH(self, h): self.hpr.x = float(h)
    def setP(self, p): self.hpr.y = float(p)
    def setR(self, r): self.hpr.z = float(r)
    
    def setScale(self, *args):
        if len(args) == 1:
            self.scale = MockVector3(args[0])
        else:
            self.scale = MockVector3(*args)
            
    def getScale(self): return self.scale
    
    def setColorScale(self, *args):
        pass
        
    def setQuat(self, quat):
        pass

    def removeNode(self):
        if self.parent:
            self.parent.children.remove(self)
    
    def getNumChildren(self):
        return len(self.children)
    
    def getChild(self, index):
        return self.children[index] if 0 <= index < len(self.children) else None
    
    def getParent(self):
        return self.parent
        
    def lookAt(self, *args):
        pass
        
    def reparentTo(self, other):
        if self.parent:
            self.parent.children.remove(self)
        self.parent = other
        other.children.append(self)
    
    def isHidden(self):
        return getattr(self, '_hidden', False)
    
    def hide(self):
        self._hidden = True
    
    def show(self):
        self._hidden = False
