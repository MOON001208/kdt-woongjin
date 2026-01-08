from shiny import App, ui, render, reactive
import pandas as pd
from analysis import SubwayAnalyzer
import matplotlib.pyplot as plt
import faicons as fa

# Initialize analyzer
analyzer = SubwayAnalyzer()

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_action_button("refresh", "Refresh Data", icon=fa.icon_svg("arrows-rotate")),
        ui.input_slider("limit", "Max Records", 100, 5000, 1000),
        ui.hr(),
        ui.p("Last updated:"),
        ui.output_text("last_update_time"),
    ),
    ui.layout_columns(
        ui.value_box(
            "Active Trains (Unique)",
            ui.output_ui("total_trains"),
            showcase=fa.icon_svg("train"),
        ),
        ui.value_box(
            "System Avg Interval",
            ui.output_ui("avg_interval"),
            showcase=fa.icon_svg("clock"),
        ),
        ui.value_box(
            "Express Trains",
            ui.output_ui("express_count"),
            showcase=fa.icon_svg("bolt"),
        ),
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Interval Regularity by Line (Avg + Std Dev)"),
            ui.output_plot("interval_plot"),
        ),
        ui.card(
            ui.card_header("Delay Hotspots (Frequency)"),
            ui.output_data_frame("delay_table"),
        ),
    ),
    title="Subway Operations Monitor",
)

def server(input, output, session):
    
    @reactive.Calc
    def get_data():
        input.refresh() # Dependency
        limit = input.limit()
        # Invalidate manually or just rely on button
        return analyzer.fetch_data(limit=limit)

    @render.text
    def last_update_time():
        df = get_data()
        if df.empty: return "No Data"
        # Return current time because we just fetched
        return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    @render.ui
    def total_trains():
        df = get_data()
        if df.empty: return "0"
        return str(df['train_number'].nunique())

    @render.ui
    def avg_interval():
        df = get_data()
        if df.empty: return "N/A"
        stats = analyzer.analyze_interval_regularity(df)
        if stats is None or stats.empty: return "N/A"
        avg = stats['mean'].mean() 
        return f"{avg:.1f} min"

    @render.ui
    def express_count():
        df = get_data()
        if df.empty: return "0"
        counts = analyzer.analyze_express_interference(df)
        return str(counts.get('express_count', 0))

    @render.plot
    def interval_plot():
        df = get_data()
        if df.empty: return
        stats = analyzer.analyze_interval_regularity(df)
        if stats is None or stats.empty: return
        
        # Plot using matplotlib
        fig, ax = plt.subplots(figsize=(8, 4))
        lines = stats['line_name']
        means = stats['mean']
        stds = stats['std']
        
        ax.bar(lines, means, yerr=stds, capsize=5, color='skyblue', alpha=0.8)
        ax.set_ylabel('Interval (min)')
        ax.set_title('Average Interval with Regularity (Std Dev)')
        plt.tight_layout()
        return fig

    @render.data_frame
    def delay_table():
        df = get_data()
        if df.empty: return pd.DataFrame()
        hotspots = analyzer.analyze_delay_hotspots(df)
        return render.DataGrid(hotspots, selection_mode="none")

app = App(app_ui, server)
