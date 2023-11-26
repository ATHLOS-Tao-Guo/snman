import networkx as nx
import json
from . import utils


def add_hierarchies(G, n):
    uvks = set(G.in_edges(n, keys=True)).union(set(G.out_edges(n, keys=True)))
    hierarchies = {G.edges[uvk].get('hierarchy') for uvk in uvks}
    G.nodes[n]['hierarchies'] = hierarchies


def cast_attributes_for_export(G, n):

    data = G.nodes[n]
    data['hierarchies'] = str(data.get('hierarchies'))
    data['layers'] = str(data.get('layers'))

def cast_attributes_for_import(G, n):

    data = G.nodes[n]
    data['hierarchies'] = utils.object_from_string(data['hierarchies'])
