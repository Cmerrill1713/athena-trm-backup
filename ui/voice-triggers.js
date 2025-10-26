/**
 * Athena Voice Triggers
 * Wake word detection + push-to-talk + continuous listening
 * 100% LOCAL - uses Web Speech API or local Whisper
 */

class VoiceTriggers {
    constructor() {
        this.isListening = false;
        this.isPushToTalkActive = false;
        this.wakeWordEnabled = false;
        this.recognition = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        // Configuration
        this.wakeWords = ['hey athena', 'hi athena', 'okay athena', 'athena'];
        this.whisperUrl = 'http://localhost:8095';
        this.useWebSpeech = true;  // Fallback to local Whisper if false
        
        this.initializeVoice();
    }
    
    initializeVoice() {
        // Try Web Speech API first (built into browser, offline)
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            
            this.recognition.onresult = (event) => this.handleSpeechResult(event);
            this.recognition.onerror = (event) => this.handleSpeechError(event);
            this.recognition.onend = () => {
                if (this.wakeWordEnabled || this.isPushToTalkActive) {
                    this.recognition.start();  // Restart if still active
                }
            };
            
            console.log('🎤 Web Speech API initialized (offline)');
            this.useWebSpeech = true;
        } else {
            console.log('⚠️ Web Speech API not available, will use local Whisper');
            this.useWebSpeech = false;
        }
    }
    
    handleSpeechResult(event) {
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join(' ')
            .toLowerCase();
        
        // Check for wake word
        if (this.wakeWordEnabled && !this.isListening) {
            const hasWakeWord = this.wakeWords.some(word => transcript.includes(word));
            
            if (hasWakeWord) {
                console.log('🔊 Wake word detected!');
                this.onWakeWordDetected();
                
                // Extract command after wake word
                const commandPart = transcript.split(/hey athena|hi athena|okay athena|athena/i)[1];
                if (commandPart && commandPart.trim()) {
                    this.onTranscript(commandPart.trim());
                }
            }
        } else if (this.isPushToTalkActive) {
            // Push-to-talk mode - send all speech
            const lastResult = event.results[event.results.length - 1];
            if (lastResult.isFinal) {
                this.onTranscript(lastResult[0].transcript);
            }
        }
    }
    
    handleSpeechError(event) {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
            alert('Microphone access denied. Please allow microphone access for voice features.');
        }
    }
    
    // Enable wake word listening
    enableWakeWord() {
        if (!this.useWebSpeech) {
            alert('Wake word requires Web Speech API (offline). Not available in this browser.');
            return false;
        }
        
        this.wakeWordEnabled = true;
        this.recognition.start();
        console.log('🔊 Wake word listening enabled');
        return true;
    }
    
    // Disable wake word listening
    disableWakeWord() {
        this.wakeWordEnabled = false;
        if (this.recognition && !this.isPushToTalkActive) {
            this.recognition.stop();
        }
        console.log('🔇 Wake word listening disabled');
    }
    
    // Start push-to-talk
    async startPushToTalk() {
        if (this.useWebSpeech) {
            // Use Web Speech API
            this.isPushToTalkActive = true;
            if (!this.recognition.started) {
                this.recognition.start();
            }
        } else {
            // Use local Whisper
            await this.startWhisperRecording();
        }
        
        console.log('🎤 Push-to-talk started');
    }
    
    // Stop push-to-talk
    async stopPushToTalk() {
        if (this.useWebSpeech) {
            this.isPushToTalkActive = false;
            if (!this.wakeWordEnabled) {
                this.recognition.stop();
            }
        } else {
            // Stop Whisper recording
            await this.stopWhisperRecording();
        }
        
        console.log('🎤 Push-to-talk stopped');
    }
    
    // Whisper recording (fallback when Web Speech unavailable)
    async startWhisperRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.audioChunks = [];
            this.mediaRecorder = new MediaRecorder(stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                await this.transcribeWithWhisper(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };
            
            this.mediaRecorder.start();
            console.log('🎤 Whisper recording started');
            
        } catch (error) {
            console.error('Microphone error:', error);
            alert('Microphone access denied. Please allow microphone access.');
        }
    }
    
    async stopWhisperRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
    }
    
    async transcribeWithWhisper(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            const response = await fetch(`${this.whisperUrl}/transcribe`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                this.onTranscript(data.text);
            } else {
                console.error('Whisper transcription failed');
            }
        } catch (error) {
            console.error('Whisper error:', error);
        }
    }
    
    // Callbacks (override these)
    onWakeWordDetected() {
        // Play sound or visual feedback
        console.log('🔊 Wake word detected!');
        
        // Visual feedback
        const micBtn = document.getElementById('micBtn');
        if (micBtn) {
            micBtn.classList.add('wake-word-active');
            setTimeout(() => micBtn.classList.remove('wake-word-active'), 2000);
        }
        
        // Audio feedback (short beep)
        const audio = new Audio('data:audio/wav;base64,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');
            audio.play().catch(() => {});
        }
    }
    
    onTranscript(text) {
        console.log('📝 Transcript:', text);
        // Send to chat input
        const input = document.getElementById('input');
        if (input) {
            input.value = text;
            input.focus();
            
            // Auto-send if wake word mode
            if (this.wakeWordEnabled) {
                const sendBtn = document.getElementById('send');
                if (sendBtn) {
                    sendBtn.click();
                }
            }
        }
    }
    
    // Enable wake word detection
    enableWakeWord() {
        if (!this.useWebSpeech) {
            console.warn('Wake word requires Web Speech API');
            return false;
        }
        
        this.wakeWordEnabled = true;
        this.recognition.start();
        console.log('🔊 Wake word detection enabled:', this.wakeWords);
        return true;
    }
    
    // Disable wake word detection
    disableWakeWord() {
        this.wakeWordEnabled = false;
        if (!this.isPushToTalkActive) {
            this.recognition.stop();
        }
        console.log('🔇 Wake word detection disabled');
    }
    
    // Toggle wake word
    toggleWakeWord() {
        if (this.wakeWordEnabled) {
            this.disableWakeWord();
            return false;
        } else {
            return this.enableWakeWord();
        }
    }
    
    // Push-to-talk (hold to speak)
    async startPushToTalk() {
        if (this.useWebSpeech) {
            this.isPushToTalkActive = true;
            this.recognition.start();
        } else {
            // Use local Whisper
            await this.startWhisperRecording();
        }
        
        console.log('🎤 Push-to-talk active');
        return true;
    }
    
    async stopPushToTalk() {
        if (this.useWebSpeech) {
            this.isPushToTalkActive = false;
            if (!this.wakeWordEnabled) {
                this.recognition.stop();
            }
        } else {
            await this.stopWhisperRecording();
        }
        
        console.log('🎤 Push-to-talk stopped');
    }
    
    // Whisper recording
    async startWhisperRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.audioChunks = [];
            this.mediaRecorder = new MediaRecorder(stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                await this.transcribeWithWhisper(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };
            
            this.mediaRecorder.start();
            console.log('🎤 Whisper recording started');
            
        } catch (error) {
            console.error('Microphone error:', error);
        }
    }
    
    async stopWhisperRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
    }
    
    async transcribeWithWhisper(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            const response = await fetch(`${this.whisperUrl}/transcribe`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                this.onTranscript(data.text);
            } else {
                console.error('Whisper transcription failed');
            }
        } catch (error) {
            console.error('Whisper error:', error);
        }
    }
}

// Global instance
window.voiceTriggers = new VoiceTriggers();

// Convenience functions
window.enableWakeWord = () => window.voiceTriggers.enableWakeWord();
window.disableWakeWord = () => window.voiceTriggers.disableWakeWord();
window.toggleWakeWord = () => window.voiceTriggers.toggleWakeWord();
window.startPushToTalk = () => window.voiceTriggers.startPushToTalk();
window.stopPushToTalk = () => window.voiceTriggers.stopPushToTalk();

