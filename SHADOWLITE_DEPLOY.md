# Shadow Hand Lite — Deployment & Hardware Reference

Sources: *Shadow Dexterous Hand Lite* manual (Release 2.1.4) + RoTO sim code.
Companion to `deploy_policy.py`.

> Page numbers are the **printed** numbers in the manual; your PDF viewer may be offset by
> front matter (title/TOC). Mechanical-section pages are confirmed by direct read; ROS-chapter
> pages are approximate.

---

## 1. ROS interface

| Topic | Dir | Type | Notes | Doc |
|-------|-----|------|-------|-----|
| `/joint_states` | read, 100 Hz | `sensor_msgs/JointState` | name/position/velocity/effort for **all** joints (incl. LF, WR, THJ3); **radians** & rad/s | ≈ p.37 |
| `/rh_trajectory_controller/command` | write | `trajectory_msgs/JointTrajectory` | set positions in **radians**; accepts a subset of joints | p.41 |
| `/sh_rh_*_position_controller/command` | write | per-joint position controllers (incl. `ffj0`) | alternative to trajectory controller | — |
| `/calibrated`, `/cal_sh_rh_*/calibrated` | read | startup calibration status | ≈ p.37 |

- **Units: radians everywhere** for the controllers.
- The trajectory controller interpolates with a quintic spline at 1 ms.
- `/joint_states` reports `J1` and `J2` **separately** (independent Hall sensors), even though
  they are mechanically coupled (see §3).

---

## 2. Joints, order & limits (authoritative)

Policy obs/action channel order — taken from the sim `actuated_dof_indices` dump.
**It is breadth-first by joint level, NOT per-finger.**

| ch | joint | lo (rad) | hi (rad) | vel | ch | joint | lo (rad) | hi (rad) | vel |
|---:|-------|---------:|---------:|----:|---:|-------|---------:|---------:|----:|
| 0 | FFJ4 | -0.3491 | 0.3491 | 2.0 | 8  | FFJ2 | 0.0     | 1.5708 | 2.0 |
| 1 | MFJ4 | -0.3491 | 0.3491 | 2.0 | 9  | MFJ2 | 0.0     | 1.5708 | 2.0 |
| 2 | RFJ4 | -0.3491 | 0.3491 | 2.0 | 10 | RFJ2 | 0.0     | 1.5708 | 2.0 |
| 3 | THJ5 | -1.0472 | 1.0472 | 4.0 | 11 | FFJ1 | 0.0     | 1.5708 | 2.0 |
| 4 | FFJ3 | -0.2618 | 1.5708 | 2.0 | 12 | MFJ1 | 0.0     | 1.5708 | 2.0 |
| 5 | MFJ3 | -0.2618 | 1.5708 | 2.0 | 13 | RFJ1 | 0.0     | 1.5708 | 2.0 |
| 6 | RFJ3 | -0.2618 | 1.5708 | 2.0 | 14 | THJ2 | -0.6981 | 0.6981 | 2.0 |
| 7 | THJ4 | 0.0     | 1.2217 | 4.0 | 15 | THJ1 | -0.2618 | 1.5708 | 4.0 |

Ranges match the manual's Ranges table (p.65–67).

---

## 3. J0 coupling ("mimic") — §6.3.2 (p.65), §6.6.1 (p.68)

- On FF/MF/RF, the distal (J1) and middle (J2) joints are driven by **one motor** as
  **J0 = J1 + J2** (loopback tendon).
- Hard constraint **J1 ≤ J2** ("middle ≥ distal"); flexing J1 beyond J2 forces J2 to flex.
  As J0 increases, the middle bends first while the distal stays straighter.
- `/joint_states` and the trajectory controller expose J1/J2 **separately**, but the constraint
  still binds — you cannot realize arbitrary independent (J1, J2).
- **Thumb is fully independent** (5 DOF, no coupling). THJ3 is fixed.
- Deploy handling: `target[J1] = min(target[J1], target[J2])` for each finger (see `COUPLED_PAIRS`).

---

## 4. Backlash — p.62

- Tendons have **slack**; when a motor reverses direction there is a dead period while the spool
  winds in the slack ("backlash"). Firmware drives full power on torque-demand sign change to
  compensate (imperfect).
- Slack grows over time → re-tension tendons (§6.7.4); behavior varies per finger.
- **Impact:** Baoding is oscillatory (constant direction reversals) → backlash is one of the
  larger sim-to-real gaps (sim had none).

---

## 5. Calibration — §5.4.8 (p.31); topics ≈ p.37

- Raw ADC → radians via host calibration tables. Re-calibrate via the Advanced Hand Calibration
  plugin (must be run on the NUC).
