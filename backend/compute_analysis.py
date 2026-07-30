from embeddings import tfidf, alibaba, random_model
from clusterings import cosine
import transfrom_data
import load_data
import sys
import pathlib
import json
import networkx as nx
import pandas as pd
import numpy as np
from collections import Counter
from dateutil import parser
from datetime import datetime
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform
import seaborn as sns


class Metric:
    def __init__(
        self,
        y_axis_type,
        y_axis_title,
        x_axis_type,
        x_axis_title,
        requires_confusion_mtx=False,
    ):
        self.y_axis_type: str = y_axis_type
        self.y_axis_title: str = y_axis_title
        self.x_axis_type: str = x_axis_type
        self.x_axis_title: str = x_axis_title
        self.requires_confusion_mtx: bool = requires_confusion_mtx


METRICS = {
    "edges": Metric("edges", "Number of edges", "thresholds", "Threshold (ε)"),
    "weak_components": Metric(
        "weak_components", "Number of weak components", "thresholds", "Threshold (ε)"
    ),
    "strong_components": Metric(
        "strong_components",
        "Number of strong components",
        "thresholds",
        "Threshold (ε)",
    ),
    "f1": Metric("f1", "f_1 score", "thresholds", "Threshold (ε)", True),
    "recall": Metric("recall", "Recall score", "thresholds", "Threshold (ε)", True),
    "precision": Metric(
        "precision", "Precision score", "thresholds", "Threshold (ε)", True
    ),
    "freq_total_degrees": Metric(
        "freq_total_degrees", "Number of nodes", "degrees", "Unique degrees"
    ),
    "freq_in_degrees": Metric(
        "freq_in_degrees", "Number of nodes", "degrees_in", "Unique in-degrees"
    ),
    "freq_out_degrees": Metric(
        "freq_out_degrees", "Number of nodes", "degrees_out", "Unique out-degrees"
    ),
    "freq_component_size_weak": Metric(
        "freq_component_size_weak",
        "Number of components",
        "component_size_weak",
        "Weak component size",
    ),
    "degree_dist_prob": Metric(
        "degree_dist_prob", "Degree distribution (P(k))", "degree_k", "Degree k"
    ),
    "maximum_component": Metric(
        "maximum_component",
        "Size of the largest weak component",
        "thresholds",
        "Threshold (ε)",
    ),
    "maximum_degree": Metric(
        "maximum_degree",
        "Largest degree",
        "thresholds",
        "Threshold (ε)",
    ),
    "maximum_pagerank": Metric(
        "maximum_pagerank",
        "Largest pagerank",
        "thresholds",
        "Threshold (ε)",
    ),
    "maximum_betweenness_centrality": Metric(
        "maximum_betweenness_centrality",
        "Largest betweenness centrality",
        "thresholds",
        "Threshold (ε)",
    ),
    "average_clustering": Metric(
        "average_clustering",
        "Average clustering",
        "thresholds",
        "Threshold (ε)",
    ),
    "average_path_length": Metric(
        "average_path_length",
        "Average shortest path length",
        "thresholds",
        "Threshold (ε)",
    ),
    "true_origins": Metric(
        "true_origins",
        "Number of true origins found",
        "thresholds",
        "Threshold (ε)",
    ),
    "clustermap": Metric(
        "clustermap",
        "i",
        "similarities",
        "j",
    ),
}

COMPUTE = {
    # "edges",
    # "weak_components",
    "true_origins",
    # "strong_components",
    # "f1",  # story id
    # "recall",  # story id
    # "precision",  # story id
    # "freq_total_degrees",
    # "freq_in_degrees",
    # "freq_out_degrees",
    # "freq_component_size_weak",
    # "degree_dist_prob",
    # "maximum_component",
    # "maximum_degree",
    # "maximum_betweenness_centrality",
    # "average_clustering",
    # "average_path_length", # Has to be strongly connected grapn
    # "clustermap",
}

