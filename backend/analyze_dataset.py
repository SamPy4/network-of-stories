from embeddings import tfidf, alibaba
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
import matplotlib.pyplot as plt

MEDIA_FOLDER = "analysis_media"


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
}

COMPUTE = {
    "edges",
    "weak_components",
    # "strong_components",
    # "f1",  # story id
    # "recall",  # story id
    # "precision",  # story id
    # "freq_total_degrees",
    # "freq_in_degrees",
    # "freq_out_degrees",
    # "freq_component_size_weak",
    # "degree_dist_prob",
    "maximum_component",
    # "maximum_degree",
    # "maximum_betweenness_centrality",
    # "average_clustering",
    # "average_path_length", # Has to be strongly connected grapn
}
EMBEDDERS = ["tfidf", "alibaba"]
EMBEDDERS = ["alibaba"]
DATASET_NAME = ""

THRESHOLDS = [i / 100 for i in range(40, 100, 1)]

HIGLIGHTS = {
    "tfidf": {"x": {"f1": [0.85], "weak_components": [0.85]}, "y": {}},
    "alibaba": {
        "x": {
            "f1": [0.89],
            "weak_components": [0.85],
            "degree_dist_prob": [8],
            "maximum_component": [0.89],
        },
        "y": {"f1": []},
    },
}

PLOT_ARGS = {
    "tfidf": {"degree_dist_prob": {"datapoint_ticks": 42}},
    "alibaba": {
        "freq_total_degrees": {"skip_first_n": 3},
        "maximum_component": {"datapoint_ticks": 42},
        "f1": {"datapoint_ticks": 42},
    },
}

# Filter not selected metrics out
for not_computed in set(METRICS.keys()).difference(COMPUTE):
    METRICS.pop(not_computed)


def plot_xy(
    x_values,
    y_values,
    dataset_name: str,
    embedder: str = "alibaba",
    score: str = "f1",
    x_value_name: str = "threshold",
    show: bool = False,
):
    embedder_names = {"alibaba": "Alibaba GTE", "tfidf": "TF-IDF"}
    plt.figure(figsize=(8, 5))

    skip_first_n = 0
    if "skip_first_n" in PLOT_ARGS[embedder].get(y_type, []):
        skip_first_n = PLOT_ARGS[embedder][y_type]["skip_first_n"]

    if type(x_values) is dict:
        x_ticks = []
        y_ticks = []
        for key in x_values:
            x = x_values[key][skip_first_n:]
            y = y_values[key][skip_first_n:]

            x_ticks += x
            y_ticks += y

            plt.plot(x, y, marker="o", label=f"ε={str(key)}")
        if "datapoint_ticks" in PLOT_ARGS[embedder].get(y_type, {}):
            plt.xticks(list(set(x_ticks)), rotation=45)
            plt.yticks(list(set(y_ticks)))
        plt.legend(title="Series")
        # plt.yticks(np.arange(min_y, max_y+1, 1))
    else:
        if "bar" in PLOT_ARGS[embedder].get(y_type, {}):
            plt.bar(x_values[skip_first_n:], y_values[skip_first_n])
        else:
            if "datapoint_ticks" in PLOT_ARGS[embedder].get(y_type, {}):
                plt.xticks(x_values, rotation=45)
                plt.yticks(y_values)
            plt.plot(x_values, y_values, marker="o")

    highlight_x_ticks = (
        HIGLIGHTS[embedder]["x"][y_type] if y_type in HIGLIGHTS[embedder]["x"] else []
    )
    print(HIGLIGHTS[embedder]["x"])
    print(highlight_x_ticks)
    highlight_y_ticks = (
        HIGLIGHTS[embedder]["y"][y_type] if y_type in HIGLIGHTS[embedder]["y"] else []
    )
    for xtick in highlight_x_ticks:
        plt.axvline(x=xtick, linestyle="--", color="red")
    for ytick in highlight_y_ticks:
        plt.axhline(y=ytick, linestyle="--", color="red")

    plt.xlabel(METRICS[score].x_axis_title)
    plt.ylabel(METRICS[score].y_axis_title)
    plt.title(
        f"{dataset_name} | {embedder_names[embedder]}:\n{METRICS[score].x_axis_title} vs. {METRICS[score].y_axis_title}"
    )

    plt.grid(True)
    highlight_text = (
        (f"_xhigh{highlight_x_ticks}" if highlight_x_ticks else "")
        + f"_yhigh{highlight_y_ticks}"
        if highlight_y_ticks
        else ""
    )
    plt.savefig(
        f"./{MEDIA_FOLDER}/{dataset_name}_{embedder}_{score}{highlight_text}.png"
    )
    if show:
        plt.show()


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


