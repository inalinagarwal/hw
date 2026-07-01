#!/usr/bin/env python3
import glob, numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import Patch

JOINTS = ['FFJ4','MFJ4','RFJ4','THJ5','FFJ3','MFJ3','RFJ3','THJ4',
          'FFJ2','MFJ2','RFJ2','FFJ1','MFJ1','RFJ1','THJ2','THJ1']

# sim tactile channel names (24)
TAC_NAMES = ("world forearm palm ffknuck mfknuck rfknuckle thbase "
             "ffprox mfprox rfprox thprox ffmid mfmid rfmid thhub "
             "ffdist mfdist rfdist thmid fftip mftip rftip thdist thtip").split()

# your 7 FSR channels (mux order)
FSR_CH = [10, 7, 4, 9, 5, 2, 11]
FSR_NAMES = ["thprox","ffprox","mfknuck","rfprox","rfknuck","palm","ffmid"]

sim = np.load("sim_policy_log_seed1.npz", allow_pickle=True)
hw  = np.load("hw_policy_log_ablate.npz", allow_pickle=True)
n = min(len(sim["q"]), len(hw["q"]))
sq, scmd = sim["q"][:n], sim["cmd"][:n]
hq, hcmd = hw["q"][:n], hw["cmd"][:n]
stac, htac = sim["tac"][:n], hw["tac"][:n]

# ---- Fig 1: joint cmd vs achieved (4x4) ----
fig, ax = plt.subplots(4, 4, figsize=(18, 12), sharex=True)
for j, a in enumerate(ax.flat):
    a.plot(scmd[:, j], 'k--', lw=0.8, alpha=0.7, label='sim cmd')
    a.plot(sq[:, j], label='sim achieved', alpha=0.8)
    a.plot(hcmd[:, j], 'r--', lw=0.8, alpha=0.7, label='hw cmd')
    a.plot(hq[:, j], label='hw achieved', alpha=0.8)
    a.set_title(JOINTS[j]); a.grid(True, alpha=0.3)
ax.flat[0].legend(fontsize=7)
fig.suptitle("Joint trajectories: sim vs hardware")
fig.tight_layout(); fig.savefig("/home/nalin/roto/7sensor_ablate_plots/hw_vs_sim_joints.png", dpi=150)

# ---- Fig 2: tracking error (cmd - achieved) RMS per joint ----
sim_err = np.sqrt(((scmd - sq)**2).mean(0))
hw_err  = np.sqrt(((hcmd - hq)**2).mean(0))
x = np.arange(16); w = 0.35
fig2, ax2 = plt.subplots(figsize=(12, 4))
ax2.bar(x - w/2, np.degrees(sim_err), w, label='sim')
ax2.bar(x + w/2, np.degrees(hw_err),  w, label='hw')
ax2.set_xticks(x); ax2.set_xticklabels(JOINTS, rotation=45, ha='right')
ax2.set_ylabel("RMS tracking error (deg)")
ax2.set_title("Command vs achieved mismatch")
ax2.legend(); fig2.tight_layout(); fig2.savefig("/home/nalin/roto/7sensor_ablate_plots/hw_vs_sim_tracking_err.png", dpi=150)

# ---- Fig 3: tactile activation % (7 instrumented channels only) ----
sim_freq = 100 * stac.mean(0)
hw_freq  = 100 * htac.mean(0)
labels = [TAC_NAMES[c] for c in FSR_CH]
sv = [sim_freq[c] for c in FSR_CH]
hv = [hw_freq[c] for c in FSR_CH]
x = np.arange(7); w = 0.35
fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.bar(x - w/2, sv, w, label='sim', color='#4c72b0')
ax3.bar(x + w/2, hv, w, label='hw (FSR)', color='#dd8452')
ax3.set_xticks(x); ax3.set_xticklabels(labels, rotation=30, ha='right')
ax3.set_ylabel("Contact frequency (%)")
ax3.set_title("Tactile activation: sim vs hardware (7 FSR channels)")
for i, (a, b) in enumerate(zip(sv, hv)):
    ax3.text(i - w/2, a + 1, f"{a:.0f}%", ha='center', fontsize=8)
    ax3.text(i + w/2, b + 1, f"{b:.0f}%", ha='center', fontsize=8)
ax3.legend(); fig3.tight_layout(); fig3.savefig("/home/nalin/roto/7sensor_ablate_plots/hw_vs_sim_tactile_bars.png", dpi=150)

# ---- Fig 4: tactile raster side-by-side ----
active = sorted(set(
    [i for i in range(24) if stac[:, i].any()] +
    [i for i in range(24) if htac[:, i].any()]
))
fig4, (a4s, a4h) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
a4s.imshow(stac[:, active].T, aspect='auto', cmap='Greys', interpolation='nearest')
a4s.set_yticks(range(len(active))); a4s.set_yticklabels([TAC_NAMES[i] for i in active])
a4s.set_title("Sim tactile raster")
a4h.imshow(htac[:, active].T, aspect='auto', cmap='Greys', interpolation='nearest')
a4h.set_yticks(range(len(active))); a4h.set_yticklabels([TAC_NAMES[i] for i in active])
a4h.set_xlabel("timestep"); a4h.set_title("Hardware tactile raster (FSR-mapped)")
fig4.tight_layout(); fig4.savefig("/home/nalin/roto/7sensor_ablate_plots/hw_vs_sim_tactile_raster.png", dpi=150)

# ---- console summary ----
print(f"Compared {n} steps")
print("\n=== RMS tracking error (deg) ===")
for j, name in enumerate(JOINTS):
    print(f"  {name:5s}  sim {np.degrees(sim_err[j]):5.1f}   hw {np.degrees(hw_err[j]):5.1f}")
print("\n=== Tactile activation (7 FSR channels) ===")
for name, s, h in zip(labels, sv, hv):
    print(f"  {name:10s}  sim {s:5.1f}%   hw {h:5.1f}%")
print("\nsaved hw_vs_sim_*.png")
plt.show()