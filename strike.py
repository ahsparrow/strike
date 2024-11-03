import csv
import itertools
import math
import sys

import matplotlib.pyplot as plt
import numpy as np


# Get whole rows, discard any strikes after an imcomplete row
def whole_rows(strikes):
    # Sort strikes in time order
    strikes.sort(key=lambda s: s["time"])

    # Get the number of bells
    nbells = len(set([s["bell"] for s in strikes]))

    # Split into rows
    iterators = [iter(strikes)] * nbells
    rows = zip(*iterators)

    # Terminate after any incomplete row
    rows = itertools.takewhile(
        lambda row: len(set(x["bell"] for x in row)) == nbells, rows
    )

    return nbells, list(itertools.chain(*rows))


# Alpha Beta filter (see https://en.wikipedia.org/wiki/Alpha_beta_filter)
def alpha_beta(nbells, strikes, alpha=0.4, beta=0.1):
    # Intitial state estimates, tk is the strike time, dk is the time between strikes
    tk_1 = strikes[0]["time"]
    dk_1 = (strikes[-1]["time"] - tk_1) / (len(strikes) - 1) * nbells / (nbells + 0.5)
    strikes[0]["est"] = tk_1

    for n, strike in enumerate(strikes[1:], start=1):
        gap = 2 if n % (nbells * 2) == 0 else 1

        tk = tk_1 + dk_1 * gap
        dk = dk_1

        rk = strike["time"] - tk

        tk += alpha * rk
        dk += beta * rk

        tk_1 = tk
        dk_1 = dk

        strike["est"] = tk


# Calculate RMS error for all bells
def calculate_rms_errors(sorted_rows):
    nbells = len(sorted_rows[0])
    nrows = len(sorted_rows)

    out = []
    for bell in range(nbells):
        squares = 0
        for row in sorted_rows:
            squares += (row[bell]["est"] - row[bell]["time"]) ** 2

        rms = math.sqrt(squares / nrows)
        out.append(rms)

    return out


def calculate_faults(sorted_rows, threshold=0.05):
    def count_faults(strikes):
        early_error = 0
        late_error = 0
        for strike in strikes:
            err = strike["time"] - strike["est"]
            if abs(err) > 0.05:
                if err > 0:
                    late_error += 1
                else:
                    early_error += 1

        nstrikes = len(strikes)
        return {"early": early_error / nstrikes, "late": late_error / nstrikes}

    nbells = len(sorted_rows[0])

    out = []
    for bell in range(nbells):
        hand = count_faults([row[bell] for row in sorted_rows[::2]])
        back = count_faults([row[bell] for row in sorted_rows[1::2]])

        out.append({"hand": hand, "back": back})

    return out


def plot_rms_errors(rms_errors):
    nbells = len(rms_errors)
    rms_errors = [rms * 1000 for rms in rms_errors]

    colours = ["red" if error > 50 else "green" for error in rms_errors]

    fig, ax = plt.subplots()

    ax.bar(range(1, nbells + 1), rms_errors, color=colours)
    ax.set_title("RMS Error (ms)")
    plt.show()


def plot_faults(faults):
    nbells = len(faults)

    x = np.arange(1, nbells + 1)
    width = 0.25

    fig, ax = plt.subplots()

    hand_early = [-f["hand"]["early"] * 100 for f in faults]
    hand_late = [f["hand"]["late"] * 100 for f in faults]
    back_early = [-f["back"]["early"] * 100 for f in faults]
    back_late = [f["back"]["late"] * 100 for f in faults]

    ax.bar(x - width / 2 - 0.01, hand_early, width, label="Hand Early", color="tab:red")
    ax.bar(
        x - width / 2 - 0.01,
        hand_late,
        width,
        label="Hand Late",
        color="tab:purple",
    )
    ax.bar(
        x + width / 2 + 0.01, back_early, width, label="Back Early", color="tab:orange"
    )
    ax.bar(
        x + width / 2 + 0.01,
        back_late,
        width,
        label="Back Late",
        color="tab:cyan",
    )
    ax.legend(loc="upper right", ncols=2)
    ax.set_title("Faults percent (50ms threshold)")

    plt.show()


def plot_striking(sorted_rows):
    nbells = len(sorted_rows[0])

    for bell in range(0, nbells):
        actual = [
            sorted_row[bell]["time"] - min([s["est"] for s in sorted_row])
            for row, sorted_row in zip(rows, sorted_rows)
        ]
        plt.plot(actual, "o-")

    plt.gca().set_prop_cycle(None)

    for bell in range(0, nbells):
        est = [
            sorted_row[bell]["est"] - min([s["est"] for s in sorted_row])
            for row, sorted_row in zip(rows, sorted_rows)
        ]
        plt.plot(est, ".")

    plt.show()


if __name__ == "__main__":
    with open(sys.argv[1]) as csvfile:
        # Convert time from ms to s
        strikes = [
            {"bell": int(x[0]), "time": int(x[1]) / 1000} for x in csv.reader(csvfile)
        ]

    # Check for incomplete rows
    nbells, strikes = whole_rows(strikes)

    # State estimation
    alpha_beta(nbells, strikes, 0.4, 0.1)

    rows = list(zip(*[iter(strikes)] * nbells))
    sorted_rows = [sorted(row, key=lambda x: x["bell"]) for row in rows]

    # RMS errors
    rms_errors = calculate_rms_errors(sorted_rows)

    # Striking faults
    faults = calculate_faults(sorted_rows)

    # plot_rms_errors(rms_errors)
    # plot_faults(faults)
    plot_striking(sorted_rows)
