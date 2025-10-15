#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/notify_iphone.sh "+15551234567" "Your message here"
DEST="${1:?Provide your E.164 phone number or Apple ID iMessage address}"
MSG="${2:?Provide a message body}"

# AppleScript will try iMessage; if no buddy, it creates a new chat with DEST
osascript - "$DEST" "$MSG" <<'APPLESCRIPT'
on run argv
  set theDest to item 1 of argv
  set theMsg to item 2 of argv

  tell application "Messages"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy theDest of targetService
    send theMsg to targetBuddy
  end tell
end run
APPLESCRIPT
