"""
Bell striking statistics
"""

import csv
import io
import json
import os
from pathlib import Path

import httpx
import toga
import toga_chart
from toga.style.pack import Pack
from toga.validators import LengthBetween, Number

from . import stats


class Strike(toga.App):
    def startup(self):
        self.load_prefs()

        self.touch = 0
        self.rms_errors = None

        score = toga.Box()
        line = self.line_box()
        rms = self.rms_box()
        faults = toga.Box()

        self.container = toga.OptionContainer(
            content=[("Score", score), ("Line", line), ("RMS", rms), ("Faults", faults)]
        )

        self.prefs_content = self.prefs_box()

        cmd_prefs = toga.Command(self.action_prefs, "Preferences", order=4, section=2)

        cmd_auto = toga.Command(self.action_auto, "Auto", order=1, section=1)
        cmd_prev = toga.Command(self.action_prev, "Prev", order=2, section=1)
        cmd_next = toga.Command(self.action_next, "Next", order=3, section=1)

        self.commands.add(cmd_auto, cmd_prev, cmd_next, cmd_prefs)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.container
        self.main_window.show()

    async def action_auto(self, widget):
        print("Action - auto")
        catalog = await self.get_catalog()
        print(catalog)

    async def action_prev(self, widget):
        print("Action - prev")
        catalog = await self.get_catalog()
        if self.touch == 0 or self.touch > len(catalog):
            self.touch = 1
        elif self.touch != 1:
            self.touch -= 1

        await self.update()

    async def action_next(self, widget):
        print("Action - next")
        catalog = await self.get_catalog()
        ntouches = len(catalog)
        if self.touch == 0 or self.touch >= (ntouches - 1):
            self.touch = len(catalog)
        else:
            self.touch += 1

        await self.update()

    def action_prefs(self, widget):
        self.main_window.content = self.prefs_content

    async def get_catalog(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{self.server}/log")

        reader = csv.DictReader(io.StringIO(response.text))
        catalog = [x for x in reader]

        return catalog

    def load_prefs(self):
        try:
            with open(Path(self.paths.config, "config.json"), "rt") as fp:
                prefs = json.load(fp)
        except FileNotFoundError:
            prefs = {}

        self.server = prefs.get("server", "192.168.4.1")
        self.alpha = prefs.get("alpha", "0.4")
        self.beta = prefs.get("beta", "0.1")
        self.include_rounds = prefs.get("rounds", False)

    async def update(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{self.server}/log/{self.touch}")

        reader = csv.DictReader(io.StringIO(response.text))
        data = [
            {"bell": int(x["bell"]), "time": int(x["ticks_ms"]) / 1000} for x in reader
        ]

        nbells, strikes = stats.whole_rows(data)
        stats.alpha_beta(nbells, strikes, self.alpha, self.beta)

        rows = list(zip(*[iter(strikes)] * nbells))
        sorted_rows = [sorted(row, key=lambda x: x["bell"]) for row in rows]

        self.rms_errors = stats.calculate_rms_errors(sorted_rows)
        self.rms_chart.redraw()

    def line_box(self):
        self.line_chart = toga_chart.Chart(
            style=Pack(flex=1), on_draw=self.draw_line_chart
        )
        box = toga.Box(children=[self.line_chart])

        return box

    def rms_box(self):
        self.rms_chart = toga_chart.Chart(
            style=Pack(flex=1), on_draw=self.draw_rms_chart
        )
        box = toga.Box(children=[self.rms_chart])

        return box

    def draw_rms_chart(self, chart, figure, *args, **kwargs):
        if self.rms_errors is None:
            return

        nbells = len(self.rms_errors)
        rms_errors = [rms * 1000 for rms in self.rms_errors]
        colours = ["orange" if error > 50 else "green" for error in rms_errors]

        ax = figure.add_subplot(1, 1, 1)
        ax.bar(range(1, nbells + 1), rms_errors, color=colours)

        ax.set_title("RMS Errors")
        ax.set_ylabel("Error (ms)")
        figure.tight_layout()

    def draw_line_chart(self, chart, figure, *args, **kwargs):
        ax = figure.add_subplot(1, 1, 1)
        ax.plot([1, 4, 9, 16])

        figure.tight_layout()

    def prefs_box(self):
        def init_prefs():
            server_input.value = self.server
            alpha_input.value = self.alpha
            beta_input.value = self.beta
            rounds_switch.value = self.include_rounds

        def on_save(widget):
            if server_input.is_valid and alpha_input.is_valid and beta_input.is_valid:
                self.server = server_input.value
                self.alpha = float(alpha_input.value)
                self.beta = float(beta_input.value)
                self.include_rounds = rounds_switch.value

                prefs = {
                    "server": self.server,
                    "alpha": self.alpha,
                    "beta": self.beta,
                    "rounds": self.include_rounds,
                }
                os.makedirs(self.paths.config, exist_ok=True)
                with open(Path(self.paths.config, "config.json"), "wt") as fp:
                    json.dump(prefs, fp)

                self.main_window.content = self.container

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
        box.add(server_box, alpha_box, beta_box, rounds_box, button_box)

        init_prefs()
        return box


def main():
    return Strike()
