// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NeuroForgeApp",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "NeuroForgeApp",
            targets: ["NeuroForgeApp"]
        )
    ],
    targets: [
        .executableTarget(
            name: "NeuroForgeApp",
            path: "Sources",
            swiftSettings: [
                .unsafeFlags(["-parse-as-library"])
            ]
        )
    ]
)
