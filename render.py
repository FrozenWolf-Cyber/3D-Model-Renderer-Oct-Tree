

import pygame
import copy
from OpenGL.GL import *
from oct_tree import Octree
import numpy as np



dist_range = 20
dist_sq = dist_range**2
vertices= (
    (1, -1, -1),
    (1, 1, -1),
    (-1, 1, -1),
    (-1, -1, -1),
    (1, -1, 1),
    (1, 1, 1),
    (-1, -1, 1),
    (-1, 1, 1)
    )

def gen_vertices(Xc,Yc,Zc,SL):
    return [[Xc + SL/2, Yc - SL/2, Zc - SL/2],
            [Xc + SL/2, Yc + SL/2, Zc - SL/2],
            [Xc - SL/2, Yc + SL/2, Zc - SL/2],
            [Xc - SL/2, Yc - SL/2, Zc - SL/2],
            [Xc + SL/2, Yc - SL/2, Zc + SL/2],
            [Xc + SL/2, Yc + SL/2, Zc + SL/2],
            [Xc - SL/2, Yc - SL/2, Zc + SL/2],
            [Xc - SL/2, Yc + SL/2, Zc + SL/2]]

colors = (
    (1,0,0),
    (0,1,0),
    (0,0,1),
    (0,1,0),
    (1,1,1),
    (0,1,1),
    (1,0,0),
    (0,1,0),
    (0,0,1),
    (1,0,0),
    (1,1,1),
    (0,1,1),
    )

edges = (
    (0,1),
    (0,3),
    (0,4),
    (2,1),
    (2,3),
    (2,7),
    (6,3),
    (6,4),
    (6,7),
    (5,1),
    (5,4),
    (5,7)
    )

surfaces = (
    (0,1,2,3),
    (3,2,7,6),
    (6,7,5,4),
    (4,5,1,0),
    (1,5,7,2),
    (4,0,3,6)
    )



def Cube(x, y, z, size):
    glBegin(GL_LINES)
    vertices = gen_vertices(x,y,z,size)
    for edge in edges:
        for vertex in edge:
            a = vertices[vertex] 
            glVertex3fv(a)
    glEnd()




def MTL(filename):
    contents = {}
    mtl = None
    for line in open(filename, "r"):
        if line.startswith('#'): continue
        values = line.split()
        # print(values)
        if not values: continue
        if values[0] == 'newmtl':
            mtl = contents[values[1]] = {}
        elif mtl is None:
            raise ValueError("mtl file doesn't start with newmtl stmt")
        elif values[0] == 'map_Kd':
            # load the texture referred to by this declaration
            mtl[values[0]] = values[1]
            surf = pygame.image.load(mtl['map_Kd'])
            image = pygame.image.tostring(surf, 'RGBA', 1)
            ix, iy = surf.get_rect().size
            texid = mtl['texture_Kd'] = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texid)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA,
                GL_UNSIGNED_BYTE, image)
            
        else:
            mtl[values[0]] = map(float, values[1:])

    # print(contents)
    return contents

