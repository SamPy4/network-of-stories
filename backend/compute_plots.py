import pathlib
import json
import matplotlib.pyplot as plt
import numpy as np


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
}

HIGLIGHTS = {
    "tfidf": {
        "x": {
            "f1": [0.85],
            "maximum_betweenness_centrality": [],
        },
        "y": {
            "maximum_betweenness_centrality": [],
        },
    },
    "alibaba": {
        "x": {
            "f1": [],
            "maximum_betweenness_centrality": [],
        },
        "y": {
            "f1": [],
            "maximum_betweenness_centrality": [],
        },
    },
    "random": {"x": {}, "y": {}},
}

ANNOT_PARAMS = {
    "tfidf": {
        "maximum_betweenness_centrality": {
            "offset": (15, -10),
            "rotation": 0,
            "replace_right": True,
        },
        "f1": {},
    },
    "alibaba": {
        "f1": {},
        "degree_dist_prob": {},
        "maximum_betweenness_centrality": {"offset": (15, -5), "replace_left": True},
    },
}

PLOT_ARGS = {
    "tfidf": {
        "degree_dist_prob": {},
        "maximum_betweenness_centrality": {},
    },
    "alibaba": {
        "freq_total_degrees": {"skip_first_n": 3},
        "f1": {},
        "maximum_betweenness_centrality": {},
    },
    "random": {},
}

MEDIA_FOLDER = "analysis_media"


def load_data(dataset, embedder, score):
    res_path = pathlib.Path(f"./analysis_results/{dataset}/{embedder}")
    if not res_path.exists():
        print(f"DATA FILE '{res_path}/{score}' NOT FOUND! Exiting...")
        exit(1)

    score_path = res_path.as_posix() + f"/{score}"

    with open(score_path, "r") as f:
        result = json.load(f)

    print("Result loaded:")
    print(result)
    return result["x"], result["y"]


def plot_xy(
    x_values,
    y_values,
    dataset_name: str,
    embedder: str = "alibaba",
    score: str = "f1",
    show: bool = False,
):
    embedder_names = {"alibaba": "Alibaba GTE", "tfidf": "TF-IDF", "random": "Random"}
    plt.figure(figsize=(8, 5))

    skip_first_n = 0
    if "skip_first_n" in PLOT_ARGS[embedder].get(score, []):
        skip_first_n = PLOT_ARGS[embedder][score]["skip_first_n"]

    if type(x_values) is dict:
        x_ticks = []
        y_ticks = []
        for key in x_values:
            x = x_values[key][skip_first_n:]
            y = y_values[key][skip_first_n:]

            x_ticks += x
            y_ticks += y

            plt.plot(x, y, marker="o", label=f"ε={str(key)}")
        if "datapoint_ticks" in PLOT_ARGS[embedder].get(score, {}):
            plt.xticks(list(set(x_ticks)), rotation=45)
            plt.yticks(list(set(y_ticks)))
        plt.legend(title="Series")
        # plt.yticks(np.arange(min_y, max_y+1, 1))
    else:
        if "bar" in PLOT_ARGS[embedder].get(score, {}):
            plt.bar(x_values[skip_first_n:], y_values[skip_first_n])
        else:
            if "datapoint_ticks" in PLOT_ARGS[embedder].get(score, {}):
                plt.xticks(x_values, rotation=45)
                plt.yticks(y_values)
            plt.plot(x_values, y_values, marker="o")

    highlight_x_ticks = (
        HIGLIGHTS[embedder]["x"][score] if score in HIGLIGHTS[embedder]["x"] else []
    )
    highlight_y_ticks = (
        HIGLIGHTS[embedder]["y"][score] if score in HIGLIGHTS[embedder]["y"] else []
    )
    for xtick in highlight_x_ticks:
        plt.axvline(x=xtick, linestyle="--", color="red")

    if HIGLIGHTS[embedder]["x"].get(score, None) == []:
        xtick = x_values[y_values.index(max(y_values))]
        plt.axvline(x=xtick, linestyle="--")
        ticks = list(plt.xticks()[0])
        ticks.append(xtick)
        s = sorted(ticks)
        if ANNOT_PARAMS[embedder][score].get("replace_right", False):
            s.pop(s.index(xtick) + 1)
        if ANNOT_PARAMS[embedder][score].get("replace_left", False):
            s.pop(s.index(xtick) - 1)
        plt.xticks(s, rotation=ANNOT_PARAMS[embedder][score].get("rotation", 0))

    if HIGLIGHTS[embedder]["y"].get(score, {}) == []:
        yval = max(y_values)
        xval = x_values[y_values.index(yval)]
        plt.annotate(
            f"y = {round(yval, 3)}",
            (xval, yval),  # point location
            textcoords="offset points",
            xytext=ANNOT_PARAMS[embedder][score].get(
                "offset", (10, 10)
            ),  # textbox offset
            ha="left",
            bbox=dict(boxstyle="round", alpha=0.3),
            arrowprops=dict(arrowstyle="->"),
        )

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