- Wait for `/calibrated == True` before commanding.

---

## 6. Sim ↔ real observation / action contract

- **Control loop: 60 Hz** (sim: physics 240 Hz, decimation 4).
- Observation = `{policy: {prop, tactile}}`, frame-stacked ×4, flattened to **352**:
  - layout (oldest → newest, prop before tactile):
    `[prop_t-3(64) | prop_t-2 | prop_t-1 | prop_t | tac_t-3(24) | tac_t-2 | tac_t-1 | tac_t]`
    = prop(256) + tactile(96) = **352**.
- **prop per step (64)** = `[pos_norm(16), vel_norm(16), cmd_error_raw(16), last_action(16)]`:
  - `pos_norm = unscale(q, lo, hi)` ∈ [-1, 1]
  - `vel_norm = q_dot / vel_limit` (per-joint; the sim `/3.0` line is dead code — do not use it)
  - `cmd_error = last_command - q` in **raw radians** (NOT normalized)
  - `last_action` = previous normalized policy output (~[-1, 1])
- **Action (16)** = absolute normalized joint targets:
  - `q_target = scale(a, lo, hi)`; clamp to `[lo, hi]`; then apply J1 ≤ J2.
- The encoder has **no** state preprocessor — feed the raw normalized obs directly.
- For inference you only need **encoder + policy**. `value`, `value_preprocessor`, and the
  `*_optimiser` entries in the checkpoint are training-only.
- Use the policy **mean** (deterministic), no sampling.

---

## 7. Tactile — 24 binary channels (sim body order)

| idx | body | use | idx | body | use |
|----:|------|-----|----:|------|-----|
| 0 | world | 0 | 12 | rh_mfmiddle | FSR |
| 1 | rh_forearm | 0 | 13 | rh_rfmiddle | FSR |
| 2 | rh_palm | FSR (OR pads) | 14 | rh_thhub | 0 |
| 3 | rh_ffknuckle | 0 | 15 | rh_ffdistal | FSR |
| 4 | rh_mfknuckle | 0 | 16 | rh_mfdistal | FSR |
| 5 | rh_rfknuckle | 0 | 17 | rh_rfdistal | FSR |
| 6 | rh_thbase | FSR (opt) | 18 | rh_thmiddle | FSR |
| 7 | rh_ffproximal | FSR | 19 | rh_fftip | 0 |
| 8 | rh_mfproximal | FSR | 20 | rh_mftip | 0 |
| 9 | rh_rfproximal | FSR | 21 | rh_rftip | 0 |
| 10 | rh_thproximal | FSR | 22 | rh_thdistal | FSR |
| 11 | rh_ffmiddle | FSR | 23 | rh_thtip | 0 |

- Resolution is **per link**: OR all FSR pads on one link into that single channel.
- Binarize each pad with a per-pad threshold above its noise floor (sim used "any force > 0").
- Channels marked `0` (world/forearm/knuckles/hub/tips) were ~always 0 in sim → leave 0.
- Currently `read_tactile()` returns zeros (FAKE) → policy runs blind to contact (OOD); replace
  with the FSR source once wired.

---

## 8. Sim-to-real gaps / open items

- **Tactile**: currently fake zeros; even once wired, the 16-FSR → per-link-binary mapping is
  lossy (partial coverage). This is the policy's only contact sense.
- **Coupling (J1 ≤ J2)**: sim treated J1/J2 as independent.
- **Backlash / tendon slack**: sim had none — worst for oscillatory Baoding.
- **Dynamics**: PD/actuator mismatch (sim implicit actuator vs tendon motors); ball
  mass/size/friction differences.
- **Morphology**: the real hand has a **little finger**, wrist, and THJ3 that the sim Shadow Lite
  does not; the uncontrolled little finger is physically present during Baoding.
- **No domain randomization** in the current training → likely brittle.

**Recommended path:** zero-shot bring-up + calibration (~1–2 weeks) → if not converging, retrain
in sim with domain randomization (coupled 13-DOF action, tactile noise model, backlash/latency,
randomized ball params) → redeploy and fine-tune.

---

## 9. Checkpoint

- Trained (250M, blind `rl_only_pt`): `mean_returns` ~176 / `num_rotations` ~19–24.
- Location on the GPU box:
  `scripts/logs/shadowlite_baoding/rl_only_pt/<timestamp>/checkpoints/best_agent.pt`
- Copy to the control laptop and set `CHECKPOINT` in `deploy_policy.py`.
- Must be run with the matching `rl_only_pt` obs config (prop + tactile, stack 4).
