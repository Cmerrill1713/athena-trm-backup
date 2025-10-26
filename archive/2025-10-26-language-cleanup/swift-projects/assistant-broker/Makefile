.PHONY: build run install-agent uninstall-agent logs token help

help:
	@echo "Assistant Broker - Commands"
	@echo "============================"
	@echo "build           - Build release binary"
	@echo "run             - Run broker locally (generates token if not set)"
	@echo "install-agent   - Install LaunchAgent (generates token)"
	@echo "uninstall-agent - Remove LaunchAgent"
	@echo "logs            - Tail broker logs"
	@echo "token           - Generate new random token"
	@echo ""

build:
	swift build -c release

token:
	@openssl rand -hex 32

run: build
	@if [ -z "$$ASSISTANT_BROKER_TOKEN" ]; then \
		export ASSISTANT_BROKER_TOKEN=$$(openssl rand -hex 32); \
		echo "🔑 Generated token: $$ASSISTANT_BROKER_TOKEN"; \
		echo "   Save this token and use it in API calls with X-Assistant-Token header"; \
		echo ""; \
	fi; \
	.build/release/assistant-broker serve

install-agent: build
	@echo "🔑 Generating secure token..."
	@TOKEN=$$(openssl rand -hex 32); \
	sed "s/CHANGE_ME_TO_RANDOM_TOKEN/$$TOKEN/" scripts/com.neuroforge.assistant-broker.plist > /tmp/assistant-broker.plist; \
	mkdir -p ~/Library/LaunchAgents; \
	cp /tmp/assistant-broker.plist ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist; \
	rm /tmp/assistant-broker.plist; \
	launchctl unload ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist 2>/dev/null || true; \
	launchctl load  ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist; \
	echo "✅ Broker installed with token: $$TOKEN"; \
	echo "   Save this token to ~/.assistant-broker-token or set ASSISTANT_BROKER_TOKEN"; \
	echo "   Use X-Assistant-Token: $$TOKEN in all API requests"; \
	echo ""; \
	echo "📋 Grant permissions if prompted:"; \
	echo "   System Settings → Privacy & Security → Automation → assistant-broker"; \
	echo "   System Settings → Privacy & Security → Accessibility → assistant-broker"

uninstall-agent:
	launchctl unload ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist || true
	rm -f ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist

logs:
	tail -f ~/Library/Logs/AssistantBroker.out.log ~/Library/Logs/AssistantBroker.err.log
