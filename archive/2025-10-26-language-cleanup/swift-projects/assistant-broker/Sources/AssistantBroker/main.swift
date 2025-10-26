import Vapor
import Foundation
import AppKit

struct OpenAppReq: Content { let bundle_id: String }
struct QuitAppReq: Content { let bundle_id: String; let force: Bool? }
struct RunReq: Content { let cmd: String; let args: [String] }
struct WriteFileReq: Content { let path: String; let content: String }
struct ReadFileReq: Content { let path: String }

// Security: Shared secret token
let BROKER_TOKEN = ProcessInfo.processInfo.environment["ASSISTANT_BROKER_TOKEN"] ?? ""

let ALLOWED_CMDS: Set<String> = ["open", "osascript", "xcrun", "xcodebuild"]
let ALLOWED_DIRS: [String] = [
    FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Desktop").path,
    FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Documents").path
]

func isAllowedPath(_ path: String) -> Bool {
    let p = (path as NSString).standardizingPath
    return ALLOWED_DIRS.contains { p.hasPrefix($0) }
}

// Token Authentication Middleware
struct TokenAuthMiddleware: Middleware {
    let token: String
    
    func respond(to request: Request, chainingTo next: Responder) -> EventLoopFuture<Response> {
        // Allow health check without auth
        if request.url.path.hasSuffix("/v1/health") {
            return next.respond(to: request)
        }
        
        guard request.headers.first(name: "X-Assistant-Token") == token else {
            request.logger.warning("Unauthorized request from \(request.remoteAddress?.description ?? "unknown")")
            return request.eventLoop.makeFailedFuture(Abort(.unauthorized, reason: "Missing or invalid X-Assistant-Token header"))
        }
        
        return next.respond(to: request)
    }
}

func routes(_ app: Application) throws {
    app.get("v1","health") { _ in ["status":"ok"] }

    app.post("v1","open_app") { req async throws -> [String:String] in
        let b = try req.content.decode(OpenAppReq.self)
        guard NSWorkspace.shared.urlForApplication(withBundleIdentifier: b.bundle_id) != nil else {
            throw Abort(.notFound, reason: "Bundle ID '\(b.bundle_id)' not found. Find bundle ID with: osascript -e 'id of app \"AppName\"'")
        }
        NSWorkspace.shared.launchApplication(withBundleIdentifier: b.bundle_id,
                                             options: [.default],
                                             additionalEventParamDescriptor: nil,
                                             launchIdentifier: nil)
        req.logger.info("Opened app: \(b.bundle_id)")
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
        guard ALLOWED_CMDS.contains(b.cmd) else {
            let allowed = ALLOWED_CMDS.sorted().joined(separator: ", ")
            throw Abort(.forbidden, reason: "Command '\(b.cmd)' not allowed. Allowed: \(allowed)")
        }
        req.logger.info("Running command: \(b.cmd) \(b.args.joined(separator: " "))")
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
        guard isAllowedPath(b.path) else {
            let allowed = ALLOWED_DIRS.joined(separator: ", ")
            throw Abort(.forbidden, reason: "Path '\(b.path)' not allowed. Allowed directories: \(allowed)")
        }
        try b.content.data(using: .utf8)?.write(to: URL(fileURLWithPath: b.path))
        req.logger.info("Wrote file: \(b.path)")
        return ["ok":"true"]
    }

    app.post("v1","read_file") { req async throws -> [String:String] in
        let b = try req.content.decode(ReadFileReq.self)
        guard isAllowedPath(b.path) else {
            let allowed = ALLOWED_DIRS.joined(separator: ", ")
            throw Abort(.forbidden, reason: "Path '\(b.path)' not allowed. Allowed directories: \(allowed)")
        }
        let txt = try String(contentsOfFile: b.path, encoding: .utf8)
        req.logger.info("Read file: \(b.path)")
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
        
        // Security: Bind to localhost only
        app.http.server.configuration.hostname = "127.0.0.1"
        
        // Security: Require token authentication (except health check)
        if !BROKER_TOKEN.isEmpty {
            app.middleware.use(TokenAuthMiddleware(token: BROKER_TOKEN))
            app.logger.notice("✅ Token authentication ENABLED")
        } else {
            app.logger.warning("⚠️  Token authentication DISABLED - set ASSISTANT_BROKER_TOKEN environment variable")
        }
        
        try routes(app)
        app.logger.notice("🚀 Assistant Broker ready on http://\(app.http.server.configuration.hostname):\(app.http.server.configuration.port)")
        try app.run()
    }
}
