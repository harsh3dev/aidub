console.log('Content script loaded');

let translatedAudio = null;
let originalVolume = 1;
let isPlaying = false;
let isProcessing = false;
let controlButton = null;

// Create and inject visible audio element for testing
function createHiddenAudioElement() {
    const audioElement = document.createElement('audio');
    audioElement.id = 'murfai-translated-audio';
    audioElement.style.cssText = `
        position: fixed;
        bottom: 150px;
        right: 20px;
        z-index: 9999;
        background-color: rgba(0, 0, 0, 0.8);
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    `;
    audioElement.controls = true;
    audioElement.crossOrigin = 'anonymous'; // Enable CORS
    audioElement.volume = 0.8; // Set default volume to 80%
    document.body.appendChild(audioElement);
    return audioElement;
}

// Create and inject control button
function createControlButton() {
    const button = document.createElement('button');
    button.id = 'murfai-control-button';
    button.innerHTML = '🔊 Play Translation';
    button.style.cssText = `
        position: fixed;
        bottom: 80px;
        right: 20px;
        z-index: 9999;
        padding: 10px 20px;
        background-color: #ff0000;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    `;
    
    button.addEventListener('mouseover', () => {
        button.style.backgroundColor = '#cc0000';
    });
    
    button.addEventListener('mouseout', () => {
        button.style.backgroundColor = '#ff0000';
    });
    
    document.body.appendChild(button);
    return button;
}

// Toggle audio playback
function toggleAudioPlayback() {
    if (!translatedAudio) return;
    
    if (isPlaying) {
        translatedAudio.pause();
        controlButton.innerHTML = '🔊 Play Translation';
    } else {
        translatedAudio.play().catch(error => {
            console.error('Error playing translated audio:', error);
        });
        controlButton.innerHTML = '🔇 Pause Translation';
    }
    isPlaying = !isPlaying;
}

// Notify that content script is ready
chrome.runtime.sendMessage({ action: 'contentScriptReady' });

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Content script received message:', request);
    
    if (request.action === 'translateVideo') {
        if (isProcessing) {
            sendResponse({ success: false, error: 'Translation already in progress' });
            return true;
        }
        
        isProcessing = true;
        handleVideoTranslation(request.voiceId)
            .then(() => {
                isProcessing = false;
                sendResponse({ success: true });
            })
            .catch(error => {
                isProcessing = false;
                console.error('Translation error:', error);
                sendResponse({ success: false, error: error.message });
            });
        return true; // Keep the message channel open for async response
    }
});

