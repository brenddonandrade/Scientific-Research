# -*- coding: utf-8 -*-
"""edge-effects-data.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1-bxExubofghxA_f2nUUf_4YoYUhhfrLD

## Downloads
"""

#!pip install osmnx

"""## Imports"""

import osmnx as ox
import plotly.express as px
import networkx as nx
import numpy as np
import pandas as pd
#from shapely.constructive import normalize
import requests
from io import StringIO
import seaborn as sns
import matplotlib.pyplot as plt
import time as t
import ast

"""## Constants"""

# certo
# São Paulo (centro)
#UF = 'sp'
#CENTER_POINT = -23.209,-45.850

# São José
# UF = 'sj'
# CENTER_POINT = -23.220,-45.891

# Rio de Janeiro
# UF = 'rj'
# CENTER_POINT = -22.909,-43.184

# Barcelona
# UF = 'ba'
# CENTER_POINT = 41.390, 2.166

# Manhattan
UF = 'ma'
CENTER_POINT = 40.748, -73.985

# Brasilia
#UF = 'br'
#CENTER_PONIT = -15.800, -47.867

MAX_RADIUS = 1500
RADIUS_SUBGRAPH = 400
MEASURES = 12


# ==============================
# teste
# CENTER_POINT = -23.209,-45.850
# MAX_RADIUS = 1000
# RADIUS_SUBGRAPH = 500
# MEASURES = 2

"""## Support functions

The point-wise vulnerability (citar Gio) :

\begin{equation}
    V(i) = \frac{E(G) - E(G, i)}{E(G)}
\end{equation}

where $V(i)$ is the point-wise vulnerability of the node $i$, $E(G)$ is the global efficiency of the network, and $E(G,i)$ is the global efficiency of a new similar network, being the only diffrence is the node $i$ disconnection from the network.
"""

def vulnerability_node(graph):
    vul = {}
    similar_graph = nx.Graph(graph)
    for node in similar_graph.nodes:

        # Remotion node
        similar_graph_copy = similar_graph.copy()
        similar_graph_copy.remove_node(node)

        # getting efficency
        eff_before = nx.global_efficiency(similar_graph)
        eff_after = nx.global_efficiency(similar_graph_copy)

        vul[node] = (eff_before - eff_after)/eff_before


    graph.graph['vulnerability-node']= vul

def vulnerability_edge(graph):
    vul = {}
    simple_graph = nx.Graph(graph)
    for u, v in simple_graph.edges():

        # Remotion node
        simple_graph_copy = simple_graph.copy()
        simple_graph_copy.remove_edge(u, v)

        # getting efficency
        eff_before = nx.global_efficiency(simple_graph)
        eff_after = nx.global_efficiency(simple_graph_copy)

        vul[(u, v, 0)] = (eff_before - eff_after)/eff_before

    graph.graph['vulnerability-edge']= vul

"""## Getting network"""

G = ox.graph.graph_from_point(CENTER_POINT, dist=MAX_RADIUS, dist_type='bbox', network_type='drive', simplify=True)

# len(G)

"""## Generating data"""

def generating_data(graph):

    # Nodes attributes
    # calculate node degree centrality
    dc = nx.degree_centrality(graph)
    nx.set_node_attributes(graph, values=dc, name="dc")

    # calculate node closeness centrality
    cc = nx.closeness_centrality(graph)
    nx.set_node_attributes(graph, values=cc, name="cc")

    # calculate node betweenness centrality
    bc = nx.betweenness_centrality(graph)
    nx.set_node_attributes(graph, values=bc, name="nbc")

    # vulnerability per efficiency - node(simple graph)
    vulnerability_node(graph)
    nx.set_node_attributes(graph, values=graph.graph['vulnerability-node'], name='vul')


    # calculete communicability of the nodes
    # Note that communicability is defined for a simple graph (our graph is not of this type)
    #simple_graph = nx.Graph(graph)
    #com = nx.communicability_exp(simple_graph)
    # for node_p, nodes_values in com.items():
    #     let_com = 0
    #     for node_q, com_value in nodes_values.items():
    #         let_com = let_com + com_value

    #     dict_com[node_p] = (let_com/len(list(graph.nodes)))
    #nx.set_node_attributes(graph, values=com, name="com")


    # graph attributes
    # calculate efficiency
    # e = nx.global_efficiency(simple_graph)
    # dict_eff = {}
    # for node in simple_graph:
        # dict_eff[node] = e

    # nx.set_node_attributes(graph, values=dict_eff, name='eff')



    return graph

