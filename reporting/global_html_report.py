from pathlib import Path
from analysis.fosters_dashboard import build_fosters_dashboard
from analysis.acwr_dashboard import build_ultra_acwr_dashboard
from analysis.long_run_vr import plot_longest_run_metric_interactive
from analysis.long_run_mechanics_hr import plot_long_run_mechanics_hr

BASE_DIR = Path(__file__).resolve().parents[1]  # repo/
OUT_DIR = BASE_DIR.parent / "out"               # sibling to repo/
WORKOUTS_DIR = BASE_DIR.parent / "workouts"    # sibling to repo/


def generate_training_report(
    summary_path: str | Path = None,
    output_html: str | Path = None,
):
    """
    Generates a multi-section HTML training report with:
    - Foster load dashboard
    - Ultra ACWR analysis
    """

    # -----------------------------
    # Resolve paths safely (NEW)
    # -----------------------------
    if summary_path is None:
        summary_path = OUT_DIR / "master_workout_summary.tsv"
    else:
        summary_path = Path(summary_path)

    if output_html is None:
        output_path = OUT_DIR / "training_report.html"
    else:
        output_path = Path(output_html)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build figures 
    fosters_fig = build_fosters_dashboard(summary_path)
    acwr_fig = build_ultra_acwr_dashboard(summary_path)
    vr_fig = plot_longest_run_metric_interactive(summary_path, "../out", metric="vertical_ratio")
    cadence_fig = plot_longest_run_metric_interactive(summary_path, "../out", metric="cadence")
    mech_hr_fig = plot_long_run_mechanics_hr(summary_path, "../out")

    # Keep working Plotly pattern
    fosters_html = fosters_fig.to_html(full_html=False, include_plotlyjs="cdn")
    acwr_html = acwr_fig.to_html(full_html=False, include_plotlyjs=False)
    vr_html = vr_fig.to_html(full_html=False, include_plotlyjs=False)
    cadence_html = cadence_fig.to_html(full_html=False, include_plotlyjs=False)
    mech_hr_html = mech_hr_fig.to_html(full_html=False, include_plotlyjs=False)

    # -----------------------------
    # Compose HTML
    # -----------------------------
    html = f"""
<html>
<head>
    <title>Ultra Endurance Training Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f8f9fa;
        }}
        h1, h2 {{
            color: #222;
        }}
        .section {{
            margin-bottom: 60px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        .explanation {{
            color: #555;
            max-width: 900px;
            line-height: 1.6;
        }}
        code {{
            background: #eee;
            padding: 2px 6px;
            border-radius: 4px;
        }}
    </style>
</head>

<body>

<h1>🏃 Ultra Endurance Training Report</h1>

<div class="section">
    <h2>How to Read This Report</h2>
    <div class="explanation">

        <p>
        This report evaluates endurance training using complementary perspectives on 
        load, structure, biomechanics, and physiological response.
        </p>

        <p>
        The analysis combines:
        </p>

        <ul>
            <li><b>Foster’s Strain</b> — training structure and consistency</li>
            <li><b>ACWR</b> — rate of change in training load</li>
            <li><b>Biomechanics</b> — running efficiency under fatigue</li>
        </ul>

        <p>
        Together, these provide a comprehensive view of how training is distributed, 
        how the body responds, and how performance evolves over longer durations.
        </p>

        <p><b>Training Load Definition:</b></p>

        <p>
        <code>Load = Duration (minutes) × Average Heart Rate / 100</code>
        </p>

        <p>
        This provides a simple proxy for internal physiological stress by combining 
        session duration and cardiovascular intensity.
        </p>

        <p><b>Exponentially Weighted Moving Average (EWMA):</b></p>

        <p>
        <code>EWMAₜ = α × Loadₜ + (1 − α) × EWMAₜ₋₁</code>
        </p>

        <p>
        EWMA places greater emphasis on recent training while retaining historical context. 
        Short windows reflect fatigue, while longer windows capture accumulated fitness.
        </p>

    </div>
</div>

<div class="section">
    <h2>1. Foster’s Strain (Load × Monotony)</h2>
    <div class="explanation">

        <p><b>Overview:</b></p>

        <p>
        Foster’s method evaluates both total training load and how consistently that load 
        is applied over time.
        </p>

        <p>
        <code>Monotony = Mean Daily Load / Std Dev Daily Load (7 days)</code><br>
        <code>Strain = Weekly Load × Monotony</code>
        </p>

        <p><b>Interpretation:</b></p>

        <ul>
            <li><b>High monotony (&gt;2.0)</b> → repetitive training with limited variation</li>
            <li><b>High strain</b> → high load combined with insufficient variability</li>
        </ul>

        <p><b>Context:</b></p>

        <p>
        Effective ultra-endurance training typically follows structured cycles:
        </p>

        <ul>
            <li>Gradual load progression during build phases</li>
            <li>Reduced load during taper periods</li>
            <li>Recovery blocks following peak efforts</li>
        </ul>

        <p>
        Foster’s Strain helps identify whether this structure is present by capturing 
        both load magnitude and variability.
        </p>

        <p><b>Strengths:</b></p>
        <ul>
            <li>Captures both volume and distribution of training</li>
            <li>Well suited to periodised endurance programmes</li>
        </ul>

        <p><b>Limitations:</b></p>
        <ul>
            <li>Less sensitive to isolated extreme sessions (e.g. race efforts)</li>
        </ul>

    </div>

    {fosters_html}

</div>

<div class="section">
    <h2>2. Acute:Chronic Workload Ratio (ACWR)</h2>
    <div class="explanation">

        <p><b>Overview:</b></p>

        <p>
        ACWR compares short-term load (fatigue) to long-term load (fitness):
        </p>

        <p>
        <code>Acute Load = EWMA(7 days)</code><br>
        <code>Chronic Load = EWMA(56 days)</code><br>
        <code>ACWR = Acute / Chronic</code>
        </p>

        <p><b>Interpretation:</b></p>

        <ul>
            <li><b>~1.0</b> → stable training load</li>
            <li><b>0.8 – 1.3</b> → typical adaptation range</li>
            <li><b>&gt;1.5</b> → rapid load increase (potential risk)</li>
        </ul>

        <p><b>Context:</b></p>

        <p>
        ACWR is highly sensitive to rapid changes in load. While effective at identifying 
        spikes, it can overreact during structured endurance training cycles:
        </p>

        <ul>
            <li>Taper periods reduce acute load</li>
            <li>Race efforts create sharp increases</li>
        </ul>

        <p>
        As a result, ACWR is most useful when interpreted alongside structural metrics 
        such as Foster’s Strain.
        </p>

        <p><b>Strengths:</b></p>
        <ul>
            <li>Simple and widely used</li>
            <li>Effective for detecting sudden load changes</li>
        </ul>

        <p><b>Limitations:</b></p>
        <ul>
            <li>Overly sensitive to taper-to-race transitions</li>
            <li>Less suited to long-cycle ultra training</li>
        </ul>

    </div>

    {acwr_html}

</div>

<div class="section">
    <h2>3. Long Run Efficiency: Vertical Ratio</h2>
    <div class="explanation">

        <p><b>Overview:</b></p>

        <p>
        Vertical Ratio (VR) measures running efficiency by comparing vertical movement 
        to forward progression:
        </p>

        <p>
        <code>Vertical Ratio = Vertical Oscillation / Step Length</code>
        </p>

        <p>
        Lower values indicate more efficient forward motion per unit of vertical movement.
        </p>

        <p><b>Interpretation:</b></p>

        <ul>
            <li><b>~6–8%</b> → efficient movement</li>
            <li><b>&gt;9–10%</b> → increased vertical motion, reduced efficiency</li>
        </ul>

        <p><b>Context:</b></p>

        <p>
        During long efforts, fatigue often leads to:
        </p>

        <ul>
            <li>Reduced stride length</li>
            <li>Increased vertical oscillation</li>
            <li>Higher energy cost per distance</li>
        </ul>

        <p>
        This chart compares the longest run to historical baseline behaviour to show 
        how efficiency changes under fatigue.
        </p>

    </div>

    {vr_html}

</div>

<div class="section">
    <h2>4. Long Run Dynamics: Cadence</h2>
    <div class="explanation">

        <p><b>Overview:</b></p>

        <p>
        Cadence represents stride frequency and is a key component of running mechanics:
        </p>

        <p>
        <code>Cadence = Steps per minute (spm)</code>
        </p>

        <p><b>Interpretation:</b></p>

        <ul>
            <li><b>Higher cadence (170–185 spm)</b> → shorter, more frequent steps</li>
            <li><b>Lower cadence</b> → longer ground contact, often associated with fatigue</li>
        </ul>

        <p><b>Context:</b></p>

        <p>
        Cadence typically decreases with fatigue, but is also influenced by terrain:
        </p>

        <ul>
            <li>Climbs → lower cadence</li>
            <li>Descents → higher cadence</li>
        </ul>

        <p>
        This chart highlights how stride dynamics evolve relative to baseline behaviour.
        </p>

    </div>

    {cadence_html}

</div>

<div class="section">
    <h2>5. Long Run Mechanics & Physiology</h2>
    <div class="explanation">

        <p><b>Overview:</b></p>

        <p>
        This chart integrates biomechanics, physiological response, and movement output 
        to provide a comprehensive view of performance during the longest run.
        </p>

        <p>
        The top panel shows <b>mechanics</b>, while the bottom panel shows 
        <b>physiological demand and resulting output</b>.
        </p>

        <p><b>Key relationships:</b></p>

        <ul>
            <li><b>VR ↑ + Cadence ↓</b> → reduced mechanical efficiency</li>
            <li><b>HR ↑ with stable mechanics</b> → increasing physiological strain</li>
            <li><b>HR ↓ with falling speed</b> → reduced output (slowing)</li>
        </ul>

        <p>
        Solid lines represent smoothed signals, while dashed lines indicate 
        longer-term trends.
        </p>

        <p>
        Shaded regions highlight periods of mechanical deterioration, where efficiency 
        declines due to fatigue or external factors.
        </p>

        <p>
        By combining mechanics, physiology, and output, this chart provides insight into 
        fatigue resistance and performance sustainability over extended durations.
        </p>

    </div>

    {mech_hr_html}

</div>

</body>
</html>
"""

    output_path.write_text(html)
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    generate_training_report("../out/master_workout_summary.tsv")