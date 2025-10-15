#!/usr/bin/swift
// VoiceProof.swift - Definitive test of voice availability

import AVFoundation
import Foundation

let want = "Samantha"
let v = AVSpeechSynthesisVoice.speechVoices()
    .filter { $0.name == want }
    .sorted { $0.quality.rawValue > $1.quality.rawValue }
    .first

if let vv = v {
    print("Will use \(vv.name) [\(vv.identifier)] \(vv.language) q=\(vv.quality.rawValue)")
    let s = AVSpeechSynthesizer()
    let u = AVSpeechUtterance(string: "Samantha proof line. This should sound natural and female, not generic.")
    u.voice = vv
    s.speak(u)
    RunLoop.main.run(until: Date().addingTimeInterval(5))
    print("✅ Speech completed")
} else {
    print("❌ Samantha not installed.")
    exit(1)
}

