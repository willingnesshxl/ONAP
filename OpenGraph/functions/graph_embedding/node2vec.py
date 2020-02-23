import sys
sys.path.append('../../../')
import OpenGraph as og

from node2vec import Node2Vec
import random
import numpy as np
from tqdm import tqdm

__all__ = [
    "node2vec_multi_thread",
    "node2vec"
]


def node2vec_multi_thread(G, dimensions=128, walk_length=80, num_walks=10, p=1.0, q=1.0, weight_key="weight", workers=1,
                          **skip_gram_params):
    """
    Returns 
        1. The embedding vector of each node via node2vec 
        2. The most similar nodes of each node and its similarity
    Packaged functions implemented by https://towardsdatascience.com/node2vec-embeddings-for-graph-data-32a866340fef
    Using Word2Vec model of package gensim.

    Parameters
    ----------
    G : graph

    dimensions : int
        Embedding dimensions (default: 128)

    walk_length : int
        Number of nodes in each walk (default: 80)

    num_walks : int
        Number of walks per node (default: 10)

    p : float
        The return hyper parameter (default: 1.0)

    q : float
        The inout parameter (default: 1.0)

    weight_key : string
        On weighted graphs, this is the key for the weight attribute (default: 'weight')

    workers : int
        Number of workers for parallel execution (default: 1)

    skip_gram_params : dict
        Parameteres for gensim.models.Word2Vec - do not supply 'size' it is taken from the Node2Vec 'dimensions' parameter
    """
    G_index, index_of_node, node_of_index = G.to_index_node_graph()

    node2vec = Node2Vec(graph=G_index, dimensions=dimensions,
                        walk_length=walk_length, num_walks=num_walks, workers=workers)

    # Embed nodes
    model = node2vec.fit(**skip_gram_params)

    embedding_vector = dict()
    most_similar_nodes_of_node = dict()

    def change_string_to_node_from_gensim_return_value(value_including_str):
        # As the return value of gensim model.wv.most_similar includes string index in G_index,
        # the string index should be changed to the original node element in G.
        result = []
        for (node_index, value) in value_including_str:
            node_index = int(node_index)
            node = node_of_index[node_index]
            result.append((node, value))
        return result

    for node in G.nodes:
        # Output node names are always strings in gensim
        embedding_vector[node] = model.wv[str(index_of_node[node])]

        most_similar_nodes = model.wv.most_similar(str(index_of_node[node]))
        most_similar_nodes_of_node[node] = change_string_to_node_from_gensim_return_value(
            most_similar_nodes)

    del G_index
    return embedding_vector, most_similar_nodes_of_node


def node2vec(G, dimensions=128, walk_length=80, num_walks=10, p=1.0, q=1.0, weight_key=None, **skip_gram_params):
    """
    Returns 
        1. The embedding vector of each node via node2vec: https://arxiv.org/abs/1607.00653
        2. The most similar nodes of each node and its similarity
    Using Word2Vec model of package gensim.

    Parameters
    ----------
    G : graph

    dimensions : int
        Embedding dimensions (default: 128)

    walk_length : int
        Number of nodes in each walk (default: 80)

    num_walks : int
        Number of walks per node (default: 10)

    p : float
        The return hyper parameter (default: 1.0)

    q : float
        The inout parameter (default: 1.0)

    weight_key : string
        On weighted graphs, this is the key for the weight attribute (default: 'weight')

    skip_gram_params : dict
        Parameteres for gensim.models.Word2Vec - do not supply 'size', it is taken from the 'dimensions' parameter
    """
    G_index, index_of_node, node_of_index = G.to_index_node_graph()

    walks = simulate_walks(
        G_index, walk_length=walk_length, num_walks=num_walks,
        p=p, q=q, weight_key=weight_key)
    model = learn_embeddings(
        walks=walks, dimensions=dimensions, **skip_gram_params)

    embedding_vector = dict()
    most_similar_nodes_of_node = dict()

    def change_string_to_node_from_gensim_return_value(value_including_str):
        # As the return value of gensim model.wv.most_similar includes string index in G_index,
        # the string index should be changed to the original node element in G.
        result = []
        for (node_index, value) in value_including_str:
            node_index = int(node_index)
            node = node_of_index[node_index]
            result.append((node, value))
        return result

    for node in G.nodes:
        # Output node names are always strings in gensim
        embedding_vector[node] = model.wv[str(index_of_node[node])]

        most_similar_nodes = model.wv.most_similar(str(index_of_node[node]))
        most_similar_nodes_of_node[node] = change_string_to_node_from_gensim_return_value(
            most_similar_nodes)

    del G_index
    return embedding_vector, most_similar_nodes_of_node


def simulate_walks(G, walk_length, num_walks, p, q, weight_key=None):
    alias_nodes, alias_edges = _preprocess_transition_probs(
        G, p, q, weight_key)
    walks = []
    nodes = list(G.nodes)
    print('Walk iteration:')
    for walk_iter in tqdm(range(num_walks)):
        random.shuffle(nodes)
        for node in nodes:
            walks.append(_node2vec_walk(G,
                                        walk_length=walk_length, start_node=node,
                                        alias_nodes=alias_nodes, alias_edges=alias_edges))

    return walks


