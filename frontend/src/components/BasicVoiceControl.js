import React, { useState, useEffect, useRef, useCallback } from 'react';
import './BasicVoiceControl.css';

const BasicVoiceControl = () => {
    const [isListening, setIsListening] = useState(false);
    const [lastCommand, setLastCommand] = useState('');
    const [response, setResponse] = useState('');
    const [voiceEnabled, setVoiceEnabled] = useState(false);
    const [audioSettings, setAudioSettings] = useState({
        voiceSpeed: 1.0,
        voicePitch: 0.8,  // Deep voice
        volume: 0.8
    });

    const recognitionRef = useRef(null);
    const synthRef = useRef(null);

    // Speak text with VeoGen's deep voice
    const speakText = useCallback((text) => {
        if (!synthRef.current || !voiceEnabled) return;

        // Cancel any ongoing speech
        synthRef.current.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        
        // Configure deep voice
        const voices = synthRef.current.getVoices();
        let deepVoice = voices.find(voice => 
            voice.name.toLowerCase().includes('david') || 
            voice.name.toLowerCase().includes('male') ||
            voice.name.toLowerCase().includes('guy') ||
            voice.name.toLowerCase().includes('deep')
        );

        // Fallback to first available voice
        if (!deepVoice && voices.length > 0) {
            deepVoice = voices[0];
        }

        if (deepVoice) {
            utterance.voice = deepVoice;
        }
        
        utterance.rate = audioSettings.voiceSpeed;
        utterance.pitch = audioSettings.voicePitch;
        utterance.volume = audioSettings.volume;

        synthRef.current.speak(utterance);
    }, [voiceEnabled, audioSettings]);

    // Handle voice commands
    const handleVoiceCommand = useCallback((command) => {
        let responseText = '';

        if (command.includes('weather') && command.includes('austin')) {
            responseText = "Get lost! I ain't no weather service, partner!";
        } else if (command.includes('howdy') || command.includes('hello') || command.includes('hi')) {
            responseText = "Well howdy there! What can VeoGen do for ya?";
        } else if (command.includes('what') && command.includes('time')) {
            const time = new Date().toLocaleTimeString();
            responseText = `It's ${time}, partner!`;
        } else if (command.includes('generate') || command.includes('video')) {
            responseText = "Video generation coming right up! Just give me them details!";
        } else if (command.includes('music') || command.includes('song')) {
            responseText = "Music generation, eh? That's mighty fine! What style you looking for?";
        } else if (command.includes('image') || command.includes('picture')) {
            responseText = "Image generation? You bet! Describe what you want to see!";
        } else if (command.includes('help')) {
            responseText = "I can help with video generation, music, images, and general VeoGen questions. Just speak your mind!";
        } else if (command.includes('stop') || command.includes('quiet') || command.includes('shut up')) {
            responseText = "Alright, I'll pipe down, partner.";
        } else {
            responseText = "I reckon I didn't catch that. Try asking about video generation, music, images, or say 'help' for more options.";
        }

        setResponse(responseText);
        speakText(responseText);
    }, [speakText]);

    // Initialize speech recognition and synthesis
    useEffect(() => {
        // Check for speech synthesis support
        if ('speechSynthesis' in window) {
            synthRef.current = window.speechSynthesis;
            setVoiceEnabled(true);
        }

        // Check for speech recognition support
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            
            // Configure recognition
            recognitionRef.current.continuous = false;
            recognitionRef.current.interimResults = false;
            recognitionRef.current.lang = 'en-US';

            // Handle recognition events
            recognitionRef.current.onresult = (event) => {
                const command = event.results[0][0].transcript.toLowerCase();
                setLastCommand(command);
                handleVoiceCommand(command);
                setIsListening(false);
            };

            recognitionRef.current.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                setIsListening(false);
            };

            recognitionRef.current.onend = () => {
                setIsListening(false);
            };
        } else {
            console.warn('Speech recognition not supported');
        }

        // Say howdy on component mount
        setTimeout(() => {
            speakText("Howdy! VeoGen voice control is ready, partner!");
        }, 1000);

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
        };
    }, [handleVoiceCommand, speakText]);

    // Start listening for voice commands
    const startListening = () => {
        if (!recognitionRef.current || isListening) return;

        try {
            setIsListening(true);
            recognitionRef.current.start();
        } catch (error) {
            console.error('Failed to start voice recognition:', error);
            setIsListening(false);
        }
    };

    // Stop listening
    const stopListening = () => {
        if (recognitionRef.current && isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
        }
    };

    // Test the voice output
    const testVoice = () => {
        speakText("Howdy! This here's a voice test from your friendly VeoGen!");
    };

    return (
        <div className="voice-control">
            <div className="voice-header">
                <h2>🤠 VeoGen Voice Control</h2>
                <div className={`voice-status ${voiceEnabled ? 'enabled' : 'disabled'}`}>
                    {voiceEnabled ? '🎤 Voice Enabled' : '❌ Voice Disabled'}
                </div>
            </div>

            <div className="voice-interface">
                {/* Voice Control Buttons */}
                <div className="control-buttons">
                    <button 
                        className={`listen-button ${isListening ? 'listening' : ''}`}
                        onClick={isListening ? stopListening : startListening}
                        disabled={!voiceEnabled}
                    >
                        {isListening ? '🔴 Stop Listening' : '🎤 Start Listening'}
                    </button>
                    
                    <button 
                        className="test-button"
                        onClick={testVoice}
                        disabled={!voiceEnabled}
                    >
                        🔊 Test Voice
                    </button>
                </div>

                {/* Last Command & Response */}
                <div className="conversation">
                    {lastCommand && (
                        <div className="command-display">
                            <strong>You said:</strong> "{lastCommand}"
                        </div>
                    )}
                    
                    {response && (
                        <div className="response-display">
                            <strong>VeoGen says:</strong> "{response}"
                        </div>
                    )}
                </div>

                {/* Voice Settings Quick Controls */}
                <div className="quick-settings">
                    <div className="setting-control">
                        <label>Voice Speed: {audioSettings.voiceSpeed}x</label>
                        <input
                            type="range"
                            min="0.5"
                            max="2.0"
                            step="0.1"
                            value={audioSettings.voiceSpeed}
                            onChange={(e) => setAudioSettings(prev => ({ 
                                ...prev, voiceSpeed: parseFloat(e.target.value) 
                            }))}
                        />
                    </div>

                    <div className="setting-control">
                        <label>Voice Pitch: {audioSettings.voicePitch} (lower = deeper)</label>
                        <input
                            type="range"
                            min="0.1"
                            max="2.0"
                            step="0.1"
                            value={audioSettings.voicePitch}
                            onChange={(e) => setAudioSettings(prev => ({ 
                                ...prev, voicePitch: parseFloat(e.target.value) 
                            }))}
                        />
                    </div>

                    <div className="setting-control">
                        <label>Volume: {Math.round(audioSettings.volume * 100)}%</label>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={audioSettings.volume}
                            onChange={(e) => setAudioSettings(prev => ({ 
                                ...prev, volume: parseFloat(e.target.value) 
                            }))}
                        />
                    </div>
                </div>

                {/* Example Commands */}
                <div className="example-commands">
                    <h3>Try saying:</h3>
                    <ul>
                        <li>"Howdy!" or "Hello VeoGen"</li>
                        <li>"How's the weather in Austin?" (for the classic response)</li>
                        <li>"What time is it?"</li>
                        <li>"Generate a video"</li>
                        <li>"What's your status?"</li>
                        <li>"Help"</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default BasicVoiceControl; 