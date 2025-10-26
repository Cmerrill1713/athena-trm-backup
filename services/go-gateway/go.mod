module github.com/athena/go-gateway

go 1.21

require (
	google.golang.org/grpc v1.60.1
	google.golang.org/protobuf v1.32.0
	go.opentelemetry.io/otel v1.21.0
	go.opentelemetry.io/otel/trace v1.21.0
	golang.org/x/time v0.5.0  // For rate limiting
)

