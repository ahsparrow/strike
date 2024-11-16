"""
Bell striking statistics
"""

import asyncio
import csv
import io
import json
import os
from pathlib import Path

import httpx
import numpy as np
import toga
import toga_chart
from matplotlib.ticker import FuncFormatter
from toga.style.pack import Pack
from toga.validators import Integer, LengthBetween, Number
from websockets.asyncio.client import connect

from . import stats

# From www.simplifiedsciencepublishing.com
GRAY = "#c8c8c8"
GOLD = "#f0c571"
TEAL = "#59a89c"
BLUE = "#0b8aa2"
RED = "#e25759"
DARK_RED = "#9d2c00"
PURPLE = "#7e4794"
GREEN = "#36b700"

MIN_LINE_ROWS = 10
MAX_LINE_ROWS = 100


class Strike(toga.App):
    def startup(self):
        self.load_prefs()

        self.touch = 0
        self.rows = []
        self.score = None
        self.rms_errors = None
        self.faults = None

        self.ws_task = None

        # Line display parameters
        self.line_row = 0
        self.line_nrows = MIN_LINE_ROWS

        score = self.score_box()
        line = self.line_box()
        rms = self.rms_box()
        faults = self.faults_box()
        self.container = toga.OptionContainer(
            content=[
                ("Score", score),
                ("Line", line),
                ("Accuracy", rms),
                ("Striking", faults),
            ]
        )

        self.prefs_content = self.prefs_box()

        cmd_prefs = toga.Command(self.action_prefs, "Preferences", order=4, section=2)

        cmd_auto = toga.Command(self.action_auto, "Auto", order=1, section=1)
        cmd_prev = toga.Command(
            self.action_prev,
            "Prev",
            order=2,
            section=1,
            shortcut=toga.Key.MOD_1 + "p",
        )
        cmd_next = toga.Command(
            self.action_next,
            "Next",
            order=3,
            section=1,
            shortcut=toga.Key.MOD_1 + "n",
        )

        self.commands.add(cmd_auto, cmd_prev, cmd_next, cmd_prefs)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.container
        self.main_window.show()

    # Auto action
    def action_auto(self, widget):
        async def ws_recv():
            async with connect(f"ws://{self.server}/status") as websocket:
                while True:
                    msg = await websocket.recv()
                    print(msg)

                    if msg == "idle":
                        catalog = await self.get_catalog()
                        self.touch = len(catalog)

                        await self.update()

                    else:
                        self.clear()

        if self.ws_task is None or self.ws_task.cancelled():
            print("Starting WS task")
            self.ws_task = asyncio.create_task(ws_recv())

    # Previous action
    async def action_prev(self, widget):
        if self.ws_task is not None:
            self.ws_task.cancel()

        catalog = await self.get_catalog()
        if self.touch == 0 or self.touch > len(catalog):
            self.touch = 1
        elif self.touch != 1:
            self.touch -= 1

        await self.update()

    # Next action
    async def action_next(self, widget):
        if self.ws_task is not None:
            self.ws_task.cancel()

        catalog = await self.get_catalog()
        ntouches = len(catalog)
        if self.touch == 0 or self.touch >= (ntouches - 1):
            self.touch = len(catalog)
        else:
            self.touch += 1

        await self.update()

    # Preferences action
    def action_prefs(self, widget):
        self.main_window.content = self.prefs_content

    # Update results
    async def update(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{self.server}/log/{self.touch}")

        reader = csv.DictReader(io.StringIO(response.text))
        data = [
            {"bell": int(x["bell"]), "time": int(x["ticks_ms"]) / 1000} for x in reader
        ]

        nbells, rows = stats.whole_rows(data, self.include_rounds)
        if len(rows) < 10:
            return

        self.rows = rows
        stats.alpha_beta(nbells, self.rows, self.alpha, self.beta)

        self.sorted_rows = [sorted(row, key=lambda x: x["bell"]) for row in self.rows]

        self.score = stats.calculate_score(self.rows, self.threshold / 1000)
        self.score_chart.redraw()

        self.line_row = 0
        self.line_nrows = min(24, len(self.rows))
        self.line_chart.redraw()
        self.slider.value = 0

        self.rms_errors = stats.calculate_rms_errors(self.sorted_rows)
        self.rms_chart.redraw()

        self.faults = stats.calculate_faults(self.sorted_rows, self.threshold / 1000)
        self.faults_chart.redraw()

    # Clear results
    def clear(self):
        self.score = None
        self.rows = []
        self.rms_errors = None
        self.faults = None

        self.score_chart.redraw()
        self.line_chart.redraw()
        self.rms_chart.redraw()
        self.faults_chart.redraw()

    # Overall percent score display
    def score_box(self):
        self.score_chart = toga_chart.Chart(
            style=Pack(flex=1), on_draw=self.draw_score_chart
        )
        return toga.Box(children=[self.score_chart])

    # Blue line display
    def line_box(self):
        def on_zoom(widget):
            match widget.id:
                case "in":
                    self.line_nrows = self.line_nrows // 2
                    if self.line_nrows < MIN_LINE_ROWS:
                        self.line_nrows = MIN_LINE_ROWS
                case "out":
                    self.line_nrows = self.line_nrows * 2
                    self.line_nrows = min(
                        self.line_nrows, len(self.rows), MAX_LINE_ROWS
                    )

                    if self.line_row + self.line_nrows > len(self.rows):
                        self.line_row = len(self.rows) - self.line_nrows

            self.line_chart.redraw()

        def on_scroll(widget):
            self.line_row = int(widget.value * (len(self.rows) - self.line_nrows))
            self.line_chart.redraw()

        self.line_chart = toga_chart.Chart(
            style=Pack(flex=1, padding=10), on_draw=self.draw_line_chart
        )

        zoomin_button = toga.Button(
            "In", id="in", on_press=on_zoom, style=Pack(padding_right=10)
        )
        zoomout_button = toga.Button(
            "Out", id="out", on_press=on_zoom, style=Pack(padding_right=10)
        )
        self.slider = toga.Slider(
            style=Pack(flex=1, padding_right=10), on_release=on_scroll
        )

        button_box = toga.Box(
            children=[
                self.slider,
                zoomin_button,
                zoomout_button,
            ],
            style=Pack(direction="row", padding_bottom=10, padding_top=10),
        )

        return toga.Box(
            children=[self.line_chart, button_box],
            style=Pack(direction="column", alignment="center"),
        )

    # RMS errors display
    def rms_box(self):
        self.rms_chart = toga_chart.Chart(
            style=Pack(flex=1, padding=10), on_draw=self.draw_rms_chart
        )
        return toga.Box(
            children=[self.rms_chart],
        )

    # Faults per bell
    def faults_box(self):
        self.faults_chart = toga_chart.Chart(
            style=Pack(flex=1, padding=10), on_draw=self.draw_faults_chart
        )
        return toga.Box(children=[self.faults_chart])

    # Overall score chart
    def draw_score_chart(self, chart, figure, *args, **kwargs):
        ax = figure.add_subplot(1, 1, 1)
        ax.set_axis_off()

        if self.score is None:
            return

        score = f"{self.score:.0f}%"

        # Hacky method to draw score using matplotlib
        text = ax.text(0.5, 0.5, score, ha="center", va="center", fontsize="medium")

        # Gets around an apparant bug with vertical centering
        figure.canvas.draw()
        figwidth = figure.get_figwidth() * figure.dpi
        figheight = figure.get_figheight() * figure.dpi

        bbox = text.get_window_extent()
        textwidth = bbox.x1 - bbox.x0
        textheight = bbox.y1 - bbox.y0

        hscale = figwidth / textwidth
        vscale = figheight / textheight
        scale = min(hscale, vscale) * 0.9
        fontsize = scale * text.get_fontsize()

        text.remove()
        y = 0.5 - scale * textheight / (2 * figheight)
        text = ax.text(
            0.5, y, score, ha="center", va="bottom", fontsize=fontsize, color=PURPLE
        )

    # Blue line chart
    def draw_line_chart(self, chart, figure, *args, **kwargs):
        if len(self.rows) < MIN_LINE_ROWS:
            return

        nbells = len(self.sorted_rows[0])
        sorted_rows = self.sorted_rows[self.line_row : self.line_row + self.line_nrows]
        x = np.arange(self.line_row, self.line_row + self.line_nrows)

        figure.set_layout_engine("constrained")
        ax = figure.add_subplot(1, 1, 1)
        ax.autoscale(None, "x", tight=True)
        ax.set_frame_on(False)
        ax.set_yticks([])
        ax.set_prop_cycle(
            color=[
                "black",
                GOLD,
                GREEN,
                BLUE,
                GRAY,
                RED,
            ]
        )

        for bell in range(0, nbells):
            offset = [
                row[bell]["time"] - min([s["est"] for s in row]) for row in sorted_rows
            ]
            marker = f"${bell+1}$" if self.line_nrows <= 50 else ""
            ax.plot(
                x,
                offset,
                "-",
                marker=marker,
                markersize=15,
            )

        if self.show_estimates:
            for bell in range(0, nbells):
                offset = [
                    row[bell]["est"] - min([s["est"] for s in row])
                    for row in sorted_rows
                ]
                ax.plot(x, offset, "o")

        ax.set_title(f"Touch {self.touch}")

    # RMS error chart
    def draw_rms_chart(self, chart, figure, *args, **kwargs):
        figure.set_layout_engine("constrained")

        if self.rms_errors is None:
            return

        nbells = len(self.rms_errors)
        rms_errors = [rms * 1000 for rms in self.rms_errors]
        colours = [GOLD if error > 50 else TEAL for error in rms_errors]

        ax = figure.add_subplot(1, 1, 1)
        ax.bar(range(1, nbells + 1), rms_errors, color=colours)

        ax.set_title(f"RMS Accuracy - Touch {self.touch}")
        ax.set_ylabel("Time (ms)")
        ax.set_ylim(0, 100)

    # Faults per bell chart
    def draw_faults_chart(self, chart, figure, *args, **kwargs):
        figure.set_layout_engine("constrained")

        if self.faults is None:
            return

        nbells = len(self.faults)

        hand_early = [-f["hand"]["early"] * 100 for f in self.faults]
        hand_late = [f["hand"]["late"] * 100 for f in self.faults]
        back_early = [-f["back"]["early"] * 100 for f in self.faults]
        back_late = [f["back"]["late"] * 100 for f in self.faults]

        x = np.arange(1, nbells + 1)
        width = 0.35

        ax = figure.add_subplot(1, 1, 1)
        ax.bar(x - width / 2 - 0.01, hand_early, width, label="Hand Early", color=RED)
        ax.bar(x - width / 2 - 0.01, hand_late, width, label="Hand Late", color=PURPLE)
        ax.bar(x + width / 2 + 0.01, back_early, width, label="Back Early", color=GREEN)
        ax.bar(x + width / 2 + 0.01, back_late, width, label="Back Late", color=BLUE)
        ax.legend(loc="upper right", ncols=2)
        ax.set_title(
            f"Touch {self.touch} - Early/late percent ({self.threshold:.0f}ms threshold)"
        )
        ax.set_ylabel("Percentage of blows early/late")
        ax.set_ylim(-75, 75)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: str(int(abs(x)))))

    # Load stored preferences
    def load_prefs(self):
        try:
            with open(Path(self.paths.config, "config.json"), "rt") as fp:
                prefs = json.load(fp)
        except FileNotFoundError:
            prefs = {}

        self.server = prefs.get("server", "192.168.4.1")
        self.threshold = prefs.get("threshold", 50)
        self.alpha = prefs.get("alpha", "0.4")
        self.beta = prefs.get("beta", "0.1")
        self.show_estimates = prefs.get("estimates", False)
        self.include_rounds = prefs.get("rounds", False)

    # Preferences UI
    def prefs_box(self):
        def init_prefs():
            server_input.value = self.server
            threshold_input.value = self.threshold
            alpha_input.value = self.alpha
            beta_input.value = self.beta
            estimates_switch.value = self.show_estimates
            rounds_switch.value = self.include_rounds

        async def on_save(widget):
            if (
                server_input.is_valid
                and threshold_input.is_valid
                and alpha_input.is_valid
                and beta_input.is_valid
            ):
                self.server = server_input.value
                self.threshold = int(threshold_input.value)
                self.alpha = float(alpha_input.value)
                self.beta = float(beta_input.value)
                self.show_estimates = estimates_switch.value
                self.include_rounds = rounds_switch.value

                prefs = {
                    "server": self.server,
                    "threshold": self.threshold,
                    "alpha": self.alpha,
                    "beta": self.beta,
                    "estimates": self.show_estimates,
                    "rounds": self.include_rounds,
                }
                os.makedirs(self.paths.config, exist_ok=True)
                with open(Path(self.paths.config, "config.json"), "wt") as fp:
                    json.dump(prefs, fp)

                self.main_window.content = self.container
                await self.update()

        def on_cancel(widget):
            init_prefs()
            self.main_window.content = self.container

        # CANBell server
        label = toga.Label(
            "CANBell Server",
            style=Pack(width=200, text_align="right", padding_right=10),
        )
        server_input = toga.TextInput(
            style=Pack(width=150), validators=[LengthBetween(3, 15, allow_empty=False)]
        )
        server_box = toga.Box(
            style=Pack(direction="row", padding=10, alignment="center")
        )
        server_box.add(label, server_input)

        # Error threshold
        label = toga.Label(
            "Threshold (ms)",
            style=Pack(width=200, text_align="right", padding_right=10),
        )
        threshold_input = toga.TextInput(
            style=Pack(width=150), validators=[Integer(allow_empty=False)]
        )
        threshold_box = toga.Box(
            style=Pack(direction="row", padding=10, alignment="center")
        )
        threshold_box.add(label, threshold_input)

        # Alpha filter coefficient
        label = toga.Label(
            "Alpha", style=Pack(width=200, text_align="right", padding_right=10)
        )
        alpha_input = toga.TextInput(
            style=Pack(width=150), validators=[Number(allow_empty=False)]
        )
        alpha_box = toga.Box(
            style=Pack(direction="row", padding=10, alignment="center")
        )
        alpha_box.add(label, alpha_input)

        # Beta filter coefficient
        label = toga.Label(
            "Beta", style=Pack(width=200, text_align="right", padding_right=10)
        )
        beta_input = toga.TextInput(
            style=Pack(width=150), validators=[Number(allow_empty=False)]
        )
        beta_box = toga.Box(style=Pack(direction="row", padding=10, alignment="center"))
        beta_box.add(label, beta_input)

        # Show estimated strikes on line chart
        label = toga.Label(
            "Show estimates",
            style=Pack(width=200, text_align="right", padding_right=10),
        )
        estimates_switch = toga.Switch("")
        estimates_box = toga.Box(
            style=Pack(direction="row", padding=10, alignment="center")
        )
        estimates_box.add(label, estimates_switch)

        # Include rounds
        label = toga.Label(
            "Include Rounds",
            style=Pack(width=200, text_align="right", padding_right=10),
        )
        rounds_switch = toga.Switch("")
        rounds_box = toga.Box(
            style=Pack(direction="row", padding=10, alignment="center")
        )
        rounds_box.add(label, rounds_switch)

        # Buttons
        save_button = toga.Button("Save", on_press=on_save, style=Pack(padding_left=20))
        cancel_button = toga.Button("Cancel", on_press=on_cancel)
        padding = toga.Box(style=Pack(flex=1))
        button_box = toga.Box(style=Pack(direction="row", padding=20))
        button_box.add(padding, cancel_button, save_button)

        box = toga.Box(style=Pack(direction="column", padding=10))
        box.add(
            server_box,
            threshold_box,
            alpha_box,
            beta_box,
            estimates_box,
            rounds_box,
            button_box,
        )

        init_prefs()
        return box

    # Get catalog file from CANBell
    async def get_catalog(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{self.server}/log")

        reader = csv.DictReader(io.StringIO(response.text))
        catalog = [x for x in reader]

        return catalog


def main():
    return Strike()
