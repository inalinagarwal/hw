# Dissertation index — Shadow Hand Lite Baoding (sim → real)

Living index for thesis writing. Complements:

| Doc | Purpose |
|-----|---------|
| [`AGENTS.md`](AGENTS.md) | RoTO codebase map for agents/developers |
| [`SHADOWLITE_DEPLOY.md`](SHADOWLITE_DEPLOY.md) | Hardware ROS contract, joints, coupling, tactile map |
| [`docker.md`](docker.md) | Shadow server Docker / hand launch (other lab hand; useful patterns) |
| [`roto_paper_results/CHECKPOINTS.md`](../roto_paper_results/CHECKPOINTS.md) | Published checkpoint references |

**Not auto-maintained** — update this file after each hardware test phase.

---

## 1. Thesis framing (one paragraph)

We train a **blind tactile** (`rl_only_pt`: proprioception + binary tactile, no vision) policy for **Baoding balls** on the **Shadow Hand Lite** in Isaac Sim (RoTO + multimodal_rl), deploy it on the real hand via ROS at 60 Hz, and characterize **sim-to-real gaps** in joint coupling, plant tracking, and tactile contact patterns. Hardware uses **FSRs** (7 pads, mux + Arduino) mapped into the same 24-channel binary tactile vector the policy was trained on. Quantitative diagnostics (coupling violations, tactile activation frequencies, sim vs hardware rollout logs) motivate iterative sensor improvements (more FSRs, BioTac distals) and a planned **pad-aligned contact model** in simulation for retraining.

**Suggested abstract sentence:**  
*We train a blind tactile policy for Baoding in simulation, deploy it on Shadow Hand Lite with FSR sensing, and quantify sim-to-real gaps in finger coupling, command tracking, and contact activation—motivating pad-aligned contact sensing and retraining.*

---

## 2. Phased evaluation roadmap

Each phase uses the **same four plots** (joint overlay, tracking RMS, tactile bars, tactile raster) so results stack in the thesis.

| Phase | Code name | Hardware / sim change | Log file | Plot folder | **What this test answers** |
|-------|-----------|----------------------|----------|-------------|---------------------------|
| **Sim baseline** | — | Trained policy in Isaac (`play.py`) | `sim_policy_log_seed*.npz` | (root / paper figs) | What contact pattern and joint motion does a *successful* policy produce? |
| **0 — 7 FSR** | `v0` | 7 FSRs wired; per-channel threshold + hysteresis; cup start pose | `hw_policy_log.npz` | `7sensor_plots/` | Does zero-shot transfer work? Where do tactile and joints diverge from sim? |
| **1 — Ablation** ✓ | `ablate` | Zero stuck channels in `read_tactile()` (palm ch2, ffprox ch7) | `hw_policy_log_ablate.npz` | `7sensor_ablate_plots/` | Is policy parking caused by *wrong constant tactile* vs plant/coupling? **Done 2026-07-01** |
| **2 — More FSR** | `v1` | Add high-activation gaps (`ffdist`, fix `thprox`, tune palm/ffprox thresholds) | `hw_policy_log_v1.npz` | `12sensor_plots/` | Does better spatial coverage + threshold fixes improve contact rhythm and motion? |
| **3 — BioTac** | `v2` | Binarize `/biotac` taxels → distal channels 15,16,17,22 | `hw_policy_log_v2.npz` | `biotac_plots/` | Do distals (high sim activation) recover rolling contact the FSRs miss? |
| **4 — PadTac retrain** | `v3` | Small collision prims at pad sites in USD; N-channel obs; **new train** | `hw_policy_log_v3.npz` | `padtac_plots/` | If sim contact area matches real pad footprint, does transfer improve without link-level false positives? |

### Per-plot interpretation cheat sheet

| Plot | Filename | Read this as |
|------|----------|--------------|
| Joint trajectories | `hw_vs_sim_joints.png` | Does HW **command** stay flat while sim oscillates? → policy obs mismatch, not weak motors |
| Tracking RMS | `hw_vs_sim_tracking_err.png` | Low HW error + flat cmd = hand tracks well but policy parked |
| Tactile bars | `hw_vs_sim_tactile_bars.png` | Per-channel sim % vs HW % for instrumented sites |
| Tactile raster | `hw_vs_sim_tactile_raster.png` | Temporal contact structure: sim rhythm vs HW stuck/sparse |

**Plot script:** [`plot_hw_vs_sim.py`](plot_hw_vs_sim.py) — point at the right `hw_policy_log_*.npz`.

---

## 3. Schedule (current plan)

