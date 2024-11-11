"""
Bell striking statistics
"""

import toga
from toga.style import Pack


class Strike(toga.App):
    def startup(self):
        score = toga.Box()
        line = toga.Box()
        rms = toga.Box()
        faults = toga.Box()

        container = toga.OptionContainer(
            content=[("Score", score), ("Line", line), ("RMS", rms), ("Faults", faults)]
        )

        cmd_prefs = toga.Command(
            self.action_prefs,
            "Preferences",
            order=4,
            section=2
        )

        cmd_auto = toga.Command(
            self.action_auto,
            "Auto",
            order=1,
            section=1
        )
        cmd_prev = toga.Command(
            self.action_prev,
            "Prev",
            order=2,
            section=1
        )
        cmd_next = toga.Command(
            self.action_next,
            "Next",
            order=3,
            section=1
        )

        self.commands.add(cmd_auto, cmd_prev, cmd_next, cmd_prefs)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = container


        self.main_window.show()

    def action_auto(self, widget):
        print("Action - auto")

    def action_prev(self, widget):
        print("Action - prev")

    def action_next(self, widget):
        print("Action - next")

    def action_prefs(self, widget):
        print("Action - prefs")


def main():
    return Strike()
