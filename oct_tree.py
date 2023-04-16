import numpy as np

class OctreeNode:
    def __init__(self, center, size):
        self.center = center
        self.size = size
        self.children = [None] * 8
        self.points = []
        self.face_ids = []
        
class Octree:
    def __init__(self, points, face_ids, max_depth=10, min_points=10):
        self.root = OctreeNode(np.mean(points, axis=0), np.max(points, axis=0) - np.min(points, axis=0))
        self.max_depth = max_depth
        self.min_points = min_points
        for i, point in enumerate(points):
            self.insert(point, face_ids[i], self.root)
    
    def insert(self, point, face_id, node):
        if len(node.points) < self.min_points or node.children[0] is None or node.size / 2 < np.linalg.norm(point - node.center):
            node.points.append(point)
            node.face_ids.append(face_id)
        else:
            octant = self.get_octant(point, node.center)
            if node.children[octant] is None:
                child_center = node.center + (np.array([octant & 4, octant & 2, octant & 1]) - 0.5) * node.size / 4
                node.children[octant] = OctreeNode(child_center, node.size / 2)
            self.insert(point, face_id, node.children[octant])
    
    def get_octant(self, point, center):
        octant = 0
        if point[0] > center[0]: octant |= 4
        if point[1] > center[1]: octant |= 2
        if point[2] > center[2]: octant |= 1
        return octant
    
    def query_radius(self, query_point, radius):
        results = set()
        self._query_radius(query_point, radius, self.root, results)
        return results
    
    def _query_radius(self, query_point, radius, node, results):
        if node is None: return
        if len(node.points) > 0:
            distances = np.linalg.norm(np.array(node.points) - query_point, axis=1)
            for i, distance in enumerate(distances):
                if distance < radius:
                    results.add(node.face_ids[i])
                    
        if node.children[0] is not None:
            octant_distances = np.abs(np.array(node.children_centers) - query_point)
            closest_octant = np.argmin(octant_distances.sum(axis=1))
            if octant_distances[closest_octant].sum() - node.children[closest_octant].size / 2 < radius:
                self._query_radius(query_point, radius, node.children[closest_octant], results)
            for i in range(8):
                if i != closest_octant and octant_distances[i].sum() + node.children[i].size / 2 >= radius:
                    self._query_radius(query_point, radius, node.children[i], results)


points = np.random.rand(10000, 3)
face_ids = np.random.randint(0, 100, 10000)
print(points.shape, face_ids.shape)
octree = Octree(points, face_ids)
query_point = np.array([0.5, 0.5, 0.5])
radius = 0.1
results = octree.query_radius(query_point, radius)
print(results)