for not_computed in set(METRICS.keys()).difference(COMPUTE):
    METRICS.pop(not_computed)
EMBEDDERS = ["tfidf", "alibaba"]
# EMBEDDERS = ["random"]
DATASET_NAME = ""
THRESHOLDS = [i / 100 for i in range(0, 100, 1)]


def save_result(result, dataset, embedder, score):
    res_path = pathlib.Path(f"./analysis_results/{dataset}/{embedder}")
    if not res_path.exists():
        res_path.mkdir(parents=True)

    score_path = res_path.as_posix() + f"/{score}"

    print("Writing results to ", score_path)
    with open(score_path, "w") as f:
        json.dump(result, f)


def construct_network(graph_data) -> nx.DiGraph:
    G = nx.DiGraph()
    for node in graph_data["nodes"]:
        G.add_node(node["key"])
    for edge in graph_data["edges"]:
        G.add_edge(edge["source"], edge["target"])
    return G


def compute_confusion_matrix(network: nx.DiGraph, graph_data: dict) -> dict:
    res = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}

    node_by_id = {node["key"]: node for node in graph_data["nodes"]}

    wcc = list(nx.weakly_connected_components(network))
    for component in wcc:
        if len(component) == 1:
            res["FN"] += 1
            continue
        story_ids = [node_by_id[node]["attributes"]["story_id"] for node in component]
        avg_story_id, count = Counter(story_ids).most_common(1)[0]

        for node in component:
            story_id = node_by_id[node]["attributes"]["story_id"]
            if story_id == avg_story_id:
                res["TP"] += 1
            else:
                res["FP"] += 1

    total = res["TP"] + res["FP"] + res["TN"] + res["FN"]
    assert total == network.number_of_nodes(), (
        "The total number should match with the amount of nodes"
    )

    return res


def compute_precision(conf_mtx):
    assert (conf_mtx["TP"] + conf_mtx["FP"]) != 0, "Should not be zero"
    return conf_mtx["TP"] / (conf_mtx["TP"] + conf_mtx["FP"])


def compute_recall(conf_mtx):
    assert (conf_mtx["TP"] + conf_mtx["FN"]) != 0, "Should not be zero"
    return conf_mtx["TP"] / (conf_mtx["TP"] + conf_mtx["FN"])


def compute_f1(conf_mtx):
    P = compute_precision(conf_mtx)
    R = compute_recall(conf_mtx)
    assert P + R != 0, "Should not be zero"
    return 2 * ((P * R) / (R + P))


def count_weak_components(network: nx.DiGraph, min_size=1) -> int:
    components = list(nx.weakly_connected_components(network))
    return len([s for s in components if len(s) >= min_size])


def count_strong_components(network: nx.DiGraph) -> int:
    return len(list(nx.strongly_connected_components(network)))


def size_distribution_of_weak_components(network: nx.DiGraph) -> tuple[list, list]:
    components = [len(comp) for comp in list(nx.weakly_connected_components(network))]
    counts = Counter(components)
    items = sorted(counts.items())
    x = [k for k, _ in items]
    y = [v for _, v in items]

    return x, y


def degree_distribution(G, mode="total"):
    """
    mode:
        'total' -> total degree
        'in'    -> in-degree
        'out'   -> out-degree
    """

    if mode == "in":
        degrees = [d for _, d in G.in_degree()]
    elif mode == "out":
        degrees = [d for _, d in G.out_degree()]
    else:
        degrees = [d for _, d in G.degree()]

    counts = Counter(degrees)

    items = sorted(counts.items())

    x = [k for k, _ in items]
    y = [v for _, v in items]

    return x, y


def compute_degree_distribution_probability(network: nx.DiGraph):
    degrees = [d for _, d in network.in_degree()]
    degree_dist = Counter(degrees)
    n = network.number_of_nodes()
    pk = {k: count / n for k, count in degree_dist.items()}
    x = sorted(pk.keys())
    y = [pk[k] for k in x]
    return x, y


