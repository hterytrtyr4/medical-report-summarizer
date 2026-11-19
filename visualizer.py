"""
visualizer.py - Interactive Plotly Visualizations for Medical Laboratory Values
Renders patient-friendly range gauges and health status distribution charts.
"""
from typing import Dict, List, Any
import plotly.graph_objects as go


def create_health_donut_chart(parameters: List[Dict[str, Any]]) -> go.Figure:
    """
    Renders an interactive donut chart showing proportion of Normal, High, and Low parameters.
    """
    normal = sum(1 for p in parameters if p["status"] == "Normal")
    high = sum(1 for p in parameters if p["status"] == "High")
    low = sum(1 for p in parameters if p["status"] == "Low")

    labels = ["Normal (सामान्य)", "High (अधिक)", "Low (कम)"]
    values = [normal, high, low]
    colors = ["#27ae60", "#e74c3c", "#f39c12"]

    # Filter out zeros
    filtered_labels = [l for l, v in zip(labels, values) if v > 0]
    filtered_values = [v for v in values if v > 0]
    filtered_colors = [c for c, v in zip(colors, values) if v > 0]

    if not filtered_values:
        filtered_labels = ["No Parameters"]
        filtered_values = [1]
        filtered_colors = ["#95a5a6"]

    fig = go.Figure(data=[go.Pie(
        labels=filtered_labels,
        values=filtered_values,
        hole=0.6,
        marker=dict(colors=filtered_colors, line=dict(color="#ffffff", width=2)),
        textinfo="label+value",
        hoverinfo="label+percent"
    )])

    fig.update_layout(
        title=dict(text="<b>Test Status Overview (समग्र स्थिति)</b>", x=0.5, font=dict(size=16, color="#2c3e50")),
        showlegend=True,
        margin=dict(t=50, b=20, l=20, r=20),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def create_parameter_gauge(param: Dict[str, Any]) -> go.Figure:
    """
    Creates an intuitive indicator gauge chart for an individual laboratory test.
    Shows the safe green zone, lower bound, upper bound, and patient's value marker.
    """
    val = param["value"]
    min_ref = param["min_ref"]
    max_ref = param["max_ref"]
    unit = param["unit"]
    status = param["status"]

    # Determine scale bounds
    plot_min = max(0.0, min_ref * 0.4)
    plot_max = max_ref * 1.6 if max_ref > 0 else 100.0
    if val > plot_max:
        plot_max = val * 1.25

    bar_color = "#27ae60" if status == "Normal" else ("#e74c3c" if status == "High" else "#f39c12")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=val,
        number=dict(suffix=f" {unit}", font=dict(size=22, color="#2c3e50")),
        title=dict(text=f"<b>{param['name']}</b><br><span style='font-size:12px;color:#7f8c8d'>Normal: {min_ref} - {max_ref} {unit}</span>", font=dict(size=14)),
        delta=dict(
            reference=(min_ref + max_ref) / 2.0,
            increasing=dict(color="#e74c3c"),
            decreasing=dict(color="#f39c12")
        ),
        gauge=dict(
            axis=dict(range=[plot_min, plot_max], tickwidth=1, tickcolor="#95a5a6"),
            bar=dict(color=bar_color, thickness=0.3),
            bgcolor="white",
            borderwidth=1,
            bordercolor="#bdc3c7",
            steps=[
                dict(range=[plot_min, min_ref], color="rgba(243, 156, 18, 0.25)"),   # Low zone
                dict(range=[min_ref, max_ref], color="rgba(39, 174, 96, 0.35)"),    # Normal zone (Green)
                dict(range=[max_ref, plot_max], color="rgba(231, 76, 60, 0.25)")    # High zone
            ],
            threshold=dict(
                line=dict(color=bar_color, width=4),
                thickness=0.8,
                value=val
            )
        )
    ))

    fig.update_layout(
        height=220,
        margin=dict(t=50, b=20, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif")
    )
    return fig