| When | Work | Status |
|------|------|--------|
| **Wed** | Tactile ablation → `ablate` logs + plots | **Done** — see §5.4 |
| **Wed** | Fix rfprox stuck ON + add more FSRs → `v1` | Pending |
| **Thu–Fri** | BioTac integration → `v2` logs + plots | Pending |
| **Next week** | Pad collision prims (“VisioTac”) + retrain + `v3` | Pending |

---

## 4. Project timeline (what we did)

| Stage | Outcome |
|-------|---------|
| Index `CHECKPOINTS.md`, `AGENTS.md` | RoTO structure, training paths |
| Train `rl_only_pt` Shadow Lite Baoding | 50M sanity → 250M; `best_agent.pt`; TensorBoard rising returns |
| Fix train/deploy blockers | `num_train_envs`, TensorBoard `setuptools`, `play.py` recording |
| Deployment contract | 352-d obs, joint order, scale/unscale, absolute actions, J1≤J2 clamp |
| Hardware docs | `SHADOWLITE_DEPLOY.md` from Shadow manual |
| First HW deploy (fake tactile) | Policy moved then **parked ~2 s** → fixed-point from constant-zero tactile |
| Rotating-wave tactile stub | Confirmed non-constant tactile restores motion |
| Coupling diagnostic | Open-loop replay; FF **J1>J2 ~75%** of steps in sim (hardware infeasible) |
| Tactile activation (sim) | Bar plot + table; guides FSR placement |
| URDF / coupling | Sim does **not** model mimic; independent J1/J2 in training |
| 7 FSR wiring | Mux Arduino → CSV serial; `deploy_policy.py` calibrate + hysteresis |
| Docker / serial | `dexterous_hand_real_hw` privileged → `/dev/ttyACM0` in container |
| Py2 deploy fixes | `super(Cls,self)`, legacy checkpoint, `daemon` thread, `decode("ascii","ignore")` |
| Cup start pose | `go_to_pose.py`; calibrate empty → place balls → policy |
| **7 FSR closed loop** | Runs but poor; logged → `7sensor_plots/` |
| **Tactile ablation (phase 1)** | Zero palm+ffprox in obs; rfprox stuck 100%; joints still park → `7sensor_ablate_plots/` |

---

## 5. Key quantitative findings

### 5.1 Simulation — tactile activation (pooled rollouts, ~900 steps)

| Channel | Link | Freq % | Notes |
|--------:|------|-------:|-------|
| 10 | thprox | 56.7 | **Top** — must work on HW |
| 15 | ffdist | 38.0 | No FSR yet — BioTac target |
| 9 | rfprox | 35.4 | Only HW channel that ~matched sim |
| 4 | mfknuckle | 33.8 | |
| 11 | ffmid | 23.7 | |
| 7 | ffprox | 0.0 | Sim rarely uses — HW stuck 92% (bad) |
| 2 | palm | 7.4 | HW stuck 100% (cup holding balls) |

Scripts: [`tactile_frequency.py`](tactile_frequency.py), [`tactile_raster.py`](tactile_raster.py) (if present), [`check_coupling.py`](check_coupling.py).

### 5.2 Simulation — J1 > J2 coupling violations (achieved positions)

| Finger | Mean % steps J1>J2 | Per-seed |
|--------|-------------------:|----------|
| FF | 74.9 | 63, 81, 81 |
| MF | 1.3 | 0, 1, 3 |
| RF | 20.2 | 5, 23, 33 |

FF is the main hardware feasibility gap; `min(J1,J2)` clamp distorts FF commands on deploy.

### 5.3 Hardware — 7 FSR vs sim (`7sensor_plots/`, first closed loop)

**Joints:** HW commands **flat after ~25 steps**; sim commands oscillate (Baoding). HW **achieved ≈ commanded** (good tracking, parked policy).

**Tactile (7 instrumented channels):**

| Channel | Sim % | HW % |
|---------|------:|-----:|
| thprox | 57 | **0** |
| ffprox | 0 | **92** |
| mfknuckle | 34 | 7 |
| rfprox | 35 | **47** ✓ |
| rfknuckle | 16 | 0 |
| palm | 7 | **100** |
| ffmid | 24 | 0 |

**Conclusion:** Policy sees near-constant wrong tactile → fixed action. Not primarily “bad mechanical design”—**observation mismatch**.

### 5.4 Hardware — tactile ablation (`7sensor_ablate_plots/`, phase 1)

**Intervention:** In `read_tactile()`, force channels **palm (2)** and **ffprox (7)** to 0 after binarization (remove sim-inconsistent stuck contacts from v0).

**Joints:** HW commands still **flat after ~25 steps** — same parking as v0. Ablation alone did **not** restore Baoding-like oscillation.

**Tactile (logged policy input after ablation):**

