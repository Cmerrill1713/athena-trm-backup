import re
import unicodedata

PATTERNS = [
    (re.compile(r"\b(issue|issues|problem|problems)\b.*\b(ourself|ourselves|us|system|service|stack)\b", re.I),
     "I can help identify issues. Which area—infra, APIs, data, or UX—first?"),
    (re.compile(r"\bhow\s+are\s+you\b|\bstatus\b|\bhealth\b", re.I),
     "Running fine. What can I do for you right now?"),
    (re.compile(r"\bwhat\s+are\s+you\b|\bwho\s+are\s+you\b", re.I),
     "I'm Athena, your AI assistant. I can debug, analyze logs, and plan fixes. What's the task?"),
    (re.compile(r"\bhelp\b|\bassist\b|\bsupport\b", re.I),
     "I can help with coding, analysis, and troubleshooting. Tell me the goal or paste the error."),
    (re.compile(r"\btest\b|\bpinger\b|\bpong\b", re.I),
     "Test successful—bridge is alive and routing intents."),
    (re.compile(r"\bissue|issues|problem|problems\b", re.I),
     "What issues are you hitting—errors, latency, unexpected behavior, or something else?"),
]

def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).strip().strip("'\"\"''")
    return re.sub(r"\s+", " ", s)

def respond(msg: str) -> str:
    t = normalize(msg)
    for p, ans in PATTERNS:
        if p.search(t): 
            return ans
    return f"I understood: \"{t}\". Should I explain, troubleshoot, or run a check?"