async function handleVideoTranslation(voiceId) {
    try {
        console.log('Starting video translation...');
        
        // Get video URL and ID
        const videoUrl = window.location.href;
        const videoId = new URLSearchParams(window.location.search).get('v');
        
        if (!videoId) {
            throw new Error('Could not get video ID');
        }

        // Get video element
        const video = document.querySelector('video');
        if (!video) {
            throw new Error('Could not find video element');
        }

        // Store original volume
        originalVolume = video.volume;

        // Create control button if it doesn't exist
        if (!controlButton) {
            controlButton = createControlButton();
            controlButton.addEventListener('click', toggleAudioPlayback);
        }

        console.log('Calling backend API...');
        // Call backend API to process video
        const response = await fetch('http://localhost:5000/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                videoUrl,
                voiceId,
                targetLanguage: 'hi-IN'
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            let errorMessage = 'Translation service error';
            if (data.error) {
                if (data.error.includes('captions available')) {
                    errorMessage = 'This video does not have captions available. Please try a different video.';
                } else if (data.error.includes('Invalid YouTube URL')) {
                    errorMessage = 'Invalid YouTube URL. Please make sure you are on a YouTube video page.';
                } else {
                    errorMessage = data.error;
                }
            }
            throw new Error(errorMessage);
        }

        console.log('Received audio URL:', data.audioUrl);
        
        // Create or get visible audio element
        let audioElement = document.getElementById('murfai-translated-audio');
        if (!audioElement) {
            audioElement = createHiddenAudioElement();
        }

        // Set audio source and properties
        audioElement.src = data.audioUrl;
        audioElement.muted = false;        
        audioElement.volume = 1;

        audioElement.loop = false;
        translatedAudio = audioElement;

        // Wait for audio to be loaded
        await new Promise((resolve, reject) => {
            audioElement.addEventListener('canplaythrough', resolve, { once: true });
            audioElement.addEventListener('error', () => reject(new Error('Failed to load audio. Please try again.')), { once: true });
            audioElement.load();
        });

        // Set up event listeners for video control
        setupVideoControls(video);

        // Mute original video
        video.volume = 0;

        // Don't automatically start playing - wait for button click
        audioElement.currentTime = video.currentTime;
        isPlaying = false;
        audioElement.muted = false;
        audioElement.volume = 1;
        controlButton.innerHTML = '🔊 Play Translation';

        return true;
    } catch (error) {
        console.error('Translation error:', error);
        // Show error message to user
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #ff4444;
            color: white;
            padding: 15px;
            border-radius: 5px;
            z-index: 9999;
            max-width: 300px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        `;
        errorDiv.textContent = error.message;
        document.body.appendChild(errorDiv);
        
        // Remove error message after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
        
        throw error;
    }
}

function setupVideoControls(video) {
    console.log('Setting up video controls...');
    
    // Handle play/pause
    video.addEventListener('play', () => {
        if (translatedAudio) {
            // Ensure audio starts at the same position as video
            translatedAudio.currentTime = video.currentTime;
            translatedAudio.muted = false;
            translatedAudio.volume = 0.8; // Set default volume to 80%
            translatedAudio.play().catch(error => {
                console.error('Error playing translated audio:', error);
            });
            isPlaying = true;
        }
    });

    video.addEventListener('pause', () => {
        if (translatedAudio) {
            translatedAudio.pause();
            isPlaying = false;
        }
    });

    // Handle seeking
    video.addEventListener('seeked', () => {
        if (translatedAudio) {
            translatedAudio.currentTime = video.currentTime;
            if (isPlaying) {
                translatedAudio.play().catch(error => {
                    console.error('Error playing translated audio after seek:', error);
                });
            }
        }
    });

    // Handle video end
    video.addEventListener('ended', () => {
        if (translatedAudio) {
            translatedAudio.pause();
            translatedAudio.currentTime = 0;
            isPlaying = false;
        }
    });

    // Handle volume change
    video.addEventListener('volumechange', () => {
        if (translatedAudio) {
            // Keep translated audio volume at 80% of video volume
            translatedAudio.volume = Math.min(video.volume * 0.8, 1);
        }
    });

    // Handle rate change
    video.addEventListener('ratechange', () => {
        if (translatedAudio) {
            translatedAudio.playbackRate = video.playbackRate;
        }
    });
    
    console.log('Video controls setup complete');
}

// Clean up when extension is disabled
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'cleanup') {
        console.log('Performing cleanup...');
        if (translatedAudio) {
            translatedAudio.pause();
            translatedAudio = null;
        }
        if (controlButton) {
            controlButton.remove();
            controlButton = null;
        }
        const audioElement = document.getElementById('murfai-translated-audio');
        if (audioElement) {
            audioElement.remove();
        }
        const video = document.querySelector('video');
        if (video) {
            video.volume = originalVolume;
        }
        isPlaying = false;
        isProcessing = false;
        sendResponse({ success: true });
    }
    return true;
});

// Handle page reload
window.addEventListener('beforeunload', () => {
    if (translatedAudio) {
        translatedAudio.pause();
        translatedAudio = null;
    }
    if (controlButton) {
        controlButton.remove();
        controlButton = null;
    }
    const audioElement = document.getElementById('murfai-translated-audio');
    if (audioElement) {
        audioElement.remove();
    }
});