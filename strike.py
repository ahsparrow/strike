import csv
import itertools
import math
import sys

import matplotlib.pyplot as plt


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
        dk += beta * rk / (dk * gap)

        tk_1 = tk
        dk_1 = dk

        strike["est"] = tk


if __name__ == "__main__":
    with open(sys.argv[1]) as csvfile:
        # Convert time from ms to s
        strikes = [
            {"bell": int(x[0]), "time": int(x[1]) / 1000} for x in csv.reader(csvfile)
        ]

    nbells, strikes = whole_rows(strikes)

    # Dump the first four rows
    strikes = strikes[4 * nbells :]

    alpha_beta(nbells, strikes, 0.1, 0.001)

    rows = list(zip(*[iter(strikes)] * nbells))
    sorted_rows = [sorted(row, key=lambda x: x["bell"]) for row in rows]

    for b in range(0, 6):
        rms = math.sqrt(
            sum([(row[b]["est"] - row[b]["time"]) ** 2 for row in sorted_rows])
        ) / math.sqrt(len(rows))
        print(f"{rms*1000:0.1f}")

    for b in range(0, 6):
        actual = [
            sorted_row[b]["time"] - row[0]["est"]
            for row, sorted_row in zip(rows, sorted_rows)
        ]
        plt.plot(actual, "o-")

    for b in range(0, nbells):
        est = [
            sorted_row[b]["est"] - row[0]["est"]
            for row, sorted_row in zip(rows, sorted_rows)
        ]
        plt.plot(est, "x")

    plt.show()
