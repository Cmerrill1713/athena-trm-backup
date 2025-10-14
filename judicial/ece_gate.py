# judicial/ece_gate.py
def apply_ece_gating(ece_estimate: float, caps: dict, threshold: float = 0.06, actions: list = None):
    actions = actions or []
    if ece_estimate > threshold:
        caps.update({"tot_branches_max": 0, "tot_depth_max": 0})  # PEC-only
        actions.append("QUARANTINE")
    return caps, actions