| Channel | Sim % | HW v0 | HW ablate | Notes |
|---------|------:|------:|----------:|-------|
| thprox | 57 | 0 | **24** | Improved; raster shows contact only after ~step 200 |
| ffprox | 0 | 92 | **0** | Ablation fixed false positive |
| mfknuckle | 34 | 7 | **0** | Dead this run |
| rfprox | 35 | 47 | **100** | **New stuck channel** — constant ON entire rollout |
| rfknuckle | 16 | 0 | 0 | Dead |
| palm | 7 | 100 | **0** | Ablation removed cup-hold false contact |
| ffmid | 24 | 0 | 1 | Still dead |

**Conclusions:**

1. **Palm/ffprox were harmful** — sim expects 0–8%; v0 had 92–100%. Zeroing them is correct for deploy and for thesis narrative.
2. **Tactile is not the only blocker** — joints still park without palm/ffprox.
3. **rfprox saturation (100%)** likely replaces palm as a near-constant tactile pattern; fix thresholds/mounting before adding FSRs.
4. **Optional follow-up test:** ablate rfprox (ch 9) too, or raise `K_HI` on mux C3 only.

**Thesis sentence:**  
*Ablating persistently active palm and ffprox removed sim-inconsistent contact (92% and 100% → 0%) but did not restore dynamic joint commands; ring proximal remained saturated at 100%, indicating multiple stuck or missing channels must be resolved before the policy receives Baoding-like tactile transients.*

### 5.5 Training vs hardware start pose

| | Simulation | Hardware (current) |
|--|------------|-------------------|
| Finger joints at reset | **0°** + ±11.5° noise | Cup pose (`go_to_pose.py`) — OOD but holds balls |
| Whole-hand tilt | **~15° forward** (root rot in sim) | Fixed by physical mount |
| Balls | Spawned in contact | Placed manually after calibrate |

Sim reset `q[0]` (rad, policy order):  
`[-0.134, -0.037, -0.002, 0.109, 0.114, 0.078, -0.043, 0, 0.084, 0.165, 0.182, 0, 0.088, 0.074, 0.024, -0.230]`

---

## 6. Artifacts catalog

### 6.1 Code (deployment & diagnostics)

| File | Role |
|------|------|
| [`deploy_policy.py`](deploy_policy.py) | ROS deploy: encoder+policy, FSR tactile, logging, 60 Hz loop |
| [`go_to_pose.py`](go_to_pose.py) | Move to cup/start pose before policy (on server) |
| [`read_sensors.py`](read_sensors.py) | FSR monitor: calibrate + live binarized channels (on server) |
| [`resave_legacy.py`](resave_legacy.py) | `best_agent.pt` → PyTorch 1.4–readable format |
| [`plot_hw_vs_sim.py`](plot_hw_vs_sim.py) | Four comparison figures sim vs HW log |
| [`plot_joints.py`](plot_joints.py) | Open-loop replay: sim cmd vs HW achieved |
| [`check_coupling.py`](check_coupling.py) | Aggregate J1>J2 across sim seeds |
| [`scripts/play.py`](scripts/play.py) | Sim eval + `sim_policy_log_seed*.npz` |
| [`scripts/train.py`](scripts/train.py) | Training entry |

### 6.2 Config & policy

| Path | Role |
|------|------|
| `roto/tasks/baoding/agents/shadowlite/rl_only_pt.yaml` | Blind policy agent config |
| `roto/tasks/baoding/agents/shadowlite/default.yaml` | Training budget, env count |
| `scripts/logs/shadowlite_baoding/rl_only_pt/.../best_agent.pt` | Trained weights (GPU box) |
| `best_agent_legacy.pt` | Py2/torch1.4 deploy copy |

### 6.3 Data & figures

| Path | Contents |
|------|----------|
| `sim_policy_log_seed{1,2,3}.npz` | `act`, `q`, `cmd`, `tac` — sim rollouts |
| `hw_replay_log.npz` | Open-loop HW replay (if run) |
| `hw_policy_log.npz` | HW closed-loop v0 |
| `hw_policy_log_ablate.npz` | HW closed-loop phase 1 (palm+ffprox ablated) |
| `7sensor_plots/` | v0 four comparison PNGs |
| `7sensor_ablate_plots/` | ablation four comparison PNGs |
| `tactile_activation.png` / `.pdf` | Sim per-link activation bar chart |
| `coupling_*.png` / `.pdf` | Coupling violation figures |
| `joints_sim_vs_hw.png` | Open-loop joint overlay (if generated) |

### 6.4 FSR hardware map (mux C0–C6 → sim channel)

