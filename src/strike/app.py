"""
Bell striking statistics
"""

import json
import os
from pathlib import Path

import toga
from toga.style.pack import Pack
from toga.validators import LengthBetween, Number


class Strike(toga.App):
    def startup(self):
        self.load_prefs()

        score = toga.Box()
        line = toga.Box()
        rms = toga.Box()
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

    def action_auto(self, widget):
        print("Action - auto")

    def action_prev(self, widget):
        print("Action - prev")

    def action_next(self, widget):
        print("Action - next")

    def action_prefs(self, widget):
        self.main_window.content = self.prefs_content

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

    def prefs_box(self):
        def init_prefs():
            server_input.value = self.server
            alpha_input.value = self.alpha
            beta_input.value = self.beta
            rounds_switch.value = self.include_rounds

        def on_save(widget):
            if server_input.is_valid and alpha_input.is_valid and beta_input.is_valid:
                self.server = server_input.value
                self.alpha = alpha_input.value
                self.beta = beta_input.value
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
