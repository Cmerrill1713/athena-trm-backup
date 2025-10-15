// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AthenaPopoutDemo",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "AthenaPopoutDemo",
            targets: ["AthenaPopoutDemo"]
        )
    ],
    targets: [
        .executableTarget(
            name: "AthenaPopoutDemo",
            swiftSettings: [
                .unsafeFlags(["-parse-as-library"])
            ]
        )
    ]
)
