// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NeuroForgeApp",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "NeuroForgeApp", targets: ["NeuroForgeApp"])
    ],
    targets: [
        .executableTarget(
            name: "NeuroForgeApp",
            path: "Sources",
            resources: [
                .process("../Resources"),
                .process("../Resources/Assets.xcassets")
            ],
            swiftSettings: [
                .unsafeFlags(["-parse-as-library"])
            ]
        ),
        .testTarget(
            name: "NeuroForgeAppTests",
            dependencies: ["NeuroForgeApp"],
            path: "Tests"
        )
    ]
)
