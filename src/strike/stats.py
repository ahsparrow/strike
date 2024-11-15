import itertools
import math


# Get whole rows, discard any strikes after an incomplete row
def whole_rows(strikes, include_rounds=True):
    # Sort strikes in time order
    strikes.sort(key=lambda s: s["time"])

    # Get the number of bells
    nbells = len(set([s["bell"] for s in strikes]))

    # Split into rows
    iterators = [iter(strikes)] * nbells
    rows = zip(*iterators)

    # Terminate after any incomplete row
    rows = list(
        itertools.takewhile(
            lambda row: len(set(x["bell"] for x in row)) == nbells, rows
        )
    )

    if nbells < 3:
        return nbells, []

    if not include_rounds:
        rounds = list(range(1, nbells + 1))
        # Discard rounds at start
        while True:
            if len(rows) >= 3 and list([s["bell"] for s in rows[2]]) == rounds:
                # Discard two rows at a time, so result starts at handstroke
                rows.pop(0)
                rows.pop(0)
            else:
                break

        # Discard rounds at end
        while True:
            if len(rows) >= 2 and list([s["bell"] for s in rows[-2]]) == rounds:
                rows.pop()
            else:
                break

        if len(rows) < 2:
            return nbells, []

    return nbells, rows


# Alpha Beta filter (see https://en.wikipedia.org/wiki/Alpha_beta_filter)
def alpha_beta(nbells, rows, alpha=0.4, beta=0.1):
    strikes = list(itertools.chain(*rows))

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


# Calcuate overall percentage score
def calculate_score(rows, threshold=0.05):
    score = 0
    for row in rows:
        max_error = max([abs(bell["est"] - bell["time"]) for bell in row])
        if max_error < threshold:
            score += 1

    return 100 * score / len(rows)


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
            if abs(err) > threshold:
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