def create_data_frame(graph):
    # Save data
    # nodes
    nodes_data = list(graph.nodes(data=True))
    nodes_dict = {}


    # edges
    edges_data = list(graph.edges(data=True))
    edges_dict = {}


    for i in range(len(list(nodes_data))):
        for node, data in nodes_data:
            data['node'] = int(node)
            data['efficiency'] = graph.graph['efficiency']
            nodes_dict[int(node)] = data

    nodes_df = pd.DataFrame(nodes_dict)
    nodes_df = nodes_df.transpose()


    for i in range(len(list(edges_data))):
        for u, v,  data in edges_data:
            data['edge'] = (u ,v)
            edges_dict[(u ,v)] = data

    edges_df = pd.DataFrame(edges_dict)
    edges_df = edges_df.transpose()

    return nodes_df, edges_df

# Save data for tests
def save_data(center_point, measures, size_subgraph , max_radius, uf):
    interval = (max_radius - size_subgraph)//measures;
    print(interval)

    for size in range(size_subgraph, max_radius + interval, interval):
        time_start = t.time()
        graph = ox.graph.graph_from_point(center_point, dist = size, dist_type='bbox', network_type='drive', truncate_by_edge=False)
        graph = generating_data(graph)

        nodes_df, edges_df = ox.utils_graph.graph_to_gdfs(graph)
        nodes_df.to_csv(f'data-nodes-{uf}-{size}.csv')

        time_end = t.time()

        time_code = (time_end - time_start)
        print(f'size: {size}\t time: {time_code:}s')

    return nodes_df

"""## Steps to plots data comming from github"""

# Getting file
def getting_file_github(url):
    '''
    Parameters
    ----------
    url: raw url of the file
    '''
    response = requests.get(url)

    # Check if you can get the file
    if response.status_code == 200:
        csv_data = response.text
        csv_buffer = StringIO(csv_data)
        df = pd.read_csv(csv_buffer, index_col=0)
    else:
        print(f"Falha ao obter o arquivo CSV do GitHub {url}.\nCódigo de status:", response.status_code)
        df = None

    return df

"""## Requests"""

# Uncomment the line below to generate your own data
nodes_df = save_data(CENTER_POINT, MEASURES-1, RADIUS_SUBGRAPH, MAX_RADIUS, UF)
# node_df_500 = pd.read_csv('data-nodes-500.csv')
# node_df_1000 = pd.read_csv('data-nodes-1000.csv')


# # # Reading csv
# node_df_1500 = pd.read_csv('data-nodes-1500.csv')
# node_df_1600 = pd.read_csv('data-nodes-1600.csv')
# node_df_1700 = pd.read_csv('data-nodes-1700.csv')
# node_df_1800 = pd.read_csv('data-nodes-1800.csv')
# node_df_1900 = pd.read_csv('data-nodes-1900.csv')
# node_df_2000 = pd.read_csv('data-nodes-2000.csv')

# # # Reading csv
# node_df_1500 = work_with_data(node_df_1500, 'osmid')
# node_df_1600 = work_with_data(node_df_1600, 'osmid')
# node_df_1700 = work_with_data(node_df_1700, 'osmid')
# node_df_1800 = work_with_data(node_df_1800, 'osmid')
# node_df_1900 = work_with_data(node_df_1900, 'osmid')
# node_df_2000 = work_with_data(node_df_2000, 'osmid')



# Uncomment the lines below to get data from the github repository
# Nodes
# node_df_1500 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-1500.csv')
# node_df_1600 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-1600.csv')
# node_df_1700 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-1700.csv')
# node_df_1800 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-1800.csv')
# node_df_1900 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-1900.csv')
# node_df_2000 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2000.csv')
# node_df_2100 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2100.csv')
# node_df_2200 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2200.csv')
# node_df_2300 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2300.csv')
# node_df_2400 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2400.csv')
# node_df_2500 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2500.csv')
# node_df_2600 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2600.csv')
# node_df_2700 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2700.csv')
# node_df_2800 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2800.csv')
# node_df_2900 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-2900.csv')
# node_df_3000 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-nodes-3000.csv')

