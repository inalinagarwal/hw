import torch

SRC = "/home/nalin/roto/scripts/logs/shadowlite_baoding/rl_only_pt/2026-06-22_16-39-17/checkpoints/best_agent.pt"
DST = "best_agent_legacy.pt"

ckpt = torch.load(SRC, map_location="cpu")
torch.save(ckpt, DST, _use_new_zipfile_serialization=False)
print("wrote", DST)