import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build_ultra_acwr_dashboard(summary_tsv_path: str) -> go.Figure:
    """
    Ultra ACWR dashboard with:
    - Weekly stacked load (top)
    - ACWR (bottom)

    Fixes:
    - Stable EWMA initialization
    - Proper ACWR scaling (no flatline)
    """

    if not Path(summary_tsv_path).exists():
        raise FileNotFoundError(f"{summary_tsv_path} not found")

    # -----------------------------
    # Load & prep
    # -----------------------------
    df = pd.read_csv(summary_tsv_path, sep="\t")
    df["date"] = pd.to_datetime(df["date"])

    df["sub_sport"] = df["sub_sport"].fillna("generic")
    df["avg_hr"] = df["avg_hr"].fillna(100)

    df["load_score"] = (df["duration_min"] * df["avg_hr"]) / 100
    df["activity_key"] = df["sport"].astype(str) + " | " + df["sub_sport"].astype(str)

    # -----------------------------
    # Daily pivot (same as fosters)
    # -----------------------------
    daily_pivot = (
        df.pivot_table(
            index="date",
            columns="activity_key",
            values="load_score",
            aggfunc="sum",
        )
        .resample("D")
        .sum()
        .fillna(0)
    )

    total_daily_load = daily_pivot.sum(axis=1)

    # -----------------------------
    # EWMA (FIXED)
    # -----------------------------
    acute = total_daily_load.ewm(span=7, adjust=False).mean()
    chronic = total_daily_load.ewm(span=56, adjust=False).mean()

    # Avoid divide-by-zero + early instability
    chronic_safe = chronic.replace(0, pd.NA)
    acwr = (acute / chronic_safe).fillna(method="bfill")

    # -----------------------------
    # Weekly stacked bars (same logic)
    # -----------------------------
    weekly_pivot = daily_pivot.resample("W").sum()

    counts = df["activity_key"].value_counts()
    weekly_pivot = weekly_pivot[counts.index.tolist()]

    # -----------------------------
    # Build figure
    # -----------------------------
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.6, 0.4],
    )

    # -----------------------------
    # TOP: Weekly stacked load
    # -----------------------------
    for col in weekly_pivot.columns:
        fig.add_trace(
            go.Bar(
                x=weekly_pivot.index,
                y=weekly_pivot[col],
                name=f"{col} (n={counts[col]})",
            ),
            row=1,
            col=1,
        )

    # -----------------------------
    # BOTTOM: ACWR
    # -----------------------------
    fig.add_trace(
        go.Scatter(
            x=acwr.index,
            y=acwr,
            name="ACWR (7:56)",
            line=dict(color="firebrick", width=3),
        ),
        row=2,
        col=1,
    )

    # Target zone (green band)
    fig.add_hrect(
        y0=0.8,
        y1=1.3,
        fillcolor="green",
        opacity=0.15,
        line_width=0,
        annotation_text="Target Zone",
        row=2,
        col=1,
    )

    # Overreach line
    fig.add_hline(
        y=1.5,
        line_dash="dash",
        line_color="darkorange",
        annotation_text="Overreach (1.5)",
        row=2,
        col=1,
    )

    # -----------------------------
    # Layout
    # -----------------------------
    fig.update_layout(
        title="Ultra Training Load & ACWR (7:56 EWMA)",
        barmode="stack",
        height=800,
        legend=dict(orientation="h"),
    )

    fig.update_yaxes(title_text="Weekly Load (TRIMP)", row=1, col=1)
    fig.update_yaxes(title_text="ACWR", row=2, col=1, range=[0, 3])

    return fig