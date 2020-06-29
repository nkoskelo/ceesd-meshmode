__copyright__ = "Copyright (C) 2020 Benjamin Sepanski"

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
import numpy.linalg as la


__doc__ = """
.. autofunction:: get_affine_reference_simplex_mapping
.. autofunction:: get_finat_element_unit_nodes
"""


# {{{ Map between reference simplices

def get_affine_reference_simplex_mapping(spat_dim, firedrake_to_meshmode=True):
    """
    Returns a function which takes a numpy array points
    on one reference cell and maps each
    point to another using a positive affine map.

    :arg spat_dim: The spatial dimension
    :arg firedrake_to_meshmode: If true, the returned function maps from
        the firedrake reference element to
        meshmode, if false maps from
        meshmode to firedrake. More specifically,
        :mod:`firedrake` uses the standard :mod:`FIAT`
        simplex and :mod:`meshmode` uses
        :mod:`modepy`'s
        `unit coordinates <https://documen.tician.de/modepy/nodes.html>`_.
    :return: A function which takes a numpy array of *n* points with
             shape *(dim, n)* on one reference cell and maps
             each point to another using a positive affine map.
             Note that the returned function performs
             no input validation.
    """
    # validate input
    assert isinstance(spat_dim, int)
    assert spat_dim >= 0
    assert isinstance(firedrake_to_meshmode, bool)

    from FIAT.reference_element import ufc_simplex
    from modepy.tools import unit_vertices
    # Get the unit vertices from each system,
    # each stored with shape *(dim, nunit_vertices)*
    firedrake_unit_vertices = np.array(ufc_simplex(spat_dim).vertices).T
    modepy_unit_vertices = unit_vertices(spat_dim).T

    if firedrake_to_meshmode:
        from_verts = firedrake_unit_vertices
        to_verts = modepy_unit_vertices
    else:
        from_verts = modepy_unit_vertices
        to_verts = firedrake_unit_vertices

    # Compute matrix A and vector b so that A f_i + b -> t_i
    # for each "from" vertex f_i and corresponding "to" vertex t_i
    assert from_verts.shape == to_verts.shape
    dim, nvects = from_verts.shape

    # If only have on vertex, have A = I and b = to_vert - from_vert
    if nvects == 1:
        shift = to_verts[:, 0] - from_verts[:, 0]

        def affine_map(points):
            return points + shift[:, np.newaxis]
    # Otherwise, we have to solve for A and b
    else:
        # span verts: v1 - v0, v2 - v0, ...
        from_span_verts = from_verts[:, 1:] - from_verts[:, 0, np.newaxis]
        to_span_verts = to_verts[:, 1:] - to_verts[:, 0, np.newaxis]
        # mat maps (fj - f0) -> (tj - t0), our "A"
        mat = la.solve(from_span_verts, to_span_verts)
        # A f0 + b -> t0 so b = t0 - A f0
        shift = to_verts[:, 0] - np.matmul(mat, from_verts[:, 0])

        # Explicitly ensure A is positive
        if la.det(mat) < 0:
            from meshmode.mesh.processing import get_simplex_element_flip_matrix
            flip_matrix = get_simplex_element_flip_matrix(1, to_verts)
            mat = np.matmul(flip_matrix, mat)

        def affine_map(points):
            return np.matmul(mat, points) + shift[:, np.newaxis]

    return affine_map

# }}}


# {{{ Get firedrake unit nodes

def get_finat_element_unit_nodes(finat_element):
    """
    Returns the unit nodes used by the FInAT element in firedrake's
    (equivalently, FInAT/FIAT's) reference coordinates

    :arg finat_element: A :class:`finat.finiteelementbase.FiniteElementBase`
        instance (i.e. a firedrake function space's reference element).
        The refernce element of the finat element *MUST* be a simplex
    :return: A numpy array of shape *(dim, nunit_nodes)* holding the unit
             nodes used by this element. *dim* is the dimension spanned
             by the finat element's reference element
             (see its ``cell`` attribute)
    """
    from FIAT.reference_element import Simplex
    assert isinstance(finat_element.cell, Simplex), \
        "Reference element of the finat element MUST be a simplex"
    # point evaluators is a list of functions *p_0,...,p_{n-1}*.
    # *p_i(f)* evaluates function *f* at node *i* (stored as a tuple),
    # so to recover node *i* we need to evaluate *p_i* at the identity
    # function
    point_evaluators = finat_element._element.dual.nodes
    unit_nodes = [p(lambda x: x) for p in point_evaluators]
    unit_nodes = np.array(unit_nodes).T

    return unit_nodes

# }}}
