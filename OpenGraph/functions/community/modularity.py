from itertools import product

__all__ = [
    "modularity"
]

def modularity(G, communities, weight='weight'):
    # TODO: multigraph not included. See networkx.
    """
    Returns the modularity of the given partition of the graph.
    Modularity is defined in [1]_ as

    .. math::

        Q = \frac{1}{2m} \sum_{ij} \left( A_{ij} - \frac{k_ik_j}{2m}\right)
            \delta(c_i,c_j)

    where $m$ is the number of edges, $A$ is the adjacency matrix of
    `G`, $k_i$ is the degree of $i$ and $\delta(c_i, c_j)$
    is 1 if $i$ and $j$ are in the same community and 0 otherwise.

    Parameters
    ----------
    G : graph

    communities : list or iterable of set of nodes
        These node sets must represent a partition of G's nodes.

    weight : the key for edge weight

    Returns
    ----------
    Q : float
        The modularity of the paritition.

    References
    ----------
    .. [1] M. E. J. Newman *Networks: An Introduction*, page 224.
       Oxford University Press, 2011.

    """

    if not isinstance(communities, list):
        communities = list(communities)

    directed = G.is_directed()
    m = G.size(weight=weight)
    if directed:
        out_degree = dict(G.out_degree(weight=weight))
        in_degree = dict(G.in_degree(weight=weight))
        norm = 1 / m
    else:
        out_degree = dict(G.degree(weight=weight))
        in_degree = out_degree
        norm = 1 / (2 * m)

    def val(u, v):
        try:
            w = G[u][v].get(weight, 1)
        except KeyError:
            w = 0
        # Double count self-loops if the graph is undirected.
        if u == v and not directed:
            w *= 2
        return w - in_degree[u] * out_degree[v] * norm

    Q = sum(val(u, v) for c in communities for u, v in product(c, repeat=2))
    return Q * norm


if __name__ == "__main__":
    import sys
    sys.path.append('../../../')
    import OpenGraph as og
    
    g = og.Graph()
    edges1 = [(1, 2), (2, 3), (1, 3), (3, 4), (4, 5), (4, 6), (5, 6)]
    g.add_edges(edges1)

    cmnts = [frozenset([1, 2, 3]), frozenset([4, 5, 6])]
    print(modularity(G=g, communities=cmnts))


