from itertools import chain

__all__ = [
    "is_biconnected",
    "biconnected_components",
    "generator_biconnected_components_nodes",
    "generator_biconnected_components_edges",
    "generator_articulation_points"
]


def is_biconnected(G):
    bc_nodes = list(generator_biconnected_components_nodes(G))
    if len(bc_nodes) == 1:
        return len(bc_nodes[0]) == len(G) # avoid situations where there is isolated vertex
    return False


# TODO: get the subgraph of each biconnected graph
def biconnected_components(G):
    pass


def generator_biconnected_components_nodes(G):
    for component in _biconnected_dfs_record_edges(G, need_components=True):
        # TODO: only one edge = biconnected_component?
        yield set(chain.from_iterable(comp))


def generator_biconnected_components_edges(G):
    for component in _biconnected_dfs_record_edges(G, need_components=True):
        yield component


def generator_articulation_points(G):
    seen = set()
    for cut_vertex in _biconnected_dfs_record_edges(G, need_components=False):
        if cut_vertex not in seen:
            seen.add(cut_vertex)
            yield cut_vertex


def _biconnected_dfs_record_edges(G, need_components=True):
    r"""
    References:
    https://www.cnblogs.com/nullzx/p/7968110.html
    https://blog.csdn.net/gauss_acm/article/details/43493903
    """
    # record edges of each biconnected component in traversal
    # Copied version from NetworkX
    # depth-first search algorithm to generate articulation points
    # and biconnected components

    visited = set()
    for start in G:
        if start in visited:
            continue
        discovery = {start: 0}  # time of first discovery of node during search
        low = {start: 0}
        root_children = 0
        visited.add(start)
        edge_stack = []
        stack = [(start, start, iter(G[start]))]
        while stack:
            grandparent, parent, children = stack[-1]
            try:
                child = next(children)
                if grandparent == child:
                    continue
                if child in visited:
                    if discovery[child] <= discovery[parent]:  # back edge
                        low[parent] = min(low[parent], discovery[child])
                        if need_components:
                            edge_stack.append((parent, child))
                else:
                    low[child] = discovery[child] = len(discovery)
                    visited.add(child)
                    stack.append((parent, child, iter(G[child])))
                    if need_components:
                        edge_stack.append((parent, child))
            except StopIteration:
                stack.pop()
                if len(stack) > 1:
                    if low[parent] >= discovery[grandparent]:
                        if need_components:
                            ind = edge_stack.index((grandparent, parent))
                            yield edge_stack[ind:]
                            edge_stack = edge_stack[:ind]
                        else:
                            yield grandparent
                    low[grandparent] = min(low[parent], low[grandparent])
                elif stack:  # length 1 so grandparent is root
                    root_children += 1
                    if need_components:
                        ind = edge_stack.index((grandparent, parent))
                        yield edge_stack[ind:]
        if not need_components:
            # root node is articulation point if it has more than 1 child
            if root_children > 1:
                yield start


def _biconnected_dfs_record_nodes(G, need_components=True):
    # record nodes of each biconnected component in traversal
    # Not used.
    visited = set()
    for start in G:
        if start in visited:
            continue
        discovery = {start: 0}  # time of first discovery of node during search
        low = {start: 0}
        root_children = 0
        visited.add(start)
        node_stack = [start]
        stack = [(start, start, iter(G[start]))]
        while stack:
            grandparent, parent, children = stack[-1]
            try:
                child = next(children)
                if grandparent == child:
                    continue
                if child in visited:
                    if discovery[child] <= discovery[parent]:  # back edge
                        low[parent] = min(low[parent], discovery[child])
                else:
                    low[child] = discovery[child] = len(discovery)
                    visited.add(child)
                    stack.append((parent, child, iter(G[child])))
                    if need_components:
                        node_stack.append(child)
            except StopIteration:
                stack.pop()
                if len(stack) > 1:
                    if low[parent] >= discovery[grandparent]:
                        if need_components:
                            ind = node_stack.index(grandparent)
                            yield node_stack[ind:]
                            node_stack = node_stack[:ind+1]
                        else:
                            yield grandparent
                    low[grandparent] = min(low[parent], low[grandparent])
                elif stack:  # length 1 so grandparent is root
                    root_children += 1
                    if need_components:
                        ind = node_stack.index(grandparent)
                        yield node_stack[ind:]
        if not need_components:
            # root node is articulation point if it has more than 1 child
            if root_children > 1:
                yield start
