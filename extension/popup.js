document.addEventListener('DOMContentLoaded', function() {
  const translateBtn = document.getElementById('translate-btn');
  const voiceSelect = document.getElementById('voice-select');
  const statusDiv = document.getElementById('status');
  const loadingDiv = document.getElementById('loading');

  // Check if we're on a YouTube video page
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const currentTab = tabs[0];
    if (!currentTab.url.includes('youtube.com/watch')) {
      showStatus('Please navigate to a YouTube video page', 'error');
      translateBtn.disabled = true;
    }
  });

  translateBtn.addEventListener('click', async function() {
    try {
      // Get the current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Check if we're on YouTube
      if (!tab.url.includes('youtube.com/watch')) {
        showStatus('Please navigate to a YouTube video page', 'error');
        return;
      }

      // Show loading state
      translateBtn.disabled = true;
      loadingDiv.style.display = 'block';
      statusDiv.style.display = 'none';

      // First, inject the content script if it's not already injected
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        });
      } catch (error) {
        console.log('Content script already injected or injection failed:', error);
      }

      // Wait a moment for the content script to initialize
      await new Promise(resolve => setTimeout(resolve, 500));

      // Send message to content script
      chrome.tabs.sendMessage(tab.id, {
        action: 'translateVideo',
        voiceId: voiceSelect.value
      }, function(response) {
        // Hide loading state
        loadingDiv.style.display = 'none';
        
        if (chrome.runtime.lastError) {
          console.error('Runtime error:', chrome.runtime.lastError);
          showStatus('Error: Content script not ready. Please refresh the page and try again.', 'error');
        } else if (response && response.success) {
          showStatus('Translation completed!', 'success');
        } else {
          showStatus('Error: ' + (response ? response.error : 'Unknown error'), 'error');
        }
        translateBtn.disabled = false;
      });
    } catch (error) {
      // Hide loading state
      loadingDiv.style.display = 'none';
      console.error('Error:', error);
      showStatus('Error: ' + error.message, 'error');
      translateBtn.disabled = false;
    }
  });

  function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = 'status ' + type;
    statusDiv.style.display = 'block';
  }
}); 