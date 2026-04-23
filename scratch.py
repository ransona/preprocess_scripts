import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# File locations
tokenised_path = Path(
    "/home/pmateosaparicio/data/Repository/ESPM154/2025-07-04_04_ESPM154/recordings/s2p_tokenised_ch0.pickle"
)
timeseries_path = Path(
    "/home/pmateosaparicio/data/Repository/ESPM154/2025-07-04_04_ESPM154/recordings/s2p_ch0.pickle"
)

# Load both pickle files
with tokenised_path.open("rb") as f:
    tokenised_data = pickle.load(f)

with timeseries_path.open("rb") as f:
    timeseries_data = pickle.load(f)

# Pull out the actual arrays from the dicts
tokenised = tokenised_data["all_tokenised_dF_spikes"]  # [cellID, time, response]
t = timeseries_data["t"]  # time vector
spikes = timeseries_data["Spikes"]  # [neurons, time]

# Split the tokenised matrix into columns
cell_ids = tokenised[:, 0].astype(int)
token_times = tokenised[:, 1]
token_response = tokenised[:, 2]

# Pick 3 random neurons from the full neuron range
rng = np.random.default_rng(42)
selected_cells = rng.choice(spikes.shape[0], size=3, replace=False)

# Make one subplot per neuron
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=False)

for ax, cell_id in zip(axes, selected_cells):
    # Get all tokenised events for this neuron
    mask = cell_ids == cell_id
    tok_t = token_times[mask]
    tok_r = token_response[mask]

    # Get the same neuron from the time-series file
    ts_r = spikes[cell_id]

    # Plot both representations
    ax.scatter(tok_t, tok_r, s=18, alpha=0.75, label="Tokenised", color="tab:blue")
    ax.plot(t, ts_r, lw=1.2, alpha=0.8, label="Time-series", color="tab:orange")
    ax.set_title(f"Neuron {cell_id}")
    ax.set_ylabel("Response / amplitude")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")

axes[-1].set_xlabel("Time")
fig.suptitle("Tokenised vs. time-series data check", y=0.98)
fig.tight_layout()
plt.show()
