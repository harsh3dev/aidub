console.log('Content script loaded');

let translatedAudio = null;
let originalVolume = 1;
let isPlaying = false;
let isProcessing = false;

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

    if (!response.ok) {
      throw new Error('Translation service error');
    }

    const data = await response.json();
    console.log('Received audio URL:', data.audioUrl);
    
    // Load translated audio
    translatedAudio = new Audio(data.audioUrl);
    translatedAudio.loop = false;

    // Wait for audio to be loaded
    await new Promise((resolve, reject) => {
      translatedAudio.addEventListener('canplaythrough', resolve);
      translatedAudio.addEventListener('error', reject);
      translatedAudio.load();
    });

    // Set up event listeners for video control
    setupVideoControls(video);

    // Mute original video
    video.volume = 0;

    // If video is currently playing, start the translated audio
    if (!video.paused) {
      translatedAudio.currentTime = video.currentTime;
      translatedAudio.play().catch(error => {
        console.error('Error playing translated audio:', error);
      });
      isPlaying = true;
    }

    return true;
  } catch (error) {
    console.error('Translation error:', error);
    throw error;
  }
}

function setupVideoControls(video) {
  console.log('Setting up video controls...');
  
  // Handle play/pause
  video.addEventListener('play', () => {
    if (translatedAudio) {
      translatedAudio.currentTime = video.currentTime;
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
      translatedAudio.volume = video.volume;
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
}); 