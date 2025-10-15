#!/usr/bin/env bash
set -euo pipefail

ROOT="${PWD}"
BROKER_DIR="$ROOT/assistant-broker"
SCRIPTS_DIR="$ROOT/scripts"
mkdir -p "$BROKER_DIR/Sources/AssistantBroker" "$BROKER_DIR/scripts" "$SCRIPTS_DIR"

# ---------- Swift Package ----------
cat > "$BROKER_DIR/Package.swift" <<'SWIFT'
// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AssistantBroker",
    platforms: [.macOS(.v13)],
    products: [.executable(name: "assistant-broker", targets: ["AssistantBroker"])],
    dependencies: [
        .package(url: "https://github.com/vapor/vapor.git", from: "4.92.0")
    ],
    targets: [
        .executableTarget(
            name: "AssistantBroker",
            dependencies: [.product(name: "Vapor", package: "vapor")],
            swiftSettings: [.unsafeFlags(["-cross-module-optimization"], .when(configuration: .release))]
        )
    ]
)
SWIFT

# ---------- Broker main.swift ----------
cat > "$BROKER_DIR/Sources/AssistantBroker/main.swift" <<'SWIFT'
import Vapor
import Foundation
import AppKit

struct OpenAppReq: Content { let bundle_id: String }
struct QuitAppReq: Content { let bundle_id: String; let force: Bool? }
struct RunReq: Content { let cmd: String; let args: [String] }
struct WriteFileReq: Content { let path: String; let content: String }
struct ReadFileReq: Content { let path: String }

let ALLOWED_CMDS: Set<String> = ["open","osascript","xcrun","xcodebuild"]
let ALLOWED_DIRS: [String] = [
    FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Desktop").path,
    FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Documents").path
]

func isAllowedPath(_ path: String) -> Bool {
    let p = (path as NSString).standardizingPath
    return ALLOWED_DIRS.contains { p.hasPrefix($0) }
}

func routes(_ app: Application) throws {
    app.get("v1","health") { _ in ["status":"ok"] }

    app.post("v1","open_app") { req async throws -> [String:String] in
        let b = try req.content.decode(OpenAppReq.self)
        guard NSWorkspace.shared.urlForApplication(withBundleIdentifier: b.bundle_id) != nil else {
            throw Abort(.notFound, reason: "Bundle id not found")
        }
        NSWorkspace.shared.launchApplication(withBundleIdentifier: b.bundle_id,
                                             options: [.default],
                                             additionalEventParamDescriptor: nil,
                                             launchIdentifier: nil)
        return ["ok":"true"]
    }

    app.post("v1","quit_app") { req async throws -> [String:String] in
        let b = try req.content.decode(QuitAppReq.self)
        let running = NSRunningApplication.runningApplications(withBundleIdentifier: b.bundle_id)
        guard !running.isEmpty else { throw Abort(.notFound, reason: "App not running") }
        for appx in running {
            _ = (b.force == true) ? appx.forceTerminate() : appx.terminate()
        }
        return ["ok":"true"]
    }

    app.post("v1","run") { req async throws -> [String:String] in
        let b = try req.content.decode(RunReq.self)
        guard ALLOWED_CMDS.contains(b.cmd) else { throw Abort(.forbidden, reason: "Command not allowed") }
        let task = Process()
        task.launchPath = "/usr/bin/env"
        task.arguments = [b.cmd] + b.args
        let pipe = Pipe(); task.standardOutput = pipe; task.standardError = pipe
        try task.run(); task.waitUntilExit()
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        let out = String(data: data, encoding: .utf8) ?? ""
        return ["ok": String(task.terminationStatus == 0), "out": out]
    }

    app.post("v1","write_file") { req async throws -> [String:String] in
        let b = try req.content.decode(WriteFileReq.self)
        guard isAllowedPath(b.path) else { throw Abort(.forbidden, reason: "Path not allowed") }
        try b.content.data(using: .utf8)?.write(to: URL(fileURLWithPath: b.path))
        return ["ok":"true"]
    }

    app.post("v1","read_file") { req async throws -> [String:String] in
        let b = try req.content.decode(ReadFileReq.self)
        guard isAllowedPath(b.path) else { throw Abort(.forbidden, reason: "Path not allowed") }
        let txt = try String(contentsOfFile: b.path, encoding: .utf8)
        return ["ok":"true","content":txt]
    }
}

