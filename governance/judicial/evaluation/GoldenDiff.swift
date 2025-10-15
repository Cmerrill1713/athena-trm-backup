import XCTest
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

enum GoldenDiff {
    struct Result {
        let passed: Bool
        let mismatchRate: Double
        let diffURL: URL?
        let actualURL: URL
        let baselineURL: URL
    }

    // Env overrides (useful in CI or local tuning)
    static var tolerance: Double {
        if let s = ProcessInfo.processInfo.environment["GOLDEN_TOLERANCE"], let v = Double(s) {
            return v
        }
        return 0.0025 // 0.25% of pixels can differ
    }
    static var updateMode: Bool {
        ProcessInfo.processInfo.environment["GOLDEN_UPDATE"] == "1"
    }

    static var baseDir: URL = URL(fileURLWithPath: #file)
        .deletingLastPathComponent() // Golden/
        .deletingLastPathComponent() // UITests/
        .appendingPathComponent("UITests/Golden", isDirectory: true)

    static func ensureDirs() throws {
        let baseline = baseDir.appendingPathComponent("Baseline", isDirectory: true)
        let actual   = baseDir.appendingPathComponent("Actual", isDirectory: true)
        let diffs    = baseDir.appendingPathComponent("Diffs", isDirectory: true)
        try FileManager.default.createDirectory(at: baseline, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: actual,   withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: diffs,    withIntermediateDirectories: true)
    }

    static func path(_ kind: String, name: String) -> URL {
        baseDir.appendingPathComponent(kind, isDirectory: true).appendingPathComponent("\(name).png")
    }

    static func capture(name: String) -> URL {
        let shot = XCUIScreen.main.screenshot()
        let data = shot.pngRepresentation
        let url = path("Actual", name: name)
        try? data.write(to: url, options: .atomic)
        return url
    }

    static func compareOrUpdate(name: String, testCase: XCTestCase, attach: Bool = true) -> Result {
        try? ensureDirs()
        let baselineURL = path("Baseline", name: name)
        let actualURL   = capture(name: name)

        // Update mode: write new baseline and pass
        if updateMode || !FileManager.default.fileExists(atPath: baselineURL.path) {
            try? FileManager.default.removeItem(at: baselineURL)
            try? FileManager.default.copyItem(at: actualURL, to: baselineURL)
            if attach {
                testCase.add(XCTAttachment(contentsOfFile: baselineURL, uniformTypeIdentifier: UTType.png.identifier))
            }
            return .init(passed: true, mismatchRate: 0, diffURL: nil, actualURL: actualURL, baselineURL: baselineURL)
        }

        guard let baseImg = loadRGBA(baselineURL), let actImg = loadRGBA(actualURL),
              baseImg.width == actImg.width, baseImg.height == actImg.height else {
            let diffURL = writeTextDiffImage("SIZE MISMATCH", for: name)
            attachIfNeeded(testCase, baselineURL, actualURL, diffURL, attach)
            return .init(passed: false, mismatchRate: 1.0, diffURL: diffURL, actualURL: actualURL, baselineURL: baselineURL)
        }

        let (rate, diff) = pixelDiff(a: baseImg, b: actImg)
        let passed = rate <= tolerance
        var diffURL: URL? = nil
        if !passed, let d = diff, let png = rasterToPNG(d) {
            diffURL = path("Diffs", name: name)
            try? png.write(to: diffURL!, options: .atomic)
        }

        attachIfNeeded(testCase, baselineURL, actualURL, diffURL, attach)
        return .init(passed: passed, mismatchRate: rate, diffURL: diffURL, actualURL: actualURL, baselineURL: baselineURL)
    }

    // MARK: - Internals

    struct Raster {
        let width: Int
        let height: Int
        var pixels: [UInt8] // RGBA 8-bit
    }

    static func loadRGBA(_ url: URL) -> Raster? {
        guard let src = CGImageSourceCreateWithURL(url as CFURL, nil),
              let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else { return nil }
        let w = cg.width, h = cg.height
        var data = [UInt8](repeating: 0, count: w*h*4)
        guard let ctx = CGContext(data: &data, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w*4,
                                  space: CGColorSpaceCreateDeviceRGB(),
                                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return nil }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
        return .init(width: w, height: h, pixels: data)
    }

    static func pixelDiff(a: Raster, b: Raster) -> (Double, Raster?) {
        precondition(a.width == b.width && a.height == b.height)
        let count = a.width * a.height
        var diffs = [UInt8](repeating: 0, count: count*4)
        var mismatches = 0

        for i in 0..<count {
            let idx = i*4
            let dr = abs(Int(a.pixels[idx])   - Int(b.pixels[idx]))
            let dg = abs(Int(a.pixels[idx+1]) - Int(b.pixels[idx+1]))
            let db = abs(Int(a.pixels[idx+2]) - Int(b.pixels[idx+2]))
            let da = abs(Int(a.pixels[idx+3]) - Int(b.pixels[idx+3]))
            let delta = dr + dg + db + da
            if delta > 8 { // small jitter tolerance per pixel
                mismatches += 1
                // diff highlights in red on white
                diffs[idx]   = 255
                diffs[idx+1] = 0
                diffs[idx+2] = 0
                diffs[idx+3] = 255
            } else {
                diffs[idx]   = 255
                diffs[idx+1] = 255
                diffs[idx+2] = 255
                diffs[idx+3] = 255
            }
        }
        let rate = Double(mismatches) / Double(count)
        return (rate, .init(width: a.width, height: a.height, pixels: diffs))
    }

    static func rasterToPNG(_ r: Raster) -> Data? {
        guard let ctx = CGContext(data: UnsafeMutableRawPointer(mutating: r.pixels),
                                  width: r.width, height: r.height, bitsPerComponent: 8, bytesPerRow: r.width*4,
                                  space: CGColorSpaceCreateDeviceRGB(),
                                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue),
              let cg = ctx.makeImage(),
              let dst = CGImageDestinationCreateWithData(MutableData() as CFMutableData, UTType.png.identifier as CFString, 1, nil) else { return nil }
        CGImageDestinationAddImage(dst, cg, nil)
        guard CGImageDestinationFinalize(dst) else { return nil }
        let data = dst as AnyObject
        // Hack to pull the CFMutableData bytes:
        if let out = data.value(forKey: "data") as? Data { return out }
        return nil
    }

    static func writeTextDiffImage(_ text: String, for name: String) -> URL? {
        let url = path("Diffs", name: name)
        let size = CGSize(width: 800, height: 200)
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        guard let ctx = CGContext(data: nil, width: Int(size.width), height: Int(size.height),
                                  bitsPerComponent: 8, bytesPerRow: 0, space: colorSpace,
                                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return nil }
        ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        ctx.fill(CGRect(origin: .zero, size: size))
        // no text drawing without CoreText – just leave blank panel
        guard let cg = ctx.makeImage(),
              let dst = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else { return nil }
        CGImageDestinationAddImage(dst, cg, nil)
        CGImageDestinationFinalize(dst)
        return url
    }

    static func attachIfNeeded(_ tc: XCTestCase, _ baseline: URL, _ actual: URL, _ diff: URL?, _ attach: Bool) {
        guard attach else { return }
        [("baseline", baseline), ("actual", actual), ("diff", diff)].forEach { label, url in
            guard let url = url else { return }
            let a = XCTAttachment(contentsOfFile: url, uniformTypeIdentifier: UTType.png.identifier)
            a.name = "golden-\(label)"
            a.lifetime = .keepAlways
            tc.add(a)
        }
    }
}

private final class MutableData: NSMutableData {}
