"""Render evidence-bound quantitative charts from visual_tasks.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def render_chart(task, style, output_dir: Path):
    chart = task["chart"]
    categories = chart["categories"]
    series = chart["series"]
    colors = style["colors"]
    palette = [colors["primary"], colors.get("accent", "#D97706"), "#6B7280", "#2A9D8F", "#E76F51"]
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [style["fonts"]["body"], "Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "legend.fontsize": 8.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=180)
    chart_type = chart["type"]
    x = np.arange(len(categories))

    if chart_type == "grouped_bar":
        width = 0.72 / len(series)
        for i, item in enumerate(series):
            offset = (i - (len(series) - 1) / 2) * width
            bars = ax.bar(x + offset, item["values"], width * 0.9, label=item["name"],
                          color=palette[i % len(palette)], edgecolor="white", linewidth=0.6)
            for bar, value in zip(bars, item["values"]):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:g}",
                        ha="center", va="bottom", fontsize=8, color=colors["text"])
        ax.set_xticks(x, categories)
    elif chart_type == "horizontal_bar":
        values = series[0]["values"]
        bars = ax.barh(x, values, color=[palette[i % len(palette)] for i in range(len(values))])
        ax.set_yticks(x, categories)
        ax.invert_yaxis()
        for bar, value in zip(bars, values):
            ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {value:g}", va="center", fontsize=8)
    elif chart_type == "line":
        for i, item in enumerate(series):
            ax.plot(x, item["values"], marker="o", linewidth=2, label=item["name"],
                    color=palette[i % len(palette)])
            for x_value, value in zip(x, item["values"]):
                ax.annotate(f"{value:g}", (x_value, value), xytext=(0, 7),
                            textcoords="offset points", ha="center", fontsize=8,
                            color=colors["text"])
        ax.set_xticks(x, categories)
    else:
        raise ValueError(f"unsupported chart type: {chart_type}")

    ax.set_title(chart.get("title", ""), loc="left", fontweight="bold", color=colors["text"])
    if chart_type == "horizontal_bar":
        ax.set_xlabel(chart.get("y_label", ""))
    else:
        ax.set_ylabel(chart.get("y_label", ""))
    if chart.get("y_min") is not None or chart.get("y_max") is not None:
        ax.set_ylim(chart.get("y_min"), chart.get("y_max"))
    ax.grid(axis="y", alpha=0.16, linewidth=0.7)
    if len(series) > 1:
        ax.legend(frameon=False, ncol=min(3, len(series)), loc="upper left")
    fig.tight_layout()
    target = output_dir / task["output"]
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=220, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)
    with Image.open(target) as image:
        clean = image.convert("RGB")
        clean.save(target, "PNG", optimize=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--visual-system", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    style = json.loads(Path(args.visual_system).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    rendered = []
    for task in tasks.get("tasks", []):
        if task.get("kind") == "matplotlib_chart":
            rendered.append(str(render_chart(task, style, output_dir)))
    print(json.dumps({"rendered": rendered}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
