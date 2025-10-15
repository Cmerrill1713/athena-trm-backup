-- Athena Launcher AppleScript
-- ============================
--
-- Main launcher application for Athena
-- Provides easy access to all Athena services
--

-- Get the directory where this script is located
set scriptPath to (path to me as text)
set scriptFolder to text 1 thru -((offset of ":" in (reverse of characters of scriptPath) as text) + 1) of scriptPath
set launcherScript to scriptFolder & "athena_launcher.sh"

-- Check if launcher script exists
tell application "System Events"
    if not (exists file launcherScript) then
        display dialog "Error: athena_launcher.sh not found in " & scriptFolder & "

Please ensure the launcher script is in the same directory as this application." buttons {"OK"} default button "OK" with icon stop
        return
    end if
end tell

-- Main menu
set userChoice to choose from list {"Start Athena Frontend", "Start Athena Backend", "Restart All Services", "Stop All Services", "Check Status"} with title "Athena Control Center" with prompt "Select an action:" default items {"Restart All Services"}

if userChoice is false then
    return
end if

set selectedAction to item 1 of userChoice

-- Map menu choices to script actions
if selectedAction is "Start Athena Frontend" then
    set scriptAction to "frontend"
else if selectedAction is "Start Athena Backend" then
    set scriptAction to "backend"
else if selectedAction is "Restart All Services" then
    set scriptAction to "restart"
else if selectedAction is "Stop All Services" then
    set scriptAction to "stop"
else if selectedAction is "Check Status" then
    set scriptAction to "status"
end if

-- Execute the launcher script
try
    set command to "/bin/zsh " & quoted form of POSIX path of launcherScript & " " & scriptAction

    -- For status command, show result in dialog
    if scriptAction is "status" then
        set commandResult to do shell script command
        display dialog "Athena Service Status:" & return & return & commandResult buttons {"OK"} default button "OK" with title "Athena Status"
    else
        -- For other commands, run in background and show progress
        do shell script command & " > /tmp/athena_launcher.log 2>&1 &"

        -- Show progress dialog
        if scriptAction is "restart" then
            display dialog "Athena is restarting..." & return & "This may take a few moments." buttons {"OK"} default button "OK" giving up after 3
        else if scriptAction is "frontend" then
            display dialog "Starting Athena Frontend..." & return & "NeuroForge app will open shortly." buttons {"OK"} default button "OK" giving up after 3
        else if scriptAction is "backend" then
            display dialog "Starting Athena Backend..." & return & "Services will start in background." buttons {"OK"} default button "OK" giving up after 3
        else if scriptAction is "stop" then
            display dialog "Stopping Athena Services..." & return & "All services will be stopped." buttons {"OK"} default button "OK" giving up after 3
        end if
    end if

on error errMsg
    display dialog "Error running Athena launcher:" & return & return & errMsg buttons {"OK"} default button "OK" with icon stop
end try