| Mux | Physical pad | Sim ch | Name |
|-----|--------------|-------:|------|
| C0 | thumb proximal | 10 | thprox |
| C1 | first proximal | 7 | ffprox |
| C2 | middle knuckle | 4 | mfknuckle |
| C3 | ring proximal | 9 | rfprox |
| C4 | ring knuckle | 5 | rfknuckle |
| C5 | palm | 2 | palm |
| C6 | first middle | 11 | ffmid |

Thresholding: `baseline + K·σ` per channel; `K_HI=5`, `K_LO=2` (Schmitt); values **rise** with force.

---

## 7. Sim ↔ real contract (short)

- **Obs:** 352 = 4×(prop 64 + tactile 24); prop = `[pos_norm, vel_norm, cmd_error_raw, last_action]`
- **Action:** absolute normalized joint targets → `scale` → clamp → `J1 ≤ J2` for FF/MF/RF
- **Control:** `/rh_trajectory_controller/command`, trajectory mode, 60 Hz
- **Tactile:** binary per link; HW maps FSR pads into link channels (OR if multiple pads/link)

Full detail: [`SHADOWLITE_DEPLOY.md`](SHADOWLITE_DEPLOY.md) §6–7.

---

## 8. Known sim-to-real gaps (ranked)

1. **Tactile geometry & coverage** — link-level sim vs pad FSR; v0: stuck palm/ffprox; ablate: rfprox stuck 100%; dead thprox/ffmid/mfknuck  
2. **Finger coupling** — sim independent J1/J2; FF policy uses infeasible J1>J2 ~75%  
3. **Start distribution** — flat sim reset + spawned balls vs cup pose + manual place  
4. **Backlash / tendons** — not in sim; hurts oscillatory Baoding  
5. **Whole-hand tilt** — 15° sim root rot vs fixed HW mount  
6. **No domain randomization** in current train run  

---

## 9. Planned fixes (VisioTac / PadTac)

**Idea:** Add **small collision bodies** at each real pad location in USD/URDF; point Isaac `ContactSensorCfg` at those prims only (see Franka pattern in `roto/tasks/robots/franka/franka.py`). Retrain with **N pad channels** (not 24 full links). Hardware: 1:1 pad → channel.

**Requires:** new training run (encoder input dim changes); cannot hot-swap into current `rl_only_pt` checkpoint.

---

## 10. Suggested dissertation chapter outline

1. **Introduction** — dexterous manipulation, Baoding, tactile RL, contributions  
2. **Related work** — sim-to-real, tactile sensing, Shadow Hand  
3. **Simulation setup** — RoTO, Isaac Lab, Shadow Lite, `rl_only_pt`, training results  
4. **Policy & observations** — 352-d vector, frame stack, network architecture  
5. **Hardware system** — Shadow server, ROS, FSR electronics, thresholding pipeline  
6. **Deployment** — action contract, coupling clamp, start pose, checkpoint conversion  
7. **Evaluation methodology** — phased logs, four-plot comparison, open-loop replay  
8. **Results** — sim baselines; coupling stats; tactile activation; v0 closed loop (`7sensor_plots`)  
9. **Iterative improvements** — ablation (`7sensor_ablate_plots`); +FSR; BioTac (fill as completed)  
10. **Discussion** — why transfer fails/partially succeeds; PadTac retrain proposal  
11. **Conclusion & future work** — coupled URDF, DR, longer training  

---

## 11. Completion estimate (thesis-oriented)

| Area | ~% |
|------|---:|
| Sim train + eval | 90 |
| Deploy pipeline + docs | 85 |
| FSR integration | 75 |
| Quantitative sim2real analysis | 85 |
| Phase 1 ablation (logged + plotted) | 100 |
| HW Baoding success (this checkpoint) | 15–25 |
| Thesis writing from existing material | 55–65 |
| **Overall (dissertation-ready story)** | **~68–72** |

---

## 12. Open todos

- [x] Tactile ablation → `hw_policy_log_ablate.npz` + `7sensor_ablate_plots/` (2026-07-01)  
- [ ] Fix **rfprox** stuck ON (per-channel `K_HI` on mux C3, or remount)  
- [ ] More FSRs + threshold tuning → `v1` + `12sensor_plots/`  
- [ ] Thu–Fri: BioTac → `v2` + `biotac_plots/`  
- [ ] Next week: pad prims + retrain + `v3`  
- [ ] Update `SHADOWLITE_DEPLOY.md` §7 (tactile no longer fake; document ablation flag)  
- [ ] Stack v0 / ablate / v1 / v2 tactile bar charts for thesis figure  
- [ ] Write results section from §5.3–5.4 + plots  

---

*Last updated: 2026-07-01 — phase 1 ablation complete.*
