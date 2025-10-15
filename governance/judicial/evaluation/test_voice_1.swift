#!/usr/bin/swift
import AVFoundation

print("🎤 Testing Voice Resolution")
print("==========================")
print("")

// List all available voices
print("📋 Available voices:")
let voices = AVSpeechSynthesisVoice.speechVoices()
for voice in voices.prefix(10) {
    print("   \(voice.name) [\(voice.identifier)] (\(voice.language)) q=\(voice.quality.rawValue)")
}
print("   ... (\(voices.count) total voices)")
print("")

// Try to find Samantha
print("🔍 Looking for Samantha...")
let samanthaByName = voices.first(where: { $0.name == "Samantha" })
if let v = samanthaByName {
    print("   ✅ Found by name: \(v.name) [\(v.identifier)] quality=\(v.quality.rawValue)")
} else {
    print("   ❌ Not found by name")
}

// Try by identifier
let samanthaById = AVSpeechSynthesisVoice(identifier: "com.apple.ttsbundle.Samantha-compact")
if let v = samanthaById {
    print("   ✅ Found by ID: \(v.name) [\(v.identifier)] quality=\(v.quality.rawValue)")
} else {
    print("   ❌ Not found by ID: com.apple.ttsbundle.Samantha-compact")
}

print("")
print("🗣️  Testing speech...")
if let v = samanthaByName ?? samanthaById {
    let utt = AVSpeechUtterance(string: "This is Athena. Testing Samantha's voice.")
    utt.voice = v
    print("   Using voice: \(v.name) [\(v.identifier)]")
    let synth = AVSpeechSynthesizer()
    synth.speak(utt)
    sleep(5)
    print("   ✅ Speech completed")
} else {
    print("   ❌ Cannot test - Samantha not available")
}

