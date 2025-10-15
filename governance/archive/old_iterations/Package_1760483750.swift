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