# # Edges
# edge_df_1500 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-1500.csv')
# edge_df_1600 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-1600.csv')
# edge_df_1700 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-1700.csv')
# edge_df_1800 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-1800.csv')
# edge_df_1900 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-1900.csv')
# edge_df_2000 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2000.csv')
# edge_df_2100 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2100.csv')
# edge_df_2200 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2200.csv')
# edge_df_2300 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2300.csv')
# edge_df_2400 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2400.csv')
# edge_df_2500 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2500.csv')
# edge_df_2600 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2600.csv')
# edge_df_2700 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2700.csv')
# edge_df_2800 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2800.csv')
# edge_df_2900 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-2900.csv')
# edge_df_3000 = getting_file_github('https://raw.githubusercontent.com/brenddonandrade/Scientific-Research/main/projetos/roadNetworks/data/case-2/data-edges-3000.csv')

# nodes_df

# node_df_500 = pd.read_csv('data-nodes-com-sp-500.csv')
# node_df_1000 = pd.read_csv('data-nodes-com-sp-1000.csv')

# index_name = list(node_df_500['osmid'].values)
# node_df_500.index = index_name

# node_df_500['com'][1454006738]

# for value_1, value_2 in node_df_500['com'].items():
    # print(value_1, dict(value_2).keys())

# simple_graph = nx.Graph(G)
# com = nx.communicability_exp(simple_graph)

# com

# node_df_500

# list_df_nodes = [node_df_500, node_df_1000]

# list_df_nodes = [node_df_1500, node_df_1600, node_df_1700, node_df_1800,\
#                 node_df_1900, node_df_2000, node_df_2100, node_df_2200, \
#                 node_df_2300, node_df_2400, node_df_2500, node_df_2600,\
#                 node_df_2700, node_df_2800, node_df_2900, node_df_3000 ]

# list_df_edges = [edge_df_1500, edge_df_1600, edge_df_1700, edge_df_1800,\
#                 edge_df_1900, edge_df_2000, edge_df_2100, edge_df_2200, \
#                 edge_df_2300, edge_df_2400, edge_df_2500, edge_df_2600,\
#                 edge_df_2700, edge_df_2800, edge_df_2900, edge_df_3000 ]

# check change in node
def change_measure_node_github(df_1, df_2, measure):

    # Vou criar DataFrames de exemplo para demonstração
    # Combine os DataFrames em um único DataFrame
    df_combined = pd.concat([df_1, df_2], keys=['DataFrame1', 'DataFrame2'])

    print(df_combined)
    # # Crie o scatter plot
    sns.scatterplot(data=df_combined, x=measure, y=measure, hue=df_combined.index.get_level_values(0))
    plt.xlabel('Dados do DataFrame 1')
    plt.ylabel('Dados do DataFrame 2')
    plt.title('Scatter Plot entre DataFrames')
    plt.show()


    # return df_diff
# Agora 'common_rows' contém a diferença nas colunas 'coluna1' e 'coluna2' para as linhas comuns

def plot_matrix(dfs, measure, begin, interval):

    i = begin
    dfs_subset = pd.DataFrame()
    for df in dfs:
        dfs_subset[f'node-{i}'] = df[measure]
        i = i + interval

    sns.set(style="ticks")
    sns.pairplot(dfs_subset)
    plt.suptitle(measure)
    plt.show()

    return dfs_subset

"""## Statistics Measures"""

