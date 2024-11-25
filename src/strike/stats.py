import numpy as np
import pandas as pd

pd.options.mode.copy_on_write = True


# Converts CSV data stream to data frame
def read_csv(stream):
    strikes = pd.read_csv(stream)

    # Ensure strikes are in ascending time order
    strikes.sort_values("ticks_ms", inplace=True)
    strikes.reset_index()

    # Convert milliseconds to seconds
    strikes["time"] = strikes["ticks_ms"] / 1000

    # Array of bells
    bells = np.sort(strikes["bell"].unique())

    return bells, strikes


# Get whole rows, discard strikes following an incomplete row
def whole_rows(bells, strikes):
    nbells = len(bells)
    if nbells < 3:
        return strikes[0:0]

    # Drop data following an incomplete row
    for i, group in strikes.groupby(strikes.index // nbells):
        if group["bell"].nunique() != nbells:
            break
    strikes = strikes[: i * nbells]

    return strikes


# Find method start and stop rows
def method_start_stop(bells, strikes):
    nbells = len(bells)
    for first, group in strikes.groupby(strikes.index // nbells):
        if (group["bell"] != bells).any():
            break
    first_row = max(((first - 1) // 2) * 2, 0)

    for last, group in strikes.groupby((strikes.index // nbells)[::-1]):
        if (group["bell"] != bells).any():
            break
    last_row = len(strikes) // nbells - last + 1

    return first_row, last_row


# Alpha Beta filter (see https://en.wikipedia.org/wiki/Alpha_beta_filter)
def alpha_beta(nbells, strikes, alpha=0.4, beta=0.1):
    if len(strikes) == 0:
        return strikes

    times = strikes["time"].values
    ests = []

    # Intitial state estimates, tk is the strike time, dk is the time between strikes
    tk_1 = times[0]
    dk_1 = (times[-1] - tk_1) / (len(times) - 1) * nbells / (nbells + 0.5)
    ests.append(tk_1)

    for n, time in enumerate(times[1:], start=1):
        gap = 2 if n % (nbells * 2) == 0 else 1

        tk = tk_1 + dk_1 * gap
        rk = time - tk

        tk_1 = tk + alpha * rk
        dk_1 += beta * rk

        ests.append(tk_1)

    strikes["est"] = ests
    strikes["err"] = strikes["time"] - ests


# Calcuate overall percentage score
def calculate_score(nbells, strikes, threshold=0.05):
    if len(strikes) == 0:
        return 0

    score = 0
    for _, row in strikes.groupby(strikes.index // nbells):
        max_error = np.fabs(row["err"]).max()
        if max_error < threshold:
            score += 1

    return 100 * score / (len(strikes) / nbells)


# Calculate RMS error for all bells
def calculate_rms_errors(strikes):
    return [np.sqrt(np.mean(s["err"] ** 2)) for _, s in strikes.groupby("bell")]


def calculate_faults(strikes, threshold=0.05):
    out = []
    for _, s in strikes.groupby("bell"):
        hand = s[::2]
        h_late = (hand["err"] > threshold).sum() / len(hand) * 100
        h_early = (hand["err"] < -threshold).sum() / len(hand) * 100

        back = s[1::2]
        b_late = (back["err"] > threshold).sum() / len(back) * 100
        b_early = (back["err"] < -threshold).sum() / len(back) * 100

        out.append(
            {
                "hand": {"early": h_early, "late": h_late},
                "back": {"early": b_early, "late": b_late},
            }
        )

    return out
