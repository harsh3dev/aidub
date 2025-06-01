// Background script for YouTube Video Translator
console.log('Background script loaded');

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed');
});

// Listen for messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request);
  
  if (request.action === 'contentScriptReady') {
    console.log('Content script is ready');
    sendResponse({ success: true });
  } else if (request.action === 'cleanup') {
    console.log('Performing cleanup');
    sendResponse({ success: true });
  }
  return true;
}); 