def analyze_over_threshold_snapshots(
    data,
    distances,
    embedder,
    snapshots,
    compute_function,
    args,
):
    x_res = {}
    x_res = {th: [] for th in snapshots[embedder]}
    y_res = {th: [] for th in snapshots[embedder]}
    for th in snapshots[embedder]:
        cache_path = pathlib.Path(f"./graph_cache/{DATASET_NAME}/{embedder}/{th}.json")
        if cache_path.exists():
            with open(cache_path, "r") as f:
                graph_data = json.load(f)
        else:
            graph_data = transfrom_data.transform(data, distances, {"threshold": th})
            with open(cache_path, "w") as f:
                json.dump(graph_data, f)

        network = construct_network(graph_data)
        (
            x_res[th],
            y_res[th],
        ) = compute_function(network, *args)

    return x_res, y_res


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
    else:
        # TF-IDF
        embeddings = tfidf.embed(data)
        distances = cosine.cluster(embeddings)

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
            graph_data = transfrom_data.transform(data, distances, {"threshold": th})
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
                    max([bc for bc in nx.betweenness_centrality(network).values()])
                )
            if "average_clustering" in y_values:
                y_values["average_clustering"].append(nx.average_clustering(network))
            if "average_path_length" in y_values:
                y_values["average_path_length"].append(
                    nx.average_shortest_path_length(network)
                )

    if "freq_total_degrees" in y_values:
        snapshot_thresholds = {
            "alibaba": [0.80, 0.82, 0.85],
            "tfidf": [0.4, 0.5, 0.6],
        }
        (
            x_values[METRICS["freq_total_degrees"].x_axis_type],
            y_values["freq_total_degrees"],
        ) = analyze_over_threshold_snapshots(
            data,
            distances,
            embedder,
            snapshot_thresholds,
            degree_distribution,
            ["total"],
        )
    if "freq_in_degrees" in y_values:
        x_values["degrees_in"], y_values["freq_in_degrees"] = degree_distribution(
            network, "in"
        )
    if "freq_out_degrees" in y_values:
        x_values["degrees_out"], y_values["freq_out_degrees"] = degree_distribution(
            network, "out"
        )

    if "freq_component_size_weak" in y_values:
        snapshot_thresholds = {
            "alibaba": [0.7, 0.72, 0.75],
            "tfidf": [0.4, 0.5, 0.6],
        }
        (
            x_values[METRICS["freq_component_size_weak"].x_axis_type],
            y_values["freq_component_size_weak"],
        ) = analyze_over_threshold_snapshots(
            data,
            distances,
            embedder,
            snapshot_thresholds,
            size_distribution_of_weak_components,
            [],
        )

    if "degree_dist_prob" in y_values:
        snapshot_thresholds = {
            "alibaba": [0.7, 0.8, 0.9],
            "tfidf": [0.4, 0.5, 0.6],
        }
        snapshot_thresholds = {
            "alibaba": [0.85],
            "tfidf": [0.85],
        }
        (
            x_values[METRICS["degree_dist_prob"].x_axis_type],
            y_values["degree_dist_prob"],
        ) = analyze_over_threshold_snapshots(
            data,
            distances,
            embedder,
            snapshot_thresholds,
            compute_degree_distribution_probability,
            [],
        )

    return x_values, y_values