def compute_true_origins(network: nx.DiGraph, graph_data):
    """How many true origins per stories have been connected to the component?"""
    node_by_id = {int(node["key"]): node for node in graph_data["nodes"]}
    wcc = list(nx.weakly_connected_components(network))

    oldest_node_by_story_id = {
        node["attributes"]["story_id"]: -1 for node in graph_data["nodes"]
    }

    for node in graph_data["nodes"]:
        node_pt = parser.parse(node["attributes"]["published_time"])
        if oldest_node_by_story_id[node["attributes"]["story_id"]] == -1:
            curr_pt = node_pt
        else:
            curr_pt = parser.parse(
                node_by_id[oldest_node_by_story_id[node["attributes"]["story_id"]]][
                    "attributes"
                ]["published_time"]
            )

        if node_pt <= curr_pt:
            oldest_node_by_story_id[node["attributes"]["story_id"]] = int(node["key"])

        # [print(ol, oldest_node_by_story_id[ol]) for ol in oldest_node_by_story_id]

    # print(oldest_node_by_story_id.values())
    # print(node_by_id[list(oldest_node_by_story_id.values())[0]])

    how_many_oldest_found = 0
    for comp in wcc:
        if len(comp) > 7:
            story_ids = [
                node_by_id[int(node)]["attributes"]["story_id"] for node in comp
            ]
            avg_story_id, count = Counter(story_ids).most_common(1)[0]
            nodes = [int(n) for n in comp]
            if oldest_node_by_story_id[avg_story_id] in nodes:
                how_many_oldest_found += 1

    return how_many_oldest_found


