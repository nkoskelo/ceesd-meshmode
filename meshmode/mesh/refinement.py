from __future__ import division

__copyright__ = "Copyright (C) 2014 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import numpy as np

class TreeRayNode:
    """Describes a ray as a tree, this class represents each node in this tree
    .. attribute:: left
        Left child.
        *None* if ray segment hasn't been split yet.
    .. attribute:: right
        Right child.
        *None* if ray segment hasn't been split yet.
    .. attribute:: midpoint
        Vertex index of midpoint of this ray segment.
        *None* if no midpoint has been assigned yet.
    .. attribute:: direction
        A :class:`bool` denoting direction in the ray,
        with *True* representing "positive" and *False*
        representing "negative".
    .. attribute:: adjacent_elements
        List containing elements indices of elements adjacent
        to this ray segment.
    """
    def __init__(self, left_vertex, right_vertex, direction = True, adjacent_elements = []):
        import copy
        self.left = None
        self.right = None
        self.left_vertex = left_vertex
        self.right_vertex = right_vertex
        self.midpoint = None
        self.direction = direction
        self.adjacent_elements = copy.deepcopy(adjacent_elements)

class Refiner(object):
    def __init__(self, mesh):
        print 'herlkjjlkjasdf'
        from llist import dllist, dllistnode
        from meshmode.mesh.tesselate  import tesselatetet
        self.simplex_node_tuples, self.simplex_result = tesselatetet()
        self.last_mesh = mesh
        
        # {{{ initialization

        # mapping: (vertex_1, vertex_2) -> TreeRayNode 
        # where vertex_i represents a vertex number
        #
        # Assumption: vertex_1 < vertex_2
        self.pair_map = {}

        nvertices = len(mesh.vertices[0])
        
        #array containing element whose edge lies on corresponding vertex
        self.hanging_vertex_element = []
        import six
        for i in six.moves.range(nvertices):
            self.hanging_vertex_element.append([])

        import six
        for grp in mesh.groups:
            iel_base = grp.element_nr_base
            for iel_grp in six.moves.range(grp.nelements):
                vert_indices = grp.vertex_indices[iel_grp]
                for i in six.moves.range(len(vert_indices)):
                    for j in six.moves.range(i+1, len(vert_indices)):
                       
                        #minimum and maximum of the two indices for storing 
                        #data in vertex_pair
                        min_index = min(vert_indices[i], vert_indices[j])
                        max_index = max(vert_indices[i], vert_indices[j])

                        vertex_pair = (min_index, max_index)
                        print vertex_pair
                        if vertex_pair in self.pair_map:
                            print 'BEFORE:', self.pair_map[vertex_pair].adjacent_elements
                        if vertex_pair not in self.pair_map:
                            self.pair_map[vertex_pair] = TreeRayNode(min_index, max_index)
                            self.pair_map[vertex_pair].adjacent_elements.append(iel_base+iel_grp)
                        elif (iel_base+iel_grp) not in self.pair_map[vertex_pair].adjacent_elements:
                            (self.pair_map[vertex_pair].
                                adjacent_elements.append(iel_base+iel_grp))
                        print "HERLEJALKFJASLKFJASFLKJASF:", self.pair_map[vertex_pair].adjacent_elements
        # }}}

        #generate reference tuples
        self.index_to_node_tuple = [()] * (len(vert_indices))
        for i in six.moves.range(0, len(vert_indices)-1):
            self.index_to_node_tuple[0] = self.index_to_node_tuple[0] + (0,)
        for i in six.moves.range(1, len(vert_indices)):
            for j in six.moves.range(1, len(vert_indices)):
                if i == j:
                    self.index_to_node_tuple[i] = self.index_to_node_tuple[i] + (2,)
                else:
                    self.index_to_node_tuple[i] = self.index_to_node_tuple[i] + (0,)
        self.index_to_midpoint_tuple = [()] * (int((len(vert_indices) * (len(vert_indices) - 1)) / 2))
        curind = 0
        for ind1 in six.moves.range(0, len(self.index_to_node_tuple)):
            for ind2 in six.moves.range(ind1+1, len(self.index_to_node_tuple)):
                i = self.index_to_node_tuple[ind1]
                j = self.index_to_node_tuple[ind2]
                for k in six.moves.range(0, len(vert_indices)-1):
                    cur = int((i[k] + j[k]) / 2)
                    self.index_to_midpoint_tuple[curind] = self.index_to_midpoint_tuple[curind] + (cur,)
                curind += 1
        print "LKJAFLKJASFLJASF"
        print self.index_to_node_tuple
        print self.index_to_midpoint_tuple
        #print mesh.groups[0].vertex_indices
        '''
        self.ray_vertices = np.empty([len(mesh.groups[0].vertex_indices) * 
            len(mesh.groups[0].vertex_indices[0]) * (len(mesh.groups[0].vertex_indices[0]) - 1) / 2, 2], 
                dtype=np.int32)
        self.ray_elements = np.zeros([len(mesh.groups[0].vertex_indices) * 
            len(mesh.groups[0].vertex_indices[0]) * (len(mesh.groups[0].vertex_indices[0]) - 1)
             / 2, 1, 2], dtype=np.int32)
        self.vertex_to_ray = []
        for i in mesh.vertices[0]:
            self.vertex_to_ray.append([]);
        count = 0
        for grp in mesh.groups:
            for i in range(0, len(grp.vertex_indices)):
                for j in range(0, len(grp.vertex_indices[i])):
                    for k in range(j + 1, len(grp.vertex_indices[i])):
                        self.ray_vertices[count][0] = grp.vertex_indices[i][j]
                        self.ray_vertices[count][1] = grp.vertex_indices[i][k]
                        temp1 = VertexRay(count, 0)
                        self.vertex_to_ray[grp.vertex_indices[i][j]].append(temp1)
                        temp2 = VertexRay(count, 1)
                        self.vertex_to_ray[grp.vertex_indices[i][k]].append(temp2)
                        count += 1
        ind = 0
        #print self.ray_vertices
        for i in self.ray_vertices:
            which = 0
            for grp in mesh.groups:
                for j in range(0, len(grp.vertex_indices)):
                    count = 0
                    for k in grp.vertex_indices[j]:
                        if k == i[0] or k == i[1]:
                            count += 1
                    #found an element sharing edge
                    if count == 2:
                        self.ray_elements[ind][0][which] = j
                        which += 1
                        if which == 2:
                            break
            ind += 1
        '''

    def get_refine_base_index(self):
        if self.last_split_elements is None:
            return 0
        else:
            return self.last_mesh.nelements - len(self.last_split_elements)

    def get_empty_refine_flags(self):
        return np.zeros(
                self.last_mesh.nelements - self.get_refine_base_index(),
                np.bool)

    def get_current_mesh(self):
        
        from meshmode.mesh import Mesh
        #return Mesh(vertices, [grp], element_connectivity=self.generate_connectivity(len(self.last_mesh.groups[group].vertex_indices) \
        #            + count*3))
        groups = [] 
        grpn = 0
        for grp in self.last_mesh.groups:
            groups.append(np.empty([len(grp.vertex_indices),
                len(self.last_mesh.groups[grpn].vertex_indices[0])], dtype=np.int32))
            for iel_grp in xrange(grp.nelements):
                for i in range(0, len(grp.vertex_indices[iel_grp])):
                    groups[grpn][iel_grp][i] = grp.vertex_indices[iel_grp][i]
            grpn += 1
        grp = []

        from meshmode.mesh.generation import make_group_from_vertices
        for grpn in range(0, len(groups)):
            grp.append(make_group_from_vertices(self.last_mesh.vertices, groups[grpn], 4))
        self.last_mesh = Mesh(self.last_mesh.vertices, grp,\
                element_connectivity=self.generate_connectivity(len(self.last_mesh.groups[0].vertex_indices),\
                    len(self.last_mesh.vertices[0])))
        
        return self.last_mesh
    
    def update_connectivity(self, element_rays, to_replace, replace_to):
        import six
        for node in element_rays:
            if node.adjacent_elements.count(to_replace):
                node.adjacent_elements.remove(to_replace)
            if not node.adjacent_elements.count(to_replace):
                node.adjacent_elements.append(replace_to)

        next_element_rays = []
        for i in six.moves.range(len(element_rays)):
            for j in six.moves.range(i+1, len(element_rays)):
                if element_rays[i].midpoint is not None and element_rays[j].midpoint is not None:
                    min_midpoint = min(element_rays[i].midpoint, element_rays[j].midpoint)
                    max_midpoint = max(element_rays[i].midpoint, element_rays[j].midpoint)
                    vertex_pair = (min_midpoint, max_midpoint)
                    if vertex_pair in self.pair_map:
                        next_element_rays.append(self.pair_map[vertex_pair])
                    else:
                        return
                else:
                    return
        update_connectivity(next_element_rays, to_replace, replace_to)


    #refine_flag tells you which elements to split as a numpy array of bools
    def refine(self, refine_flags):
        import six
        import numpy as np
        from sets import Set
        #vertices and groups for next generation
        nvertices = len(self.last_mesh.vertices[0])

        groups = []

        midpoint_already = Set([])
        grpn = 0
        totalnelements = 0


        for grp in self.last_mesh.groups:
            iel_base = grp.element_nr_base
            nelements = 0
            for iel_grp in six.moves.range(grp.nelements):
                nelements += 1
                vertex_indices = grp.vertex_indices[iel_grp]
                if refine_flags[iel_base+iel_grp]:
                    nelements += len(self.simplex_result) - 1
                    for i in six.moves.range(len(vertex_indices)):
                        for j in six.moves.range(i+1, len(vertex_indices)):
                            i_index = vertex_indices[i]
                            j_index = vertex_indices[j]
                            index_tuple = (i_index, j_index) if i_index < j_index else (j_index, i_index)
                            if index_tuple not in midpoint_already and \
                                self.pair_map[index_tuple].midpoint is None:
                                    nvertices += 1
                                    midpoint_already.add(index_tuple)
            groups.append(np.empty([nelements, len(grp.vertex_indices[0])], dtype=np.int32))
            grpn += 1
            totalnelements += nelements

        vertices = np.empty([len(self.last_mesh.vertices), nvertices])

        new_hanging_vertex_element = []
        for i in six.moves.range(nvertices):
            new_hanging_vertex_element.append([])

        for i in six.moves.range(len(self.last_mesh.vertices)):
            for j in six.moves.range(len(self.last_mesh.vertices[i])):
                vertices[i,j] = self.last_mesh.vertices[i,j]
                import copy
                if i == 0:
                    new_hanging_vertex_element[j] = copy.deepcopy(self.hanging_vertex_element[j])
        grpn = 0
        for grp in self.last_mesh.groups:
            for iel_grp in six.moves.range(grp.nelements):
                for i in six.moves.range(len(grp.vertex_indices[iel_grp])):
                    groups[grpn][iel_grp][i] = grp.vertex_indices[iel_grp][i]
            grpn += 1

        grpn = 0
        vertices_index = len(self.last_mesh.vertices[0])
        nelements_in_grp = grp.nelements
        for grp in self.last_mesh.groups:
            iel_base = grp.element_nr_base
            for iel_grp in six.moves.range(grp.nelements):
                if refine_flags[iel_base+iel_grp]:
                    midpoint_vertices = []
                    midpoint_tuples = []
                    vertex_elements = []
                    vertex_indices = grp.vertex_indices[iel_grp]
                    for i in six.moves.range(len(vertex_indices)):
                        for j in six.moves.range(i+1, len(vertex_indices)):
                            vertex_elements.append([])
                            min_index = min(vertex_indices[i], vertex_indices[j])
                            max_index = max(vertex_indices[i], vertex_indices[j])
                            cur_node = self.pair_map[(min_index, max_index)]
                            if cur_node.midpoint is None:
                                cur_node.midpoint = vertices_index
                                import copy
                                cur_node.left = TreeRayNode(min_index, vertices_index,
                                        cur_node.direction, copy.deepcopy(cur_node.adjacent_elements))
                                cur_node.right = TreeRayNode(max_index, vertices_index,
                                        not cur_node.direction,
                                        copy.deepcopy(cur_node.adjacent_elements))
                                vertex_pair1 = (min_index, vertices_index)
                                vertex_pair2 = (max_index, vertices_index)
                                self.pair_map[vertex_pair1] = cur_node.left
                                self.pair_map[vertex_pair2] = cur_node.right
                                for el in cur_node.adjacent_elements:
                                    if el != (iel_base+iel_grp):
                                        vertex_elements[len(vertex_elements)-1].append(el)
                                        new_hanging_vertex_element[vertices_index].append(el)
                                #compute midpoint coordinates
                                for k in six.moves.range(len(self.last_mesh.vertices)):
                                    vertices[k, vertices_index] = \
                                    (self.last_mesh.vertices[k, vertex_indices[i]] +
                                    self.last_mesh.vertices[k, vertex_indices[j]]) / 2.0
                                midpoint_vertices.append(vertices_index)
                                vertices_index += 1
                            else:
                                cur_midpoint = cur_node.midpoint
                                elements = cur_node.left.adjacent_elements
                                for el in elements:
                                    if el != (iel_base + iel_grp) and el not in (
                                        vertex_elements[len(vertex_elements)-1]):
                                        vertex_elements[len(vertex_elements)-1].append(el)
                                elements = cur_node.right.adjacent_elements
                                for el in elements:
                                    if el != (iel_base+iel_grp) and el not in (
                                        vertex_elements[len(vertex_elements)-1]):
                                        vertex_elements[len(vertex_elements)-1].append(el)
                                for el in new_hanging_vertex_element[cur_midpoint]:
                                    if el != (iel_base + iel_grp) and el not in (
                                        vertex_elements[len(vertex_elements)-1]):
                                        vertex_elements[len(vertex_elements)-1].append(el)
                                midpoint_vertices.append(cur_midpoint)

                    #fix connectivity for elements
                    unique_vertex_pairs = [
                        (i, j) for i in range(len(vertex_indices)) for j in range(
                            i+1, len(vertex_indices))]
                    midpoint_index = 0
                    for i, j in unique_vertex_pairs:
                        min_index = min(vertex_indices[i], vertex_indices[j])
                        max_index = max(vertex_indices[i], vertex_indices[j])
                        element_indices_1 = []
                        element_indices_2 = []
                        for k_index, k, in enumerate(self.simplex_result):
                            ituple_index = self.simplex_node_tuples.index(
                                self.index_to_node_tuple[i])
                            jtuple_index = self.simplex_node_tuples.index(
                                self.index_to_node_tuple[j])
                            midpoint_tuple_index = self.simplex_node_tuples.index(
                                self.index_to_midpoint_tuple[midpoint_index])
                            if ituple_index in k and midpoint_tuple_index in k:
                                element_indices_1.append(k_index)
                            if jtuple_index in k and midpoint_tuple_index in k:
                                element_indices_2.append(k_index)
                        midpoint_index += 1
                        if min_index == vertex_indices[i]:
                            min_element_index = element_indices_1
                            max_element_index = element_indices_2
                        else:
                            min_element_index = element_indices_2
                            max_element_index = element_indices_1
                        vertex_pair = (min_index, max_index)
                        cur_node = self.pair_map[vertex_pair]
                        if cur_node.direction:
                            first_element_index = min_element_index
                            second_element_index = max_element_index
                        else:
                            first_element_index = max_element_index
                            second_element_index = min_element_index
                        queue = [cur_node.left]
                        while queue:
                            vertex = queue.pop(0)
                            #if leaf node
                            if vertex.left is None and vertex.right is None:
                                node_elements = vertex.adjacent_elements
                                print 'NODE ELEMENTS:', node_elements
                                print 'ELEMENT_NUMBER:', iel_base+iel_grp
                                node_elements.remove(iel_base+iel_grp)
                                for k in first_element_index:
                                    if k == 0:
                                        node_elements.append(iel_base+iel_grp)
                                    else:
                                        node_elements.append(iel_base+grp.nelements+k-1)
                                if new_hanging_vertex_element[vertex.left_vertex] and \
                                    new_hanging_vertex_element[vertex.left_vertex].count(
                                    iel_base+iel_grp):
                                    new_hanging_vertex_element[vertex.left_vertex].remove(
                                        iel_base+iel_grp)
                                    for k in first_element_index:
                                        if k == 0:
                                            new_hanging_vertex_element[vertex.left_vertex].append(
                                                iel_base+iel_grp)
                                        else:
                                            new_hanging_vertex_element[vertex.left_vertex].append(
                                                iel_base+grp.nelements+k-1)
                                if new_hanging_vertex_element[vertex.right_vertex] and \
                                    new_hanging_vertex_element[vertex.right_vertex].count(
                                    iel_base+iel_grp):
                                    new_hanging_vertex_element[vertex.right_vertex].remove(
                                        iel_base+iel_grp)
                                    for k in first_element_index:
                                        if k == 0:
                                            new_hanging_vertex_element[vertex.right_vertex].append(
                                                iel_base+iel_grp)
                                        else:
                                            new_hanging_vertex_element[vertex.right_vertex].append(
                                                iel_base+grp.nelements+k-1)
                            else:
                                queue.append(vertex.left)
                                queue.append(vertex.right)

                        queue = [cur_node.right]
                        while queue:
                            vertex = queue.pop(0)
                            #if leaf node
                            if vertex.left is None and vertex.right is None:
                                node_elements = vertex.adjacent_elements
                                node_elements.remove(iel_base+iel_grp)
                                for k in second_element_index:
                                    if k == 0:
                                        node_elements.append(iel_base+iel_grp)
                                    else:
                                        node_elements.append(iel_base+grp.nelements+k-1)
                                if new_hanging_vertex_element[vertex.left_vertex] and \
                                    new_hanging_vertex_element[vertex.left_vertex].count(
                                    iel_base+iel_grp):
                                    new_hanging_vertex_element[vertex.left_vertex].remove(
                                        iel_base+iel_grp)
                                    for k in second_element_index:
                                        if k == 0:
                                            new_hanging_vertex_element[vertex.left_vertex].append(
                                                iel_base+iel_grp)
                                        else:
                                            new_hanging_vertex_element[vertex.left_vertex].append(
                                                iel_base+grp.nelements+k-1)
                                if new_hanging_vertex_element[vertex.right_vertex] and \
                                    new_hanging_vertex_element[vertex.right_vertex].count(
                                    iel_base+iel_grp):
                                    new_hanging_vertex_element[vertex.right_vertex].remove(
                                        iel_base+iel_grp)
                                    for k in second_element_index:
                                        if k == 0:
                                            new_hanging_vertex_element[vertex.right_vertex].append(
                                                iel_base+iel_grp)
                                        else:
                                            new_hanging_vertex_element[vertex.right_vertex].append(
                                                iel_base+grp.nelements+k-1)
                            else:
                                queue.append(vertex.left)
                                queue.append(vertex.right)

                    #update connectivity of edges in the center
                    unique_vertex_pairs = [
                        (i,j) for i in range(len(midpoint_vertices)) for j in range(i+1,
                            len(midpoint_vertices))]
                    midpoint_index = 0
                    for i, j in unique_vertex_pairs:
                        min_index = min(midpoint_vertices[i], midpoint_vertices[j])
                        max_index = max(midpoint_vertices[i], midpoint_vertices[j])
                        vertex_pair = (min_index, max_index)
                        if vertex_pair not in self.pair_map:
                            continue
                        element_indices = []
                        for k_index, k in enumerate(self.simplex_result):
                            ituple_index = self.simplex_node_tuples.index(
                                self.index_to_midpoint_tuple[i])
                            jtuple_index = self.simplex_node_tuples.index(
                                self.index_to_midpoint_tuple[j])
                            if ituple_index in k and jtuple_index in k:
                                element_indices.append(k_index)

                        cur_node = self.pair_map[vertex_pair]
                        queue = [cur_node]
                        while queue:
                            vertex = queue.pop(0)
                            #if leaf node
                            if vertex.left is None and vertex.right is None:
                                node_elements = vertex.adjacent_elements
                                node_elements.remove(iel_base+iel_grp)
                                for k in element_indices:
                                    if k == 0:
                                        node_elements.append(iel_base+iel_grp)
                                    else:
                                        node_elements.append(iel_base+grp.nelements+k-1)
                                if new_hanging_vertex_element[vertex.left_vertex] and \
                                    new_hanging_vertex_element[vertex.left_vertex].count(
                                    iel_base+iel_grp):
                                    new_hanging_vertex_element[vertex.left_vertex].remove(
                                        iel_base+iel_grp)
                                    for k in element_indices:
                                        if k == 0:
                                            new_hanging_vertex_element[vertex.left_vertex].append(
                                                iel_base+iel_grp)
                                        else:
                                            new_hanging_vertex_element[vertex.left_vertex].append(
                                                iel_base+grp.nelements+k-1)
                                if new_hanging_vertex_element[vertex.right_vertex] and \
                                    new_hanging_vertex_element[vertex.right_vertex].count(
                                    iel_base+iel_grp):
                                    new_hanging_vertex_element[vertex.right_vertex].remove(
                                        iel_base+iel_grp)
                                    for k in second_element_index:
                                        if k == 0:
                                            new_hanging_vertex_element[vertex.right_vertex].append(
                                                iel_base+iel_grp)
                                        else:
                                            new_hanging_vertex_element[vertex.right_vertex].append(
                                                iel_base+grp.nelements+k-1)
                            else:
                                queue.append(vertex.left)
                                queue.append(vertex.right)
                    #generate new rays
                    for i in six.moves.range(len(midpoint_vertices)):
                        for j in six.moves.range(i+1, len(midpoint_vertices)):
                            min_index = min(midpoint_vertices[i], midpoint_vertices[j])
                            max_index = max(midpoint_vertices[i], midpoint_vertices[j])
                            vertex_pair = (min_index, max_index)
                            if vertex_pair in self.pair_map:
                                continue
                            elements = []
                            common_elements = list(set(new_hanging_vertex_element[min_index]).
                                intersection(new_hanging_vertex_element[max_index]))
                            for cel in common_elements:
                                elements.append(cel)
                            vertex_1_index = self.simplex_node_tuples.index(
                                self.index_to_midpoint_tuple[i])
                            vertex_2_index = self.simplex_node_tuples.index(
                                self.index_to_midpoint_tuple[j])
                            for kind, k in enumerate(self.simplex_result):
                                if vertex_1_index in k and vertex_2_index in k:
                                    if kind == 0:
                                        elements.append(iel_base+iel_grp)
                                    else:
                                        elements.append(iel_base+nelements_in_grp+kind-1)
                            self.pair_map[vertex_pair] = TreeRayNode(min_index, max_index)
                    node_tuple_to_coord = {}
                    for node_index, node_tuple in enumerate(self.index_to_node_tuple):
                        node_tuple_to_coord[node_tuple] = grp.vertex_indices[iel_grp][node_index]
                    for midpoint_index, midpoint_tuple in enumerate(self.index_to_midpoint_tuple):
                        node_tuple_to_coord[midpoint_tuple] = midpoint_vertices[midpoint_index]
                    print grp.vertex_indices[iel_grp] 
                    for i in six.moves.range(len(self.simplex_result)):
                        for j in six.moves.range(len(self.simplex_result[i])):
                            if i == 0:
                                groups[grpn][iel_grp][j] = \
                                        node_tuple_to_coord[self.simplex_node_tuples[self.simplex_result[i][j]]]
                            else:
                                groups[grpn][nelements_in_grp+i-1][j] = \
                                        node_tuple_to_coord[self.simplex_node_tuples[self.simplex_result[i][j]]]
                    
                    #update tet connectivity
                    if len(grp.vertex_indices[0]) == 4:
                        for tup_index, tup in enumerate(self.simplex_result):
                            three_vertex_tuples = [
                                    (i, j, k) for i in range(len(tup)) for j in range(i+1, len(tup))
                                    for k in range(j+1, len(tup))]
                            for i, j, k in three_vertex_tuples:
                                vertex_i = node_tuple_to_coord[self.simplex_node_tuples[tup[i]]]
                                vertex_j = node_tuple_to_coord[self.simplex_node_tuples[tup[j]]]
                                vertex_k = node_tuple_to_coord[self.simplex_node_tuples[tup[k]]]
                                element_rays = []
                                element_rays.append(self.pair_map[(
                                    min(vertex_i, vertex_j), max(vertex_i, vertex_j))])
                                element_rays.append(self.pair_map[(
                                    min(vertex_i, vertex_k), max(vertex_i, vertex_k))])
                                element_rays.append(self.pair_map[(
                                    min(vertex_j, vertex_k), max(vertex_j, vertex_k))])
                                self.update_connectivity(element_rays, iel_base+iel_grp,
                                        nelements_in_grp+tup_index-1)

                    nelements_in_grp += len(self.simplex_result)-1



                    print node_tuple_to_coord
        self.hanging_vertex_element = new_hanging_vertex_element
        from meshmode.mesh.generation import make_group_from_vertices

        grp = []
        for grpn in range(0, len(groups)):
            grp.append(make_group_from_vertices(vertices, groups[grpn], 4))

        from meshmode.mesh import Mesh

        self.last_mesh = Mesh(vertices, grp, element_connectivity=self.generate_connectivity(
            totalnelements, nvertices, groups))
        return self.last_mesh

    def print_rays(self, ind):
        import six
        for i in six.moves.range(len(self.last_mesh.groups[0].vertex_indices[ind])):
            for j in six.moves.range(i+1, len(self.last_mesh.groups[0].vertex_indices[ind])):
                mn = min(self.last_mesh.groups[0].vertex_indices[ind][i], self.last_mesh.groups[0].vertex_indices[ind][j])
                mx = max(self.last_mesh.groups[0].vertex_indices[ind][j], self.last_mesh.groups[0].vertex_indices[ind][i])
                d = self.pair_map[(mn, mx)].d
                ray = self.pair_map[(mn, mx)].ray
                if d:
                    print "FROM:", mn, "TO:", mx, self.vertex_to_ray[mn][ray]
                else:
                    print "FROM:", mn, "TO:", mx, self.vertex_to_ray[mx][ray]

    def print_hanging_elements(self, ind):
        import six
        for i in self.last_mesh.groups[0].vertex_indices[ind]:
            print "IND:", i, self.hanging_vertex_element[i]

    def generate_connectivity(self, nelements, nvertices, groups):
        # medium-term FIXME: make this an incremental update
        # rather than build-from-scratch
        import six
        vertex_to_element = [[] for i in xrange(nvertices)]
        element_index = 0
        for grp in groups:
            for iel_grp in xrange(len(grp)):
                for ivertex in grp[iel_grp]:
                    vertex_to_element[ivertex].append(element_index)
                element_index += 1
        element_to_element = [set() for i in xrange(nelements)]
        element_index = 0
        for grp in groups:
            for iel_grp in xrange(len(grp)):
                for ivertex in grp[iel_grp]:
                    element_to_element[element_index].update(
                            vertex_to_element[ivertex])
                    if self.hanging_vertex_element[ivertex]:
                        for hanging_element in self.hanging_vertex_element[ivertex]:
                            if element_index != hanging_element:
                                element_to_element[element_index].update([hanging_element])
                                element_to_element[hanging_element].update([element_index])
                for i in six.moves.range(len(grp[iel_grp])):
                    for j in six.moves.range(i+1, len(grp[iel_grp])):
                        vertex_pair = (min(grp[iel_grp][i], grp[iel_grp][j]),
                                max(grp[iel_grp][i], grp[iel_grp][j]))
                        element_to_element[element_index].update(
                                self.pair_map[vertex_pair].adjacent_elements)
                    '''
                    if self.hanging_vertex_element[ivertex] and element_index != self.hanging_vertex_element[ivertex][0]:
                        element_to_element[element_index].update([self.hanging_vertex_element[ivertex][0]])
                        element_to_element[self.hanging_vertex_element[ivertex][0]].update([element_index])
                        '''
                element_index += 1
        for iel, neighbors in enumerate(element_to_element):
            neighbors.remove(iel)
        #print self.ray_elements
        '''
        for ray in self.rays:
            curnode = ray.first
            while curnode is not None:
                if len(curnode.value.elements) >= 2:
                    if curnode.value.elements[0] is not None:
                        element_to_element[curnode.value.elements[0]].update(curnode.value.elements)
                    if curnode.value.elements[1] is not None:
                        element_to_element[curnode.value.elements[1]].update(curnode.value.elements)
                if len(curnode.value.velements) >= 2:
                    if curnode.value.velements[0] is not None:
                        element_to_element[curnode.value.velements[0]].update(curnode.value.velements)
                    if curnode.value.velements[1] is not None:
                        element_to_element[curnode.value.velements[1]].update(curnode.value.velements)
                curnode = curnode.next
        '''
        '''
        for i in self.ray_elements:
            for j in i:
                #print j[0], j[1]
                element_to_element[j[0]].update(j)
                element_to_element[j[1]].update(j)
        '''
        #print element_to_element
        lengths = [len(el_list) for el_list in element_to_element]
        neighbors_starts = np.cumsum(
                np.array([0] + lengths, dtype=self.last_mesh.element_id_dtype))
        from pytools import flatten
        neighbors = np.array(
                list(flatten(element_to_element)),
                dtype=self.last_mesh.element_id_dtype)

        assert neighbors_starts[-1] == len(neighbors)
        result = []
        result.append(neighbors_starts)
        result.append(neighbors)
        return result







# vim: foldmethod=marker
