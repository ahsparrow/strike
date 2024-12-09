"""
Bell striking statistics
"""

import asyncio
import csv
import io
import json
import os
import platform
from enum import Enum
from pathlib import Path

import httpx
import matplotlib.ticker as ticker
import numpy as np
import toga
import toga_chart
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


class Mode(Enum):
    LOCAL = 1
    REMOTE = 2


class Strike(toga.App):
    def startup(self):
        self.load_prefs()

        self.mode = Mode.REMOTE

        # Touch info
        self.remote_touch = 0
        self.local_path = None

        # Striking results
        self.score = None
        self.strikes = None
        self.rms_errors = None
        self.faults = None

        # CANBell websocket task
        self.ws_task = None

        # Line display parameters
        self.line_row = 0
        self.line_nrows = MIN_LINE_ROWS

        # Main UI
        score = self.score_box()
        line = self.line_box()
        rms = self.rms_box()
        faults = self.faults_box()
        self.container = toga.OptionContainer(
            content=[
                ("Score", score, toga.Icon("resources/score")),
                ("Line", line, toga.Icon("resources/line")),
                ("Accuracy", rms, toga.Icon("resources/rms")),
                ("Striking", faults, toga.Icon("resources/faults")),
            ]
        )

        # Preferences UI
        self.prefs_content = self.prefs_box()

        # Commands
        cmd_prefs = toga.Command(self.action_prefs, "Preferences", order=1, section=2)
        cmd_auto = toga.Command(self.action_auto, "Auto", order=1, section=1)
        cmd_first = toga.Command(
            self.action_nav, "First", id="first", order=2, section=1, shortcut="P"
        )
        cmd_prev = toga.Command(
            self.action_nav, "Prev", id="prev", order=3, section=1, shortcut="p"
        )
        cmd_next = toga.Command(
            self.action_nav, "Next", id="next", order=4, section=1, shortcut="n"
        )
        cmd_last = toga.Command(
            self.action_nav, "Last", id="last", order=5, section=1, shortcut="N"
        )
        self.commands.add(cmd_auto, cmd_first, cmd_prev, cmd_next, cmd_last, cmd_prefs)

        # TBD replace with platform.system() when upgraded to python 3.13
        if "android" not in platform.platform():
            # File open for desktop environments
            cmd_open = toga.Command(
                self.action_open, "Open...", group=toga.Group.FILE, order=1
            )
            cmd_connect = toga.Command(
                self.action_connect, "Connect", group=toga.Group.FILE, order=2
            )
            self.commands.add(cmd_open, cmd_connect)
        else:
            # File open for Android
            cmd_open = toga.Command(
                self.action_open_android, "Local", order=6, section=1
            )
            self.commands.add(cmd_open)

        # Top level window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.container
        self.main_window.show()

    # Auto action
    def action_auto(self, widget):
        async def ws_recv():
            try:
                async for websocket in connect(f"ws://{self.server}/status"):
                    while True:
                        msg = await websocket.recv()
                        if msg == "idle":
                            await self.nav_remote("last")
                        else:
                            self.clear()
            except asyncio.CancelledError:
                await websocket.close()

        if self.ws_task is None or self.ws_task.cancelled():
            self.ws_task = asyncio.create_task(ws_recv())

    # Navigation action
    async def action_nav(self, widget):
        # Cancel websocket updates
        if self.ws_task is not None:
            self.ws_task.cancel()

        if self.mode == Mode.REMOTE:
            await self.nav_remote(widget.id)
        else:
            self.nav_local(widget.id)

    # Preferences action
    def action_prefs(self, widget):
        self.main_window.content = self.prefs_content

    # File open action
    async def action_open(self, widget):
        # Cancel websocket updates
        if self.ws_task is not None:
            self.ws_task.cancel()

        file_dialog = toga.OpenFileDialog("Touch file", file_types=["csv"])
        path = await self.main_window.dialog(file_dialog)

        if path:
            self.mode = Mode.LOCAL
            self.local_path = Path(path)
            with open(self.local_path) as stream:
                self.load_touch(stream, self.local_path.name)

    # File open action for Android
    async def action_open_android(self, widget):
        from android.content import Intent
        from java import jarray, jbyte

        # Cancel websocket updates
        if self.ws_task is not None:
            self.ws_task.cancel()

        # Show file chooser
        file_chooser = Intent(Intent.ACTION_GET_CONTENT)
        file_chooser.addCategory(Intent.CATEGORY_OPENABLE)
        # text/csv doesn't work
        file_chooser.setType("*/*")

        results = await self._impl.intent_result(
            Intent.createChooser(file_chooser, "Choose a touch")
        )
        data = results["resultData"].getData()
        context = self._impl.native
        stream = context.getContentResolver().openInputStream(data)

        block = jarray(jbyte)(1024 * 1024)
        blocks = []
        while True:
            bytes_read = stream.read(block)
            if bytes_read == -1:
                break
            else:
                blocks.append(bytes(block)[:bytes_read])

        data = b"".join(blocks)
        text_stream = io.StringIO(data.decode())
        self.load_touch(text_stream, "Local")

    # Remote data action
    async def action_connect(self, widget):
        if self.mode == Mode.REMOTE:
            return

        self.mode = Mode.REMOTE

    # Navigate remote touches
    async def nav_remote(self, nav):
        catalog = await self.get_catalog()
        ntouches = len(catalog)

        if ntouches == 0:
            self.remote_touch = 0
            self.clear()
        else:
            match nav:
                case "first":
                    self.remote_touch = 1
                case "last":
                    self.remote_touch = ntouches
                case "next":
                    if self.remote_touch == 0 or self.remote_touch >= ntouches:
                        self.remote_touch = ntouches
                    else:
                        self.remote_touch += 1
                case "prev":
                    if self.remote_touch == 0 or self.remote_touch == 1:
                        self.remote_touch = 1
                    else:
                        self.remote_touch -= 1

            await self.download()

    # Navigate local touches
    def nav_local(self, nav):
        paths = sorted(self.local_path.parent.glob("touch_??.csv"))
        n = paths.index(self.local_path)

        path = self.local_path
        match nav:
            case "first":
                path = paths[0]
            case "last":
                path = paths[-1]
            case "next":
                if n < len(paths) - 1:
                    path = paths[n + 1]
            case "prev":
                if n > 0:
                    path = paths[n - 1]

        self.local_path = path
        with open(self.local_path) as stream:
            self.load_touch(stream, self.local_path.name)

    # Download touch data
    async def download(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{self.server}/log/{self.remote_touch}")

        self.load_touch(io.StringIO(response.text), f"Touch {self.remote_touch}")

    # Load touch data, call after loading new data
    def load_touch(self, stream, title):
        bells, strikes = stats.read_csv(stream)

        # Check for incomplete rows
        self.strikes = stats.whole_rows(bells, strikes)

        self.bells = bells
        self.nrows = len(self.strikes) // len(self.bells)

        # Method start and stop
        self.first_row, self.last_row = stats.method_start_stop(bells, self.strikes)

        self.line_row = 0
        self.line_nrows = min(24, len(self.strikes) // len(bells))
        self.slider.value = 0

        self.main_window.title = title
        self.update()

    # Update results, call after loading new touch or changing preferences
    def update(self):
        # Update strikes with estimated times
        stats.alpha_beta(len(self.bells), self.strikes, self.alpha, self.beta)

        # Exclude or include start and end rounds from scoring
        if not self.include_rounds:
            score_strikes = self.strikes[
                self.first_row * len(self.bells) : self.last_row * len(self.bells)
            ]
        else:
            score_strikes = self.strikes

        self.score = stats.calculate_score(
            len(self.bells), score_strikes, self.threshold / 1000
        )
        # self.score_chart.redraw()
        self.redraw_score()

        self.line_chart.redraw()

        self.rms_errors = stats.calculate_rms_errors(score_strikes)
        self.rms_chart.redraw()

        self.faults = stats.calculate_faults(score_strikes, self.threshold / 1000)
        self.faults_chart.redraw()

    # Clear results
    def clear(self):
        self.score = None
        self.data = []
        self.rms_errors = None
        self.faults = None

        self.redraw_score()
        self.line_chart.redraw()
        self.rms_chart.redraw()
        self.faults_chart.redraw()

        self.main_window.title = self.formal_name

    # Overall percent score display
    def score_box(self):
        self.score_canvas = toga.Canvas(style=Pack(flex=1), on_resize=self.on_resize)
        font = toga.Font("sans-serif", 100)
        with self.score_canvas.Fill(color=PURPLE) as text_filler:
            self.score_text = text_filler.write_text(" ", 100, 100, font)

        with self.score_canvas.Fill(color="black") as text_filler:
            self.score_title = text_filler.write_text(
                " ", 100, 100, toga.Font("sans-serif", 15)
            )

        return toga.Box(children=[self.score_canvas])

    # Blue line display
    def line_box(self):
        def on_zoom(widget):
            match widget.id:
                case "in":
                    self.line_nrows = int(self.line_nrows // 1.5)
                    self.line_nrows = max(MIN_LINE_ROWS, self.line_nrows)
                case "out":
                    self.line_nrows = int(self.line_nrows * 1.5)
                    self.line_nrows = min(MAX_LINE_ROWS, self.nrows, self.line_nrows)

                    if self.line_row + self.line_nrows > self.nrows:
                        self.line_row = self.nrows - self.line_nrows

            if self.line_nrows == self.nrows:
                self.slider.value = 0
            else:
                self.slider.value = self.line_row / (self.nrows - self.line_nrows)

            self.line_chart.redraw()

        def on_scroll(widget):
            self.line_row = int(widget.value * (self.nrows - self.line_nrows))
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
            style=Pack(
                direction="row", padding_bottom=10, padding_top=10, alignment="center"
            ),
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

    # Resize score canvas
    def on_resize(self, canvas, width, height, **kwargs):
        if canvas.context:
            self.resize_canvas(canvas, width, height)

    # Update score text size
    def resize_canvas(self, canvas, width, height):
        # Need this for Android, don't know why
        if width == 0 or height == 0:
            return

        # Center score horizontal and vertical
        text_width, text_height = canvas.measure_text(
            self.score_text.text, self.score_text.font
        )
        # 0.6 is a bodge to convert line height to actual text height
        text_height = text_height * 0.6

        scale = min(height / text_height, width / text_width) * 0.85

        self.score_text.font = toga.Font(
            family="sans-serif", size=self.score_text.font.size * scale
        )
        self.score_text.x = (width - text_width * scale) / 2
        self.score_text.y = (height + text_height * scale) / 2

        # Place title top, centre
        title_width, title_height = canvas.measure_text(
            self.score_title.text, self.score_title.font
        )
        self.score_title.x = (width - title_width) / 2
        self.score_title.y = title_height

    # Update score text
    def redraw_score(self):
        self.score_text.text = f"{self.score:.0f}%" if self.score is not None else " "

        self.score_canvas.redraw()
        self.resize_canvas(
            self.score_canvas,
            self.score_canvas.layout.content_width,
            self.score_canvas.layout.content_height,
        )

    # Blue line chart
    def draw_line_chart(self, chart, figure, *args, **kwargs):
        if self.strikes is None or len(self.strikes) < MIN_LINE_ROWS * len(self.bells):
            return

        color = ["black", GOLD, GREEN, BLUE, GRAY, RED, PURPLE, TEAL]

        figure.set_layout_engine("constrained")
        ax = figure.add_subplot(1, 1, 1)
        ax.autoscale(None, "x", tight=True)
        ax.set_frame_on(False)
        ax.set_yticks([])
        ax.set_prop_cycle(color=color)
        # Integer only xaxis labels
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        refs = [
            row["est"].min()
            for _, row in self.strikes.groupby(self.strikes.index // len(self.bells))
        ]
        x = np.arange(self.line_row, self.line_row + self.line_nrows)

        for bell, strikes in self.strikes.groupby("bell"):
            offsets = strikes["time"] - refs

            marker = f"${bell}$" if self.line_nrows <= 50 else ""
            ax.plot(
                x,
                offsets[self.line_row : self.line_row + self.line_nrows],
                "-",
                marker=marker,
                markersize=15,
            )

        if self.show_estimates:
            ax.set_prop_cycle(color=color)
            for bell, strikes in self.strikes.groupby("bell"):
                offsets = strikes["est"] - refs
                ax.plot(
                    x, offsets[self.line_row : self.line_row + self.line_nrows], "o"
                )

    # RMS error chart
    def draw_rms_chart(self, chart, figure, *args, **kwargs):
        figure.set_layout_engine("constrained")

        if self.rms_errors is None:
            return

        nbells = len(self.rms_errors)
        rms_errors = [rms * 1000 for rms in self.rms_errors]
        colours = [GOLD if error > 50 else TEAL for error in rms_errors]

        ax = figure.add_subplot(1, 1, 1)
        ax.bar(range(1, nbells + 1), rms_errors, color=colours, tick_label=self.bells)

        ax.set_title("RMS Accuracy")
        ax.set_ylabel("Time (ms)")
        ax.set_ylim(0, 100)

    # Faults per bell chart
    def draw_faults_chart(self, chart, figure, *args, **kwargs):
        figure.set_layout_engine("constrained")

        if self.faults is None:
            return

        nbells = len(self.faults)

        hand_early = [-f["hand"]["early"] for f in self.faults]
        hand_late = [f["hand"]["late"] for f in self.faults]
        back_early = [-f["back"]["early"] for f in self.faults]
        back_late = [f["back"]["late"] for f in self.faults]

        x = np.arange(1, nbells + 1)
        width = 0.35

        ax = figure.add_subplot(1, 1, 1)
        ax.bar(
            x - width / 2 - 0.01,
            hand_early,
            width,
            label="Hand Early",
            color=RED,
            tick_label=self.bells,
        )
        ax.bar(x - width / 2 - 0.01, hand_late, width, label="Hand Late", color=PURPLE)
        ax.bar(x + width / 2 + 0.01, back_early, width, label="Back Early", color=GREEN)
        ax.bar(x + width / 2 + 0.01, back_late, width, label="Back Late", color=BLUE)
        ax.legend(loc="upper right", ncols=2)
        ax.set_title(f"Early/late percent ({self.threshold:.0f}ms threshold)")
        ax.set_ylabel("Percentage of blows early/late")
        ax.set_ylim(-75, 75)
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda x, pos: str(int(abs(x))))
        )

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

        def on_save(widget):
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
                self.update()

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