def compute_xy_values(data, thresholds: list, embedder: str = "alibaba"):
    new_data = []
    for d in data:
        if not d.embedding:
            continue
        new_data.append(d)
    data = new_data
    if embedder == "alibaba":
        # Alibaba
        embeddings = pd.DataFrame([d.embedding for d in data])
        distances = cosine.cluster(embeddings)
    elif embedder == "tfidf":
        # TF-IDF
        embeddings = tfidf.embed(data)
        distances = cosine.cluster(embeddings)
    elif embedder == "random":
        distances = random_model.embed(data)

    y_values = {k: [] for k in METRICS.keys()}
    x_values = {METRICS[y].x_axis_type: [] for y in y_values}

    print()
    x_values["thresholds"] = thresholds
    if any([v.x_axis_type == "thresholds" for v in METRICS.values()]):
        for i, th in enumerate(thresholds):
            print(
                f"Progress... {i + 1} / {len(thresholds)}\t{embedder}",
                " " * 80,
                end="\r",
            )
            cache_path = pathlib.Path(
                f"./graph_cache/{DATASET_NAME}/{embedder}/{th}.json"
            )
            if cache_path.exists():
                with open(cache_path, "r") as f:
                    graph_data = json.load(f)
            else:
                graph_data = transfrom_data.transform(
                    data, distances, {"threshold": th}
                )
                with open(cache_path, "w") as f:
                    json.dump(graph_data, f)
            network = construct_network(graph_data)
            if any([v.requires_confusion_mtx for v in METRICS.values()]):
                conf_mtx = compute_confusion_matrix(network, graph_data)
                if "f1" in y_values:
                    y_values["f1"].append(compute_f1(conf_mtx))
                if "recall" in y_values:
                    y_values["recall"].append(compute_recall(conf_mtx))
                if "precision" in y_values:
                    y_values["precision"].append(compute_precision(conf_mtx))
            if "weak_components" in y_values:
                y_values["weak_components"].append(count_weak_components(network))
            if "strong_components" in y_values:
                y_values["strong_components"].append(count_strong_components(network))
            if "edges" in y_values:
                y_values["edges"].append(network.number_of_edges())
            if "maximum_component" in y_values:
                y_values["maximum_component"].append(
                    max([len(com) for com in nx.weakly_connected_components(network)])
                )
            if "maximum_degree" in y_values:
                y_values["maximum_degree"].append(max([d for _, d in network.degree()]))

            if "maximum_pagerank" in y_values:
                y_values["maximum_pagerank"].append(
                    max([rank for rank in nx.pagerank(network).values()])
                )

            if "maximum_betweenness_centrality" in y_values:
                y_values["maximum_betweenness_centrality"].append(
                    max(
                        [
                            bc
                            for bc in nx.betweenness_centrality(
                                network, normalized=False
                            ).values()
                        ]
                    )
                )
            if "average_clustering" in y_values:
                y_values["average_clustering"].append(nx.average_clustering(network))
            if "average_path_length" in y_values:
                y_values["average_path_length"].append(
                    nx.average_shortest_path_length(network)
                )

            if "true_origins" in y_values:
                y_values["true_origins"].append(
                    compute_true_origins(network, graph_data)
                )

    # Dendrogram
    if "clustermap" in y_values:
        # Convert square matrix to condensed form
        actual_distances = 1 - distances
        actual_distances[np.abs(actual_distances) < 1e-12] = 0.0
        condensed = squareform(actual_distances)
        # Hierarchical clustering
        Z = linkage(condensed, method="average", optimal_ordering=True)

        plt.figure(figsize=(8, 5))
        dendrogram(
            Z,
            # truncate_mode="lastp",
            # p=100,  # show only the last 50 merged clusters
            color_threshold=0.71,
            show_leaf_counts=True,
        )
        plt.xlabel("Samples")
        plt.ylabel("Cosine Distance")
        # plt.show()

        plt.figure(figsize=(10, 4))
        plt.plot(Z[:, 2])
        plt.xlabel("Merge step")
        plt.ylabel("Distance")
        # plt.show()

        sns.clustermap(distances, row_linkage=Z, col_linkage=Z, figsize=(12, 12))
        # plt.show()
        plt.savefig(f"./analysis_media/{dataset_name}_{embedder}_clustermap.png")

    # In - versus out-degree heatmap
    if False and embedder == "alibaba":
        graph_data = transfrom_data.transform(data, distances, {"threshold": 0.85})
        network = construct_network(graph_data)

        degree_pairs = [
            (network.in_degree(n), network.out_degree(n)) for n in network.nodes()
        ]

        counts = Counter(degree_pairs)

        max_i = 0
        max_j = 0
        for c in counts:
            if c[0] > max_i:
                max_i = c[0]
            if c[1] > max_j:
                max_j = c[1]

        values = [[0 for _ in range(max_j + 1)] for _ in range(max_i + 1)]
        for c in counts:
            print(c)
            values[c[0]][c[1]] = counts[c]

        res = {"values": values}
        save_result(res, "combined_ground_news", "alibaba", "in-out-degree_matrix")

    # if "freq_total_degrees" in y_values:
    #     snapshot_thresholds = {
    #         "alibaba": [0.80, 0.82, 0.85],
    #         "tfidf": [0.4, 0.5, 0.6],
    #     }
    #     (
    #         x_values[METRICS["freq_total_degrees"].x_axis_type],
    #         y_values["freq_total_degrees"],
    #     ) = analyze_over_threshold_snapshots(
    #         data,
    #         distances,
    #         embedder,
    #         snapshot_thresholds,
    #         degree_distribution,
    #         ["total"],
    #     )
    if "freq_in_degrees" in y_values:
        x_values["degrees_in"], y_values["freq_in_degrees"] = degree_distribution(
            network, "in"
        )
    if "freq_out_degrees" in y_values:
        x_values["degrees_out"], y_values["freq_out_degrees"] = degree_distribution(
            network, "out"
        )

    # if "freq_component_size_weak" in y_values:
    #     snapshot_thresholds = {
    #         "alibaba": [0.7, 0.72, 0.75],
    #         "tfidf": [0.4, 0.5, 0.6],
    #     }
    #     (
    #         x_values[METRICS["freq_component_size_weak"].x_axis_type],
    #         y_values["freq_component_size_weak"],
    #     ) = analyze_over_threshold_snapshots(
    #         data,
    #         distances,
    #         embedder,
    #         snapshot_thresholds,
    #         size_distribution_of_weak_components,
    #         [],
    #     )

    if "degree_dist_prob" in y_values:
        graph_data = transfrom_data.transform(
            data,
            distances,
            {"threshold": 0.85} if embedder == "alibaba" else {"threshold": 0.29},
        )
        network = construct_network(graph_data)
        (
            x_values[METRICS["degree_dist_prob"].x_axis_type],
            y_values["degree_dist_prob"],
        ) = compute_degree_distribution_probability(network)

    # if "degree_dist_prob" in y_values:
    #     snapshot_thresholds = {
    #         "alibaba": [0.7, 0.8, 0.9],
    #         "tfidf": [0.4, 0.5, 0.6],
    #     }
    #     snapshot_thresholds = {
    #         "alibaba": [0.85],
    #         "tfidf": [0.85],
    #     }
    #     (
    #         x_values[METRICS["degree_dist_prob"].x_axis_type],
    #         y_values["degree_dist_prob"],
    #     ) = analyze_over_threshold_snapshots(
    #         data,
    #         distances,
    #         embedder,
    #         snapshot_thresholds,
    #         compute_dyyegree_distribution_probability,
    #         [],
    #     )

    return x_values, y_values


