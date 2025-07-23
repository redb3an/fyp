class AvatarController {
    constructor(config = null) {
        this.avatarImg = document.getElementById('avatar-img');
        this.isTalking = false;
        this.blinkTimeout = null;
        this.talkInterval = null;
        this.mouthFrames = ['close', 'halfopen', 'fullopen'];
        this.currentMouthFrame = 0;
        this.state = { eyes: 'open', mouth: 'close' };

        // Enhanced avatar behavior configuration with natural speaking speed
        this.config = config || {
            "avatar": {
                "defaultBehavior": {
                    "blinking": "human-like"  // continuous blinking throughout
                },
                "speakingBehavior": {
                    "onStart": {
                        "mouthAnimation": {
                            "type": "open_half_to_full",
                            "syncWithTTS": true,
                            "pace": "match_tts",
                            "rateScale": 0.9  // slows mouth to 90% of base animation speed
                        }
                    },
                    "onEnd": {
                        "mouthAnimation": "close"
                    }
                }
            },
            "tts": {
                "voice": {
                    "gender": "female",
                    "preset": "en-US-Wavenet-F"  // Change as needed for your TTS provider
                },
                "speed": 1.4  // Much faster speed to match typewriter effect
            }
        };

        this.updateImage();
        this.initializeDefaultBehavior();
    }

    getImageName() {
        return `/static/chatbot/avatar/avatar_eyes${this.state.eyes}_mouth${this.state.mouth}.png`;
    }

    updateImage() {
        this.avatarImg.src = this.getImageName();
    }

    initializeDefaultBehavior() {
        const defaultBehavior = this.config.avatar.defaultBehavior;

        if (defaultBehavior.blinking === "human-like") {
            this.setupHumanLikeBlinking();
        }
    }

    setupHumanLikeBlinking() {
        const blink = () => {
            // Enhanced blinking: continues even while talking for more natural behavior
            this.state.eyes = 'close';
            this.updateImage();
            setTimeout(() => {
                this.state.eyes = 'open';
                this.updateImage();
                // Schedule next blink with human-like randomness
                if (this.isTalking) {
                    // Slightly reduced frequency while talking but still regular
                    this.blinkTimeout = setTimeout(blink, Math.random() * 4000 + 3000);
                } else {
                    // Normal blinking frequency when not talking (2-5 seconds)
                    this.blinkTimeout = setTimeout(blink, Math.random() * 3000 + 2000);
                }
            }, 150 + Math.random() * 100); // Blink duration 150-250ms
        };

        // Initial blink after 1-3 seconds
        this.blinkTimeout = setTimeout(blink, Math.random() * 2000 + 1000);
    }

    startTalking() {
        if (this.isTalking) return;

        const speakingBehavior = this.config.avatar.speakingBehavior;
        const onStartBehavior = speakingBehavior.onStart;

        this.isTalking = true;

        // Apply onStart mouth animation with enhanced configuration
        if (onStartBehavior.mouthAnimation && onStartBehavior.mouthAnimation.type === "open_half_to_full") {
            this.animateOpenHalfToFull(onStartBehavior.mouthAnimation);
        } else if (onStartBehavior.mouthAnimation === "open_half_to_full") {
            // Backward compatibility
            this.animateOpenHalfToFull();
        }

        // Continue talking animation with natural pace
        this.continueTalkingAnimation();
    }

    animateOpenHalfToFull(animationConfig = null) {
        // Enhanced mouth opening sequence with rate scaling
        const rateScale = animationConfig?.rateScale || 0.9;
        const baseDelay = 100;
        const scaledDelay = baseDelay / rateScale;

        this.state.mouth = 'halfopen';
        this.state.eyes = 'open';
        this.updateImage();

        setTimeout(() => {
            this.state.mouth = 'fullopen';
            this.updateImage();
        }, scaledDelay);
    }

    continueTalkingAnimation() {
        let frameIndex = 0;
        const talkingFrames = ['halfopen', 'fullopen', 'halfopen', 'close'];

        // Enhanced timing based on TTS configuration
        const baseAnimationSpeed = 180;
        const rateScale = this.config.avatar.speakingBehavior.onStart?.mouthAnimation?.rateScale || 0.9;
        const ttsSpeed = this.config.tts?.speed || 1.4;

        // Calculate natural animation speed based on TTS speed and rate scale
        const naturalAnimationSpeed = (baseAnimationSpeed / rateScale) * (1 / ttsSpeed);

        this.talkInterval = setInterval(() => {
            if (!this.isTalking) return;

            this.state.mouth = talkingFrames[frameIndex % talkingFrames.length];
            // Eyes remain open during talking but still blink naturally
            this.updateImage();

            frameIndex++;
        }, naturalAnimationSpeed);
    }

    stopTalking() {
        const speakingBehavior = this.config.avatar.speakingBehavior;
        const onEndBehavior = speakingBehavior.onEnd;

        this.isTalking = false;

        // Clear talking animation
        if (this.talkInterval) {
            clearInterval(this.talkInterval);
            this.talkInterval = null;
        }

        // Apply onEnd mouth animation
        if (onEndBehavior.mouthAnimation === "close") {
            this.animateClose();
        }

        // Continue natural blinking behavior (no need to restart as it continues during talking)
        if (!this.blinkTimeout) {
            this.setupHumanLikeBlinking();
        }
    }

    animateClose() {
        // Enhanced closing animation with natural timing
        const baseDelay = 100;
        const rateScale = this.config.avatar.speakingBehavior.onStart?.mouthAnimation?.rateScale || 0.9;
        const scaledDelay = baseDelay / rateScale;

        if (this.state.mouth === 'fullopen') {
            this.state.mouth = 'halfopen';
            this.updateImage();

            setTimeout(() => {
                this.state.mouth = 'close';
                this.updateImage();
            }, scaledDelay);
        } else {
            this.state.mouth = 'close';
            this.updateImage();
        }
    }

    // Enhanced method to get TTS configuration
    getTTSConfig() {
        return this.config.tts || {
            voice: {
                gender: "female",
                preset: "en-US-Wavenet-F"
            },
            speed: 1.4
        };
    }

    // Method to update configuration at runtime
    updateConfig(newConfig) {
        this.config = newConfig;

        // Restart behavior with new configuration
        if (this.blinkTimeout) {
            clearTimeout(this.blinkTimeout);
        }
        if (this.talkInterval) {
            clearInterval(this.talkInterval);
        }

        this.isTalking = false;
        this.state = { eyes: 'open', mouth: 'close' };
        this.updateImage();
        this.initializeDefaultBehavior();
    }

    // Enhanced legacy method for backward compatibility with natural TTS settings
    speak(text) {
        return new Promise((resolve) => {
            const ttsConfig = this.getTTSConfig();
            const utterance = new SpeechSynthesisUtterance(text);

            // Apply TTS configuration
            utterance.rate = ttsConfig.speed;
            utterance.pitch = 1.2; // Slightly higher pitch for more feminine sound
            utterance.lang = 'en-US';

            // Try to use the specified voice if available
            const voices = speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice =>
                voice.name.includes('Wavenet') && voice.lang === 'en-US'
            ) || voices.find(voice =>
                voice.lang === 'en-US' && voice.name.toLowerCase().includes('female')
            );

            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }

            utterance.onstart = () => this.startTalking();
            utterance.onend = () => {
                this.stopTalking();
                resolve();
            };
            utterance.onerror = () => {
                this.stopTalking();
                resolve();
            };
            window.speechSynthesis.speak(utterance);
        });
    }

    // Method to manually trigger talking animation (for external TTS)
    triggerSpeaking(duration = null) {
        this.startTalking();

        if (duration) {
            // Calculate natural duration based on TTS speed
            const ttsSpeed = this.config.tts?.speed || 1.4;
            const adjustedDuration = duration / ttsSpeed;

            setTimeout(() => {
                this.stopTalking();
            }, adjustedDuration);
        }
    }

    // Method to manually stop talking animation
    stopSpeaking() {
        this.stopTalking();
    }

    // Cleanup method
    destroy() {
        if (this.blinkTimeout) {
            clearTimeout(this.blinkTimeout);
        }
        if (this.talkInterval) {
            clearInterval(this.talkInterval);
        }
    }
}

// Initialize avatar controller with enhanced natural configuration
document.addEventListener('DOMContentLoaded', () => {
    const enhancedConfig = {
        "avatar": {
            "defaultBehavior": {
                "blinking": "human-like"  // continuous blinking throughout
            },
            "speakingBehavior": {
                "onStart": {
                    "mouthAnimation": {
                        "type": "open_half_to_full",
                        "syncWithTTS": true,
                        "pace": "match_tts",
                        "rateScale": 0.9  // slows mouth to 90% of base animation speed
                    }
                },
                "onEnd": {
                    "mouthAnimation": "close"
                }
            }
        },
        "tts": {
            "voice": {
                "gender": "female",
                "preset": "en-US-Wavenet-F"  // Change as needed for your TTS provider
            },
            "speed": 1.4  // Much faster speed to match typewriter effect
        }
    };

    window.avatarController = new AvatarController(enhancedConfig);
}); 