@main
struct Main {
    static func main() throws {
        var env = try Environment.detect()
        try LoggingSystem.bootstrap(from: &env)
        let app = Application(env)
        defer { app.shutdown() }
        try routes(app)
        try app.run()
    }
}
SWIFT

# ---------- LaunchAgent plist ----------
USER_NAME="$(id -un)"
cat > "$BROKER_DIR/scripts/com.neuroforge.assistant-broker.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.neuroforge.assistant-broker</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/$USER_NAME/Documents/GitHub/assistant-broker/.build/release/assistant-broker</string>
    <string>serve</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PORT</key><string>8080</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/Users/$USER_NAME/Library/Logs/AssistantBroker.out.log</string>
  <key>StandardErrorPath</key><string>/Users/$USER_NAME/Library/Logs/AssistantBroker.err.log</string>
</dict>
</plist>
PLIST

# ---------- Broker Makefile ----------
cat > "$BROKER_DIR/Makefile" <<'MK'
.PHONY: build run install-agent uninstall-agent logs
build:
	swift build -c release
run: build
	.build/release/assistant-broker serve
install-agent: build
	mkdir -p ~/Library/LaunchAgents
	cp scripts/com.neuroforge.assistant-broker.plist ~/Library/LaunchAgents/
	launchctl unload ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist 2>/dev/null || true
	launchctl load  ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist
	@echo "Broker installed. Give Accessibility/Automation permissions if prompted."
uninstall-agent:
	launchctl unload ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist || true
	rm -f ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist
logs:
	tail -f ~/Library/Logs/AssistantBroker.out.log ~/Library/Logs/AssistantBroker.err.log
MK

# ---------- Build/Package scripts ----------
cat > "$SCRIPTS_DIR/build_swift_app.sh" <<'SH2'
#!/usr/bin/env bash
set -euo pipefail
APP_NAME="${1:?app name}"
PROJ_DIR="${2:?xcodeproj or swift package dir}"
OUT="$HOME/Desktop/Builds/$APP_NAME/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
pushd "$PROJ_DIR" >/dev/null
if [ -f "Package.swift" ]; then
  swift build -c release
  APP_PATH=".build/release/$APP_NAME.app"
else
  xcodebuild -scheme "$APP_NAME" -configuration Release -derivedDataPath .derived | xcpretty || true
  APP_PATH=".derived/Build/Products/Release/$APP_NAME.app"
fi
test -d "$APP_PATH" || { echo "Build failed: $APP_PATH missing" >&2; exit 1; }
cp -R "$APP_PATH" "$OUT/"
echo "$OUT/$APP_NAME.app"
SH2
chmod +x "$SCRIPTS_DIR/build_swift_app.sh"

cat > "$SCRIPTS_DIR/package_dmg.sh" <<'SH3'
#!/usr/bin/env bash
set -euo pipefail
APP_PATH="${1:?path to .app}"
DMG_PATH="$(dirname "$APP_PATH")/$(basename "$APP_PATH" .app).dmg"
hdiutil create -volname "$(basename "$APP_PATH" .app)" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"
shasum -a 256 "$DMG_PATH" > "${DMG_PATH}.sha256"
echo "$DMG_PATH"
SH3
chmod +x "$SCRIPTS_DIR/package_dmg.sh"

# ---------- Top-level Make glue (idempotent) ----------
if [ ! -f "$ROOT/Makefile" ] || ! rg -q '^# --- Broker Targets ---$' "$ROOT/Makefile" 2>/dev/null; then
cat >> "$ROOT/Makefile" <<'MK2'

# --- Broker Targets ---
.PHONY: broker broker-run broker-agent broker-uninstall broker-logs \
        build-swift package-dmg deliver-open

broker:
	$(MAKE) -C assistant-broker build
broker-run:
	$(MAKE) -C assistant-broker run
broker-agent:
	$(MAKE) -C assistant-broker install-agent
broker-uninstall:
	$(MAKE) -C assistant-broker uninstall-agent
broker-logs:
	$(MAKE) -C assistant-broker logs

# Build & package helpers
build-swift:
	@./scripts/build_swift_app.sh "$(NAME)" "$(PROJ)"
package-dmg:
	@./scripts/package_dmg.sh "$(APP)"
deliver-open:
	@curl -s -X POST http://127.0.0.1:8080/v1/run \
	  -H 'content-type: application/json' \
	  -d '{"cmd":"open","args":["$(PATH)"]}' >/dev/null || true
MK2
fi

echo "[OK] Broker scaffolded at $BROKER_DIR"