def print_conf_mtx(data, embedder, dataset):
    new_data = []
    for d in data:
        if not d.embedding:
            continue
        new_data.append(d)
    data = new_data
    if embedder == "alibaba":
        # Alibaba
        embeddings = pd.DataFrame([d.embedding for d in data])
        distances = cosine.cluster(embeddings)
    elif embedder == "tfidf":
        # TF-IDF
        embeddings = tfidf.embed(data)
        distances = cosine.cluster(embeddings)
    elif embedder == "random":
        distances = random_model.embed(data)

    th = 0.85 if embedder == "alibaba" else 0.29
    graph_data = transfrom_data.transform(
        data,
        distances,
        {"threshold": th},
    )
    network = construct_network(graph_data)

    res = compute_confusion_matrix(network, graph_data)

    print("*" * 80)
    print(f"Confusion matrix for {dataset} using {embedder} @ ε={th}")
    print(f"""{res["TP"]}\t{res["FP"]}
{res["FN"]}\t{res["TN"]}""")
    print("*" * 80)


if __name__ == "__main__":
    assert len(sys.argv) > 1, "Dataset needed"
    dataset_name = sys.argv[1]
    DATASET_NAME = dataset_name
    dataset_path = pathlib.Path(dataset_name)

    thresholds = THRESHOLDS

    data = load_data.load(dataset_path)

    n_stories = len(Counter([art.story_id for art in data]))
    avg_arts_per_story = np.average(
        list(Counter([art.story_id for art in data]).values())
    )
    pub_times = sorted([art.published_time for art in data])
    eng_n = [art.language for art in data].count("english")
    print(f"""Dataset {dataset_name} loaded
    Articles: {len(data)}
    Stories: {n_stories}
    Avg arts per story: {avg_arts_per_story}
    First article: {pub_times[0]}
    Last article: {pub_times[-1]}
    English articles: {eng_n}
""")
    debug_asserts = True

    for embedder in EMBEDDERS:
        print(
            "-" * 80,
            f"\nCreating analysis for {dataset_name} using {embedder}\nTarget metrics:\n{'\n'.join([f'{m}' for m in METRICS])}\n",
        )
        print_conf_mtx(data, embedder, dataset_name)

        x_values, y_values = compute_xy_values(data, thresholds, embedder)

        for result_name in COMPUTE:
            save_result(
                {
                    "x": x_values[METRICS[result_name].x_axis_type],
                    "y": y_values[METRICS[result_name].y_axis_type],
                },
                dataset_name,
                embedder,
                result_name,
            )