def heatmap():
    res_path = pathlib.Path(
        "./analysis_results/combined_ground_news/alibaba/in-out-degree_matrix"
    )
    with open(res_path, "r") as f:
        values = json.load(f)

    values = values["values"]
    values = np.array(values)

    plt.figure(figsize=(6, 5))

    # Heatmap
    plt.imshow(values, origin="lower", aspect="auto")

    # Color bar
    plt.colorbar(label="Number of nodes")

    # Axis labels
    plt.xlabel("Out-degree j")
    plt.ylabel("In-degree i")

    # Optional title
    plt.title("In/Out Degree Heatmap")

    # Tick labels
    plt.xticks(range(values.shape[1]))
    plt.yticks(range(values.shape[0]))

    plt.show()


def true_origins_plot():

    dataset_name = "combined_ground_news"
    # dataset_name = "combined_ground_news2"
    data = load_data(dataset_name, "alibaba", "true_origins")
    data1 = load_data(dataset_name, "tfidf", "true_origins")

    plt.figure(figsize=(8, 5))

    plt.grid(True)
    plt.title(f"Number of true origins found in {dataset_name}")
    plt.xlabel("Threshold (ε)")
    plt.ylabel("Number of true origins found")
    plt.plot(data[0], data[1], marker="o", label="method=Alibaba GTE")
    plt.plot(data1[0], data1[1], marker="o", label="method=TF-IDF")
    plt.axvline(x=0.78, linestyle="--", color="grey")
    plt.axvline(x=0.32, linestyle="--", color="grey")
    plt.legend(title="Series")

    plt.show()
    plt.savefig(f"./{MEDIA_FOLDER}/{dataset_name}_true_origins.svg")


def weak_components_in_datasets():
    embedder_names = {"alibaba": "Alibaba GTE", "tfidf": "TF-IDF"}
    embedder = "tfidf"

    dataset_names = [
        "combined_ground_news",
        "combined_ground_news2",
        "combined_disaster_and_accident",
    ]
    data = {
        set_name: load_data(set_name, embedder, "weak_components")
        for set_name in dataset_names
    }

    plt.figure(figsize=(8, 5))

    plt.grid(True)
    plt.title(f"{embedder_names[embedder]}: Number of weak components")
    plt.xlabel("Threshold (ε)")
    plt.ylabel("Number of weak components")

    for dataset in dataset_names:
        plt.plot(
            data[dataset][0], data[dataset][1], marker="o", label=f"dataset={dataset}"
        )
    plt.axvline(x=0.29, linestyle="--", color="grey")
    plt.axvline(x=0.32, linestyle="--", color="grey")
    plt.legend(title="Series")

    # plt.show()
    plt.savefig(
        f"./{MEDIA_FOLDER}/{[set_name for set_name in dataset_names]}_{embedder}_weak_components.svg"
    )


def maximum_weak_component_in_datasets():
    embedder_names = {"alibaba": "Alibaba GTE", "tfidf": "TF-IDF"}
    embedder = "tfidf"

    dataset_names = [
        "combined_ground_news",
        "combined_ground_news2",
        "combined_disaster_and_accident",
    ]
    data = {
        set_name: load_data(set_name, embedder, "maximum_component")
        for set_name in dataset_names
    }

    plt.figure(figsize=(8, 5))

    plt.grid(True)
    plt.title(f"{embedder_names[embedder]}: Size of the largest component")
    plt.xlabel("Threshold (ε)")
    plt.ylabel("Size of the component")

    for dataset in dataset_names:
        plt.plot(
            data[dataset][0], data[dataset][1], marker="o", label=f"dataset={dataset}"
        )
    # plt.axvline(x=0.78, linestyle="--", color="grey")
    # plt.axvline(x=0.32, linestyle="--", color="grey")
    plt.legend(title="Series")

    plt.show()
    plt.savefig(
        f"./{MEDIA_FOLDER}/{[set_name for set_name in dataset_names]}_{embedder}_maximum_component.svg"
    )


if __name__ == "__main__":
    # maximum_weak_component_in_datasets()
    # weak_components_in_datasets()
    true_origins_plot()
    exit()
    x1, y1 = load_data("combined_ground_news", "tfidf", "precision")
    x2, y2 = load_data("combined_ground_news", "tfidf", "recall")
    plot_xy(y2, y1, "combined_ground_news", "tfidf", "precision", show=True)
    exit()
    for dataset_name in [
        "combined_ground_news",
        "combined_ground_news2",
        "combined_disaster_and_accident",
    ]:
        for embedder in ["tfidf", "alibaba", "random"]:
            for score_name in COMPUTE:
                print("Loading and plotting", score_name)
                x, y = load_data(dataset_name, embedder, score_name)
                plot_xy(x, y, dataset_name, embedder, score_name, show=True)