class OBJ:
    def __init__(self, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = list(map(lambda x: float(x), values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = list(map(lambda x: float(x), values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(list(map(lambda x: float(x), values[1:3])))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                self.mtl = MTL(values[1])
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))

        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        glEnable(GL_TEXTURE_2D)
        glFrontFace(GL_CCW)
        for face in self.faces:
            vertices, normals, texture_coords, material = face
            
            c = list(self.mtl[material]["Kd"])
            if len(c) == 0:
                c = [1,1,1]
            else:
                self.mtl[material]["Kd"] = c
            mtl = self.mtl[material]
            if 'texture_Kd' in mtl:
                # use diffuse texmap
                glBindTexture(GL_TEXTURE_2D, copy.deepcopy(mtl['texture_Kd']))
            else:
                # just use diffuse colour
                glColor(c[0], c[1], c[2])

            glBegin(GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                if texture_coords[i] > 0:
                    glTexCoord2fv(self.texcoords[texture_coords[i] - 1])
                glVertex3fv(self.vertices[vertices[i] - 1])
            glEnd()
        glDisable(GL_TEXTURE_2D)
        glEndList()

class OBJ:
    def __init__(self, filename, swapyz, x, y, z, texture = True):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.unique_vertices = {}
        self.x = x
        self.y = y
        self.z = z
        self.swapyz = swapyz
        self.filename = filename
        self.texture = texture

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if values[0] not in self.unique_vertices:
                self.unique_vertices[values[0]] = 1
                # print(self.unique_vertices)

            else:
                self.unique_vertices[values[0]] += 1
                # print(self.unique_vertices)

            if not values: continue
            if values[0] == 'v':
                # print(values)
                v = list(map(float, values[1:4]))
                # print(v)
                if swapyz:
                    v = v[0], v[2], v[1]
                    
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(list(map(float, values[1:3])))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                self.mtl = MTL(values[1])
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))

        self.gl_list = glGenLists(1)

        self.all_faces = []
        self.all_vertices = []

        for idx, face in enumerate(self.faces):
            for vertex in face[0]:
                self.all_faces.append(idx)
                self.all_vertices.append(self.vertices[vertex-1])

        self.all_faces = np.array(self.all_faces)
        self.all_vertices = np.array(self.all_vertices)
        self.oct_tree = Octree(self.all_vertices, self.all_faces)

        self.render()


    def update(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def render(self):
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        glEnable(GL_TEXTURE_2D)
        glFrontFace(GL_CCW)

        query_point = np.array([self.x, self.y, self.z])
        selected_faces = self.oct_tree.query_radius(query_point, dist_range)
        for i in selected_faces:
            
            face = self.faces[i]
            vertices, normals, texture_coords, material = face

            if self.texture:
                mtl = copy.deepcopy(self.mtl[material])
                if 'texture_Kd' in mtl:
                    # use diffuse texmap
                    glBindTexture(GL_TEXTURE_2D,  copy.deepcopy(mtl['texture_Kd']))
                else:
                    try:
                        glColor(*mtl['Kd'])
                    except:
                        pass


            glBegin(GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                glVertex3fv(self.vertices[vertices[i] - 1])
        
            glEnd()

        glDisable(GL_TEXTURE_2D)
        glEndList()


import sys, pygame
from pygame.locals import *
from pygame.constants import *
from OpenGL.GL import *
from OpenGL.GLU import *

# IMPORT OBJECT LOADER
from objloader import *

pygame.init()
# pygame.display.gl_set_attribute(GL_DEPTH_SIZE, 24)
viewport = (2000,1600)
hx = viewport[0]/2
hy = viewport[1]/2
srf = pygame.display.set_mode(viewport, OPENGL | DOUBLEBUF)

glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
glEnable(GL_LIGHT0)
glEnable(GL_LIGHTING)
glEnable(GL_COLOR_MATERIAL)
glEnable(GL_DEPTH_TEST)
glShadeModel(GL_SMOOTH)           # most obj files expect to be smooth-shaded

# LOAD OBJECT AFTER PYGAME INIT
rx, ry = (722, -798)
tx, ty = (235, -205)
zpos = 66
rotate = move = False

obj_tx, obj_ty, obj_zpos = (0,0,0)
move_by = 2

obj = OBJ('assets.obj', True, obj_tx, obj_ty, obj_zpos, False)

sphere = gluNewQuadric()
clock = pygame.time.Clock()


glMatrixMode(GL_PROJECTION)
glLoadIdentity()
width, height = viewport
gluPerspective(45.0, width/float(height), 1, 100.0)
glEnable(GL_DEPTH_TEST)
glMatrixMode(GL_MODELVIEW)




ispress = None
while 1:
    clock.tick(30)

    translation = False
    for e in pygame.event.get():
        
        if e.type == QUIT:
            sys.exit()
        elif e.type == KEYDOWN and e.key == K_ESCAPE:
            sys.exit()
        elif e.type == MOUSEBUTTONDOWN:
            if e.button == 4: 
                zpos = max(1, zpos-1)
            elif e.button == 5: 
                zpos += 1

            elif e.button == 1: rotate = True
            elif e.button == 3: move = True
        elif e.type == MOUSEBUTTONUP:
            if e.button == 1: rotate = False
            elif e.button == 3: move = False

        elif e.type == MOUSEMOTION:
            i, j = e.rel
            if rotate:
                rx += i
                ry += j
                
            if move:
                tx += i
                ty -= j

        elif e.type == KEYUP:
            ispress = None

        elif (e.type == KEYDOWN) or ispress != None:
            
            if (ispress != None):
                decide = ispress

            else:
                decide = e.key
                
            if (decide == K_UP or decide == K_w):
                translation = True
                obj_ty -= move_by
                ispress = decide

            elif (decide == K_DOWN or decide == K_s):
                translation = True
                obj_ty += move_by
                ispress = decide

            elif (decide == K_LEFT or decide == K_a):
                translation = True
                obj_tx -= move_by
                ispress = decide

            elif (decide == K_RIGHT or decide == K_d):
                translation = True
                obj_tx += move_by
                ispress = decide


        

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glTranslate(tx/20., ty/20., - zpos)
    glRotate(ry, 1, 0, 0)
    glRotate(rx, 0, 1, 0)

    obj.update(obj_tx, obj_ty, obj_zpos)

    if (translation):
        obj.render()


    else:
        glCallList(obj.gl_list)

    Cube(obj_tx, obj_ty, obj_zpos, dist_range)
    Cube(obj_tx, obj_ty, obj_zpos, 1)

    pygame.display.flip()