def generate_statistics_measures(dfs, measure, start, interval):

    i = start
    dfs_subset = pd.DataFrame()
    for df in dfs:
        dfs_subset[f'node-{i}'] = df[measure]
        i = i + interval

    df_diff = pd.DataFrame()
    # diferenças entre as colunas
    data_count = []
    data_mean = []
    data_std = []
    data_min = []
    data_25 = []
    data_50 = []
    data_75 = []
    data_max = []
    index_name = []

    i = 0
    for df_i in dfs_subset:
        j = 0
        for df_j in dfs_subset:
            if j == (i+1):
                # antes (pelo valor absoluto)
                # df_diff[df_j, df_i] = abs(dfs_subset[df_j] - dfs_subset[df_i])
                # como vou dividir pela media?

                # agora
                df_diff[df_j, df_i] = (dfs_subset[df_j] - dfs_subset[df_i])/dfs_subset[df_j]
                list_data = list(df_diff[(df_j, df_i)].describe())
                data_count.append(list_data[0])
                data_mean.append(list_data[1])
                data_std.append(list_data[2])
                data_min.append(list_data[3])
                data_25.append(list_data[4])
                data_50.append(list_data[5])
                data_75.append(list_data[6])
                data_max.append(list_data[7])
                # index_name.append((df_j, df_i))
            j = j+1
            # print(f'i: {i} j: {j}')

        i = i+1

    # df with statistics measures
    df = pd.DataFrame()
    df['count'] = pd.DataFrame(data_count)
    df['mean'] = pd.DataFrame(data_mean)
    df['std'] = pd.DataFrame(data_std)
    df['min'] = pd.DataFrame(data_min)
    df['25'] = pd.DataFrame(data_25)
    df['50'] = pd.DataFrame(data_50)
    df['75'] = pd.DataFrame(data_75)
    df['max'] = pd.DataFrame(data_max)

    index_name = list(dfs[0]['osmid'].values)
    df_diff.index = index_name

    return df_diff, df

# df_teste = (node_df_1000['vul']-node_df_500['vul'])/node_df_1000['vul']

# df_teste

# df_diff, df = generate_statistics_measures(list_df_nodes, 'vul', RADIUS_SUBGRAPH, (MAX_RADIUS-RADIUS_SUBGRAPH)//(MEASURES-1))

# df_diff

# list(list_df_nodes[0]['osmid'].values)

# df

# df_diff

# df

def plot_measure(df, measure):

    list_index = []
    for u, v in df.index:
        u_list = u.split('-')[1]
        v_list = v.split('-')[1]
        list_index.append(f'{v_list}-{u_list}')


    fig = px.scatter(df, x=list_index ,y =df[measure])

    fig.update_layout(
        xaxis_title_text= 'dist + δdist',
        yaxis_title_text= f'abs[{measure}]',

        width = 800,
        height= 600,
    )

    # Retired the grid
    fig.update_xaxes (
        showgrid=True,
        title_font = dict(
            size= 24,
            family= 'Arial'),
        tickfont=dict(
            size=20),
        ticks = 'inside',
        nticks = len(df.index)
        )

    fig.update_yaxes (
        showgrid=True,
        title_font = dict(
            size= 24,
            family= 'Arial'),
        tickfont=dict(
            size=20),
        ticks = 'inside',
        nticks = len(df.index)
        )

    fig.show()

# df['vulnerability']

# node_df_1500

# plot_measure(df,  'max')

def create_subgraph(graph, central_node, radius):
    '''
    Parameters
    ----------
    graph: MultiDiGraph
        a graph stores nodes and edges

    central_node: node of the graph
        the center node where initiate path

    radius: int
        size of the path

    Create a subgraph from the given graph with
    central node or nodes that are at a distance smaller
    than the requested radius.
    '''
    subgraph = nx.ego_graph(G, central_node, radius=radius)
    return subgraph

# subgraph = create_subgraph(G, 1453990694, 10)

def emphasis(graph, item):

    if graph.has_node(item):

        # Especifique o nó que você deseja destacar
        node_to_highlight = item  # Substitua pelo ID do nó desejado

        # Crie uma lista de cores para os nós
        node_colors = ['r' if node == node_to_highlight else 'b' for node in graph.nodes()]

        # Plote o gráfico com a sobreposição do nó destacado
        ox.plot_graph(ox.project_graph(graph), node_color=node_colors, node_size=30, node_zorder=3, edge_color='gray', bgcolor='w')
    elif type((1,2)) == type(item):
        u, v = item
        if graph.has_edge(u, v):
            highlighted_edge = item # Substitua pelos IDs reais dos nós
            # Crie um dicionário de estilos para as arestas
            edge_colors = ['b' if e != highlighted_edge else 'r' for e in graph.edges(data=False)]

            # Plote o grafo com as arestas destacadas
            ox.plot_graph(ox.project_graph(graph), edge_color=edge_colors, node_color='gray', node_size=30, node_zorder=3, bgcolor='w')

    else:
        print(f'ERROR! The {item} is not a node or edge')

# emphasis(subgraph, (1453990700, 1453990695))