def _preprocess_transition_probs(G, p, q, weight_key=None):
    is_directed = G.is_directed()
    alias_nodes = {}

    for node in G.nodes:
        if weight_key is None:
            unnormalized_probs = [1.0 for nbr in sorted(G.neighbors(node))]
        else:
            unnormalized_probs = [G[node][nbr][weight_key]
                                  for nbr in sorted(G.neighbors(node))]
        norm_const = sum(unnormalized_probs)
        normalized_probs = [
            float(u_prob)/norm_const for u_prob in unnormalized_probs]
        alias_nodes[node] = _alias_setup(normalized_probs)

    alias_edges = {}
    triads = {}

    if is_directed:
        for edge in G.edges:
            alias_edges[(edge[0], edge[1])] = _get_alias_edge(
                G, edge[0], edge[1], p, q, weight_key)
    else:
        for edge in G.edges:
            alias_edges[(edge[0], edge[1])] = _get_alias_edge(
                G, edge[0], edge[1], p, q, weight_key)
            alias_edges[(edge[1], edge[0])] = _get_alias_edge(
                G, edge[1], edge[0], p, q, weight_key)

    return alias_nodes, alias_edges


def _get_alias_edge(G, src, dst, p, q, weight_key=None):
    unnormalized_probs = []

    if weight_key is None:
        for dst_nbr in sorted(G.neighbors(dst)):
            if dst_nbr == src:
                unnormalized_probs.append(1.0/p)
            elif G.has_edge(dst_nbr, src):
                unnormalized_probs.append(1.0)
            else:
                unnormalized_probs.append(1.0/q)
    else:
        for dst_nbr in sorted(G.neighbors(dst)):
            if dst_nbr == src:
                unnormalized_probs.append(G[dst][dst_nbr][weight_key]/p)
            elif G.has_edge(dst_nbr, src):
                unnormalized_probs.append(G[dst][dst_nbr][weight_key])
            else:
                unnormalized_probs.append(G[dst][dst_nbr][weight_key]/q)

    norm_const = sum(unnormalized_probs)
    normalized_probs = [
        float(u_prob)/norm_const for u_prob in unnormalized_probs]

    return _alias_setup(normalized_probs)


def _alias_setup(probs):
    K = len(probs)
    q = np.zeros(K)
    J = np.zeros(K, dtype=np.int)

    smaller = []
    larger = []
    for kk, prob in enumerate(probs):
        q[kk] = K*prob
        if q[kk] < 1.0:
            smaller.append(kk)
        else:
            larger.append(kk)

    while len(smaller) > 0 and len(larger) > 0:
        small = smaller.pop()
        large = larger.pop()

        J[small] = large
        q[large] = q[large] + q[small] - 1.0
        if q[large] < 1.0:
            smaller.append(large)
        else:
            larger.append(large)

    return J, q


def _node2vec_walk(G, walk_length, start_node, alias_nodes, alias_edges):
    '''
    Simulate a random walk starting from start node.
    '''
    walk = [start_node]

    while len(walk) < walk_length:
        cur = walk[-1]
        cur_nbrs = sorted(G.neighbors(cur))
        if len(cur_nbrs) > 0:
            if len(walk) == 1:
                walk.append(cur_nbrs[_alias_draw(
                    alias_nodes[cur][0], alias_nodes[cur][1])])
            else:
                prev = walk[-2]
                next_node = cur_nbrs[_alias_draw(
                    alias_edges[(prev, cur)][0], alias_edges[(prev, cur)][1])]
                walk.append(next_node)
        else:
            break

    return walk


def _alias_draw(J, q):
    K = len(J)
    kk = int(np.floor(np.random.rand()*K))
    if np.random.rand() < q[kk]:
        return kk
    else:
        return J[kk]


def learn_embeddings(walks, dimensions, **skip_gram_params):
    '''
    Learn embeddings with Word2Vec.
    '''
    from gensim.models import Word2Vec

    walks = [list(map(str, walk)) for walk in walks]

    if 'size' not in skip_gram_params:
        skip_gram_params['size'] = dimensions

    model = Word2Vec(walks, **skip_gram_params)

    return model


if __name__ == "__main__":
    graph = og.Graph()
    graph.add_edge(2, 4)
    graph.add_edge(3, 4)
    graph.add_edge(4, 5)
    graph.add_edge(2, 5)
    graph.add_edge(6, 'a')
    graph.add_edge(3, 6)

    skip_gram_params = dict(window=10, min_count=1, batch_words=4)

    embedding_vector, most_similar_nodes_of_node = node2vec(
        G=graph,
        dimensions=64, walk_length=30,
        num_walks=2000, **skip_gram_params
    )

    print(embedding_vector)
    print(most_similar_nodes_of_node)
