import React, { useState, useEffect } from 'react';
import BasicVoiceControl from './BasicVoiceControl';
import VoiceSettings from './VoiceSettings';
import './VoiceControlSideTab.css';

const VoiceControlSideTab = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [activeTab, setActiveTab] = useState('control'); // 'control', 'settings', 'battles'
    const [minimized, setMinimized] = useState(false);

    // Handle keyboard shortcut (Ctrl+` to toggle)
    useEffect(() => {
        const handleKeyDown = (event) => {
            if (event.ctrlKey && event.key === '`') {
                event.preventDefault();
                setIsOpen(prev => !prev);
            }
            // Escape to close
            if (event.key === 'Escape' && isOpen) {
                setIsOpen(false);
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isOpen]);

    const toggleSideTab = () => {
        setIsOpen(!isOpen);
        if (!isOpen) {
            setMinimized(false); // Expand when opening
        }
    };

    const toggleMinimized = () => {
        setMinimized(!minimized);
    };

    return (
        <>
            {/* Tab Toggle Button */}
            <div className={`voice-tab-toggle ${isOpen ? 'open' : ''}`} onClick={toggleSideTab}>
                <span className="tab-icon">🎤</span>
                <span className="tab-text">VeoGen Voice</span>
            </div>

            {/* Side Tab Panel */}
            <div className={`voice-side-tab ${isOpen ? 'open' : ''} ${minimized ? 'minimized' : ''}`}>
                {/* Header */}
                <div className="side-tab-header">
                    <h3>🤠 VeoGen Voice Control</h3>
                    <div className="header-controls">
                        <button 
                            className="minimize-btn"
                            onClick={toggleMinimized}
                            title={minimized ? 'Expand' : 'Minimize'}
                        >
                            {minimized ? '⬆️' : '⬇️'}
                        </button>
                        <button 
                            className="close-btn"
                            onClick={toggleSideTab}
                            title="Close (Esc)"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                {/* Tab Navigation */}
                {!minimized && (
                    <div className="tab-navigation">
                        <button 
                            className={`tab-btn ${activeTab === 'control' ? 'active' : ''}`}
                            onClick={() => setActiveTab('control')}
                        >
                            🎤 Control
                        </button>
                        <button 
                            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
                            onClick={() => setActiveTab('settings')}
                        >
                            ⚙️ Settings
                        </button>
                        <button 
                            className={`tab-btn ${activeTab === 'battles' ? 'active' : ''}`}
                            onClick={() => setActiveTab('battles')}
                        >
                            🎵 Rap Battles
                        </button>
                    </div>
                )}

                {/* Tab Content */}
                {!minimized && (
                    <div className="tab-content">
                        {activeTab === 'control' && (
                            <div className="tab-panel">
                                <BasicVoiceControl />
                            </div>
                        )}
                        
                        {activeTab === 'settings' && (
                            <div className="tab-panel">
                                <VoiceSettings />
                            </div>
                        )}
                        
                        {activeTab === 'battles' && (
                            <div className="tab-panel">
                                <RapBattleMode />
                            </div>
                        )}
                    </div>
                )}

                {/* Minimized State */}
                {minimized && (
                    <div className="minimized-controls">
                        <button className="quick-listen-btn" title="Quick Listen (Ctrl+`)">
                            🎤
                        </button>
                        <div className="voice-status-mini">
                            🟢 Ready
                        </div>
                    </div>
                )}

                {/* Resize Handle */}
                <div className="resize-handle"></div>
            </div>

            {/* Overlay when open on mobile */}
            {isOpen && <div className="voice-tab-overlay" onClick={toggleSideTab}></div>}
        </>
    );
};

// Rap Battle Mode Component (Future Samuel L. Jackson voice!)
const RapBattleMode = () => {
    const [battleMode, setBattleMode] = useState(false);
    const [userVerse, setUserVerse] = useState('');
    const [battleHistory, setBattleHistory] = useState([]);

    const startBattle = () => {
        setBattleMode(true);
        // Future: Switch to Samuel L. Jackson voice mode
        const veoGenOpener = "Alright, partner, you think you can out-rap VeoGen? Let's see what you got!";
        setBattleHistory([{ speaker: 'VeoGen', verse: veoGenOpener }]);
    };

    const submitVerse = () => {
        if (!userVerse.trim()) return;

        // Add user verse
        const newHistory = [...battleHistory, { speaker: 'You', verse: userVerse }];
        
        // Generate VeoGen response (placeholder for now)
        const veoGenResponses = [
            "That's cute, but I generate videos faster than you drop bars!",
            "I've seen better rhymes in error logs, partner!",
            "You call that a verse? I call that a first draft!",
            "Step aside, amateur - this cowboy's got bars of gold!",
            "I process AI faster than you process syllables!"
        ];
        
        const response = veoGenResponses[Math.floor(Math.random() * veoGenResponses.length)];
        newHistory.push({ speaker: 'VeoGen', verse: response });
        
        setBattleHistory(newHistory);
        setUserVerse('');
    };

    return (
        <div className="rap-battle-mode">
            <div className="battle-header">
                <h3>🎵 VeoGen Rap Battles</h3>
                <p className="future-feature">
                    🔮 Coming Soon: Samuel L. Jackson voice mode for EPIC battles!
                </p>
            </div>

            {!battleMode ? (
                <div className="battle-start">
                    <button className="start-battle-btn" onClick={startBattle}>
                        🎤 Start Rap Battle
                    </button>
                    <p className="battle-description">
                        Challenge VeoGen to a rap battle! Drop your best bars and see if you can 
                        out-rhyme our cowboy AI. Future update will include Samuel L. Jackson voice 
                        for maximum attitude! 🔥
                    </p>
                </div>
            ) : (
                <div className="battle-active">
                    <div className="battle-history">
                        {battleHistory.map((entry, index) => (
                            <div key={index} className={`battle-verse ${entry.speaker.toLowerCase()}`}>
                                <strong>{entry.speaker}:</strong>
                                <p>"{entry.verse}"</p>
                            </div>
                        ))}
                    </div>
                    
                    <div className="battle-input">
                        <textarea
                            value={userVerse}
                            onChange={(e) => setUserVerse(e.target.value)}
                            placeholder="Drop your verse here, partner..."
                            rows={3}
                        />
                        <div className="battle-controls">
                            <button onClick={submitVerse} disabled={!userVerse.trim()}>
                                🎤 Drop Bars
                            </button>
                            <button onClick={() => setBattleMode(false)}>
                                🏳️ End Battle
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="battle-tips">
                <h4>🎯 Battle Tips:</h4>
                <ul>
                    <li>Keep it clean but clever</li>
                    <li>Rhyme about AI, videos, or technology</li>
                    <li>VeoGen will roast your coding skills</li>
                    <li>Future: Voice input/output for real-time battles</li>
                </ul>
            </div>
        </div>
    );
};

export default VoiceControlSideTab; 