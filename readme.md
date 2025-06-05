# 🎙️ AIDub

**AIDub** is an AI-powered tool that automates the dubbing of videos into different languages. It processes an input video, extracts the audio, translates the transcript, synthesizes new audio in the target language, and merges it back with the original video. This solution is ideal for content creators, educators, and businesses aiming to reach a global audience.

🔗 [Live Demo](https://aidub.vercel.app)

---

## 🚀 Features

- **Automatic Speech Recognition (ASR):** Extracts transcripts from video audio.
- **Translation:** Translates transcripts into multiple languages.
- **Text-to-Speech (TTS):** Generates natural-sounding audio in the target language.
- **Video Merging:** Combines the new audio with the original video seamlessly.
- **Web Interface:** User-friendly interface for uploading videos and selecting target languages.

---

## 📁 Project Structure

\`\`\`plaintext
aidub/
├── backend/                 # Backend server handling processing
│   ├── server.py            # Main server script
│   ├── requirements.txt     # Python dependencies
├── extension/               # Browser extension (if applicable)
├── landing/                 # Frontend landing page
├── audio_files/             # Directory for audio processing
├── final_video.mp4          # Output video with dubbed audio
├── original_transcript.txt  # Extracted transcript from original audio
├── translated_transcript.txt# Translated transcript
├── translated_audio_only.wav# Synthesized audio in target language
├── cert.pem                 # SSL certificate
├── key.pem                  # SSL key
├── .gitignore               # Git ignore file
\`\`\`

---

## 🛠️ Installation

### Prerequisites

- Python 3.7 or higher
- FFmpeg installed and added to system PATH

### Steps

1. Clone the repository:
   \`\`\`bash
   git clone https://github.com/harsh3dev/aidub.git
   cd aidub/backend
   \`\`\`

2. Create a virtual environment and activate it:
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   \`\`\`

3. Install the required dependencies:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. Run the server:
   \`\`\`bash
   python server.py
   \`\`\`

5. Access the web interface at \`https://localhost:5000\` (ensure \`cert.pem\` and \`key.pem\` are present for SSL).

---

## 🧪 Usage

1. Navigate to the [live demo](https://aidub.vercel.app) or run the application locally.
2. Upload the video you wish to dub.
3. Select the target language for dubbing.
4. Initiate the dubbing process.
5. Download the dubbed video once processing is complete.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 👤 Author

- **Harsh Pandey**
  - GitHub: [@harsh3dev](https://github.com/harsh3dev)
  - LinkedIn: [Harsh Pandey](https://www.linkedin.com/in/harsh3dev/)
  - Twitter: [@harshxai](https://twitter.com/harshxai)

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request. For major changes, open an issue first to discuss potential improvements.
EOF