def plot_datasets_in_one(embedder, thresholds, score_type):
    datasets = {
        name: load_data.load(path)
        for path, name in zip([pathlib.Path(arg) for arg in sys.argv[1:]], sys.argv[1:])
    }
    new_data = {name: [] for name in sys.argv[1:]}
    dists = {name: [] for name in sys.argv[1:]}
    for name in datasets:
        data = datasets[name]
        for d in data:
            if not d.embedding:
                continue
            new_data[name].append(d)
        if embedder == "alibaba":
            # Alibaba
            embeddings = pd.DataFrame([d.embedding for d in new_data[name]])
            dists[name] = cosine.cluster(embeddings)
        else:
            # TF-IDF
            embeddings = tfidf.embed(new_data[name])
            dists[name] = cosine.cluster(embeddings)
    scores = {name: [] for name in sys.argv[1:]}
    for i, th in enumerate(thresholds):
        print(
            f"Progress... {i + 1} / {len(thresholds)}\t{embedder}",
            " " * 80,
            end="\r",
        )
        for dataset_name in dists.keys():
            if score_type == "test":
                scores[dataset_name].append(
                    0.5
                    * (
                        -2.5 * (th + len(dataset_name) / 50) ** 2
                        + 2.5 * (th + len(dataset_name) / 50)
                        + 0.5
                    )
                    + len(dataset_name) / 10
                )
                continue

            cache_path = pathlib.Path(
                f"./graph_cache/{dataset_name}/{embedder}/{th}.json"
            )
            if cache_path.exists():
                with open(cache_path, "r") as f:
                    graph_data = json.load(f)

            else:
                graph_data = transfrom_data.transform(
                    datasets[dataset_name], dists[dataset_name], {"threshold": th}
                )
                with open(cache_path, "w") as f:
                    json.dump(graph_data, f)

            network = construct_network(graph_data)
            if score_type == "f1":
                scores[dataset_name].append(
                    compute_f1(compute_confusion_matrix(network, graph_data))
                )
            elif score_type == "recall":
                scores[dataset_name].append(
                    compute_recall(compute_confusion_matrix(network, graph_data))
                )
            elif score_type == "precision":
                scores[dataset_name].append(
                    compute_precision(compute_confusion_matrix(network, graph_data))
                )
            elif score_type == "edges":
                scores[dataset_name].append(network.number_of_edges())
            elif score_type == "weak_components":
                scores[dataset_name].append(count_weak_components(network, min_size=2))
            elif score_type == "maximum_component":
                scores[dataset_name].append(
                    max([len(com) for com in nx.weakly_connected_components(network)])
                )

    plt.figure(figsize=(8, 7))
    for dataset in scores:
        # x = x_values[key][skip_first_n:]
        # y = y_values[key][skip_first_n:]

        print(
            f"Plotting {dataset} with x = {len(thresholds)}, y = {len(scores[dataset])}"
        )
        plt.plot(
            thresholds, scores[dataset], marker="o", label=f"dataset={str(dataset)}"
        )
    embedder_names = {"alibaba": "Alibaba GTE", "tfidf": "TF-IDF"}
    plt.title(
        f"{embedder_names[embedder]}: {METRICS[score_type].y_axis_title} between datasets"
    )
    plt.xlabel(METRICS[score_type].x_axis_title)
    plt.ylabel(METRICS[score_type].y_axis_title)

    colors = ["blue", "orange", "green"]
    annot_shown = {"f1": True, "edges": False}
    annot_offset = {}
    annot_offset["f1"] = [(20, 5), (-75, -10)]
    annot_offset["edges"] = [(10, 10), (-75, -10), (10, 10)]
    if annot_shown[score_type]:
        for i, dataset in enumerate(scores):
            yval = max(scores[dataset])
            xval = thresholds[scores[dataset].index(yval)]
            plt.axvline(x=xval, linestyle="--", color=colors[i])

            ticks = list(plt.xticks()[0])
            ticks.append(xval)
            s = sorted(ticks)
            if i == 0:
                s.pop(s.index(xval) - 1)
            plt.xticks(s, rotation=45)
        plt.annotate(
            f"y = {round(yval, 3)}",
            (xval, yval),  # point location
            textcoords="offset points",
            xytext=annot_offset[score_type][i],  # textbox offset
            ha="left",
            bbox=dict(boxstyle="round", alpha=0.3, facecolor=colors[i]),
            arrowprops=dict(arrowstyle="->"),
        )

        # if i == 0:
        #     ticks = list(plt.yticks()[0])
        #     ticks.append(yval)
        #     s = sorted(ticks)
        #     # s.pop(s.index(yval) - 1)
        #     plt.yticks(s)

    if annot_shown[score_type]:
        ticks = list(plt.xticks()[0])
        s = sorted(ticks)
        s.pop(0)
        s.pop(-1)
        plt.xticks(s, rotation=45)

    plt.legend(title="Series")
    plt.grid(True)
    plt.savefig(
        f"./{MEDIA_FOLDER}/{[n for n in datasets.keys()]}_{embedder}_double-{score_type}.svg"
    )
    plt.show()


if __name__ == "__main__":
    assert len(sys.argv) > 1, "Dataset needed"
    dataset_name = sys.argv[1]
    DATASET_NAME = dataset_name
    dataset_path = pathlib.Path(dataset_name)

    thresholds = THRESHOLDS

    if len(sys.argv) != 2:
        # Plot different datasets in the same plot
        embedder = "alibaba"
        thresholds = [i / 100 for i in range(0, 100, 1)]
        score_type = "weak_components"

        plot_datasets_in_one(embedder, thresholds, score_type)
        exit()

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
    exit()
    debug_asserts = True

    for embedder in EMBEDDERS:
        print(
            "-" * 80,
            f"\nCreating analysis for {dataset_name} using {embedder}\nTarget metrics:\n{'\n'.join([f'{m}' for m in METRICS])}\n",
        )

        x_values, y_values = compute_xy_values(data, thresholds, embedder)
        print()
        for metric in METRICS:
            x_type = METRICS[metric].x_axis_type
            x_name = METRICS[metric].x_axis_title
            y_type = METRICS[metric].y_axis_type
            y_name = METRICS[metric].y_axis_title
            assert not debug_asserts or len(x_values[x_type]) != 0, (
                f"X-axis should not be empty for {x_type}"
            )
            if len(x_values[x_type]) == 0 or len(x_values[x_type]) != len(
                y_values[y_type]
            ):
                print(
                    metric,
                    "\t" * (int(-len(metric) / 6 + 3)),
                    "\033[31m[FAIL]\033[0m",
                    sep="",
                )
                continue
            try:
                plot_xy(
                    x_values[x_type],
                    y_values[y_type],
                    dataset_name,
                    embedder,
                    y_type,
                    x_type,
                    False,
                )
            except Exception:
                print(
                    metric,
                    "\t" * (int(-len(metric) / 6 + 3)),
                    "\033[31m[FAIL]\033[0m",
                    sep="",
                )
                if debug_asserts:
                    raise
                continue
            print(
                metric,
                "\t" * (int(-len(metric) / 6 + 5)),
                "\033[32m[SUCCESS]\033[0m",
                sep="",
            )

        print()

    print("Done")
