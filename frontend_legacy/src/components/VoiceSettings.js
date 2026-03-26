import React, { useState, useEffect } from 'react';
import './VoiceSettings.css';

const VoiceSettings = () => {
    const [audioDevices, setAudioDevices] = useState({
        microphones: [],
        speakers: []
    });
    const [selectedDevices, setSelectedDevices] = useState({
        microphone: '',
        speaker: ''
    });
    const [audioLevels, setAudioLevels] = useState({
        microphoneGain: 50,
        speakerVolume: 75,
        voiceSpeed: 1.0,
        voicePitch: 0.8  // Deep voice default
    });
    const [permissions, setPermissions] = useState({
        microphone: false,
        speaker: false
    });
    const [testAudio, setTestAudio] = useState({
        isRecording: false,
        isPlaying: false
    });

    // Get available audio devices (Windows-aware)
    useEffect(() => {
        async function getAudioDevices() {
            try {
                // Request microphone permission first
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach(track => track.stop()); // Clean up
                setPermissions(prev => ({ ...prev, microphone: true }));

                // Enumerate devices
                const devices = await navigator.mediaDevices.enumerateDevices();
                
                const microphones = devices.filter(device => 
                    device.kind === 'audioinput' && device.deviceId !== 'default'
                );
                const speakers = devices.filter(device => 
                    device.kind === 'audiooutput' && device.deviceId !== 'default'
                );

                setAudioDevices({ microphones, speakers });
                
                // Set defaults
                if (microphones.length > 0) {
                    setSelectedDevices(prev => ({ 
                        ...prev, 
                        microphone: microphones[0].deviceId 
                    }));
                }
                if (speakers.length > 0) {
                    setSelectedDevices(prev => ({ 
                        ...prev, 
                        speaker: speakers[0].deviceId 
                    }));
                }

            } catch (error) {
                console.error('Audio device access denied:', error);
                setPermissions(prev => ({ ...prev, microphone: false }));
            }
        }

        getAudioDevices();
    }, []);

    // Test microphone input
    const testMicrophone = async () => {
        if (!selectedDevices.microphone) return;

        try {
            setTestAudio(prev => ({ ...prev, isRecording: true }));

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    deviceId: selectedDevices.microphone,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: false  // Manual gain control
                }
            });

            // Visual feedback for 3 seconds
            setTimeout(() => {
                stream.getTracks().forEach(track => track.stop());
                setTestAudio(prev => ({ ...prev, isRecording: false }));
            }, 3000);

        } catch (error) {
            console.error('Microphone test failed:', error);
            setTestAudio(prev => ({ ...prev, isRecording: false }));
        }
    };

    // Test speaker output with VeoGen voice
    const testSpeaker = () => {
        if (!selectedDevices.speaker) return;

        setTestAudio(prev => ({ ...prev, isPlaying: true }));

        const utterance = new SpeechSynthesisUtterance("Howdy! VeoGen audio test successful, partner!");
        
        // Configure deep voice
        const voices = speechSynthesis.getVoices();
        const deepVoice = voices.find(voice => 
            voice.name.toLowerCase().includes('david') || 
            voice.name.toLowerCase().includes('male') ||
            voice.name.toLowerCase().includes('guy')
        ) || voices[0];
        
        utterance.voice = deepVoice;
        utterance.rate = audioLevels.voiceSpeed;
        utterance.pitch = audioLevels.voicePitch;
        utterance.volume = audioLevels.speakerVolume / 100;

        utterance.onend = () => {
            setTestAudio(prev => ({ ...prev, isPlaying: false }));
        };

        speechSynthesis.speak(utterance);
    };

    // Windows-specific audio restart function
    const restartWindowsAudio = () => {
        // This would need backend PowerShell integration
        fetch('/api/system/restart-audio', { method: 'POST' })
            .then(() => alert('Windows audio service restarted'))
            .catch(err => console.error('Failed to restart audio:', err));
    };

    return (
        <div className="voice-settings">
            <h2>🎤 VeoGen Voice Settings</h2>
            
            {/* Permission Status */}
            <div className="permission-status">
                <div className={`permission-indicator ${permissions.microphone ? 'granted' : 'denied'}`}>
                    🎤 Microphone: {permissions.microphone ? 'Granted' : 'Denied'}
                </div>
            </div>

            {/* Microphone Settings */}
            <div className="audio-section">
                <h3>🎙️ Microphone Settings</h3>
                
                <div className="device-selector">
                    <label>Select Microphone:</label>
                    <select 
                        value={selectedDevices.microphone}
                        onChange={(e) => setSelectedDevices(prev => ({ 
                            ...prev, microphone: e.target.value 
                        }))}
                    >
                        <option value="">Select microphone...</option>
                        {audioDevices.microphones.map(device => (
                            <option key={device.deviceId} value={device.deviceId}>
                                {device.label || `Microphone ${device.deviceId.slice(0, 8)}`}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="gain-control">
                    <label>Microphone Gain: {audioLevels.microphoneGain}%</label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={audioLevels.microphoneGain}
                        onChange={(e) => setAudioLevels(prev => ({ 
                            ...prev, microphoneGain: parseInt(e.target.value) 
                        }))}
                    />
                </div>

                <button 
                    className={`test-button ${testAudio.isRecording ? 'recording' : ''}`}
                    onClick={testMicrophone}
                    disabled={!selectedDevices.microphone || testAudio.isRecording}
                >
                    {testAudio.isRecording ? '🔴 Recording...' : '🎤 Test Microphone'}
                </button>
            </div>

            {/* Speaker Settings */}
            <div className="audio-section">
                <h3>🔊 Speaker Settings</h3>
                
                <div className="device-selector">
                    <label>Select Speaker:</label>
                    <select 
                        value={selectedDevices.speaker}
                        onChange={(e) => setSelectedDevices(prev => ({ 
                            ...prev, speaker: e.target.value 
                        }))}
                    >
                        <option value="">Select speaker...</option>
                        {audioDevices.speakers.map(device => (
                            <option key={device.deviceId} value={device.deviceId}>
                                {device.label || `Speaker ${device.deviceId.slice(0, 8)}`}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="volume-control">
                    <label>Speaker Volume: {audioLevels.speakerVolume}%</label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={audioLevels.speakerVolume}
                        onChange={(e) => setAudioLevels(prev => ({ 
                            ...prev, speakerVolume: parseInt(e.target.value) 
                        }))}
                    />
                </div>

                <button 
                    className={`test-button ${testAudio.isPlaying ? 'playing' : ''}`}
                    onClick={testSpeaker}
                    disabled={!selectedDevices.speaker || testAudio.isPlaying}
                >
                    {testAudio.isPlaying ? '🔊 Playing...' : '🔊 Test Speaker'}
                </button>
            </div>

            {/* Voice Settings */}
            <div className="audio-section">
                <h3>🤠 VeoGen Voice Settings</h3>
                
                <div className="voice-control">
                    <label>Voice Speed: {audioLevels.voiceSpeed}x</label>
                    <input
                        type="range"
                        min="0.5"
                        max="2.0"
                        step="0.1"
                        value={audioLevels.voiceSpeed}
                        onChange={(e) => setAudioLevels(prev => ({ 
                            ...prev, voiceSpeed: parseFloat(e.target.value) 
                        }))}
                    />
                </div>

                <div className="voice-control">
                    <label>Voice Pitch: {audioLevels.voicePitch} (lower = deeper)</label>
                    <input
                        type="range"
                        min="0.1"
                        max="2.0"
                        step="0.1"
                        value={audioLevels.voicePitch}
                        onChange={(e) => setAudioLevels(prev => ({ 
                            ...prev, voicePitch: parseFloat(e.target.value) 
                        }))}
                    />
                </div>
            </div>

            {/* Windows-Specific Troubleshooting */}
            <div className="troubleshooting">
                <h3>🔧 Windows Audio Troubleshooting</h3>
                <div className="troubleshoot-buttons">
                    <button onClick={restartWindowsAudio}>
                        🔄 Restart Windows Audio Service
                    </button>
                    <button onClick={() => window.open('ms-settings:sound', '_blank')}>
                        ⚙️ Open Windows Sound Settings
                    </button>
                    <button onClick={() => window.open('ms-settings:privacy-microphone', '_blank')}>
                        🔒 Open Microphone Privacy Settings
                    </button>
                </div>
            </div>

            {/* Current Configuration Display */}
            <div className="config-display">
                <h3>📋 Current Configuration</h3>
                <pre>{JSON.stringify({ selectedDevices, audioLevels }, null, 2)}</pre>
            </div>
        </div>
    );
};

export default VoiceSettings; 