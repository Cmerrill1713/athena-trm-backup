import os

def _env_truthy(*names, default=False):
    vals = {"1", "true", "yes", "on", "y", "t"}
    fals = {"0", "false", "no", "off", "n", "f"}
    for n in names:
        v = os.getenv(n)
        if v is None:
            continue
        s = str(v).strip().lower()
        if s in vals:
            return True
        if s in fals:
            return False
    return default

def getenv_first(*names, default=None):
    for n in names:
        v = os.getenv(n)
        if v is not None:
            return v
    return default

MAINTENANCE = _env_truthy("MAINTENANCE_MODE", "MAINT_MODE", "MAINTENCE_MODE")
DRY_RUN = _env_truthy("DRY_RUN", "DRYRUN", "DRY-RUN")
EMERGENCY = _env_truthy("EMERGENCY_SPIKE_TEST", "EMERGENCY_TEST", "SPIKE_TEST")

AR_HOME = "/home/developer/.local/share/ai-republic"
SPIKE_DIR = getenv_first("SPIKE_SCENARIO_DIR", "SPIKES_DIR", "SPIKE_DIR", f"{AR_HOME}/spikes")

PHASE = getenv_first("BURN_IN_PHASE", "PHASE", default="dry_run")
ALLOWLIST = set((getenv_first("MAINT_ALLOWLIST", default="health,audit,spike_dry_run") or "").split(","))

MUTEX_TTL_S = int(getenv_first("MUTEX_TTL_SECONDS", default="120") or 120)
SPIKE_TO_S = int(getenv_first("SPIKE_TEST_TIMEOUT_SECONDS", default="90") or 90)
