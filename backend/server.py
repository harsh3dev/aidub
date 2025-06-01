from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from main import translate_and_create_timed_audio, get_transcript, get_video_id
import tempfile
import shutil

app = Flask(__name__)
CORS(app)

@app.route('/translate', methods=['POST'])
def translate_video():
    try:
        data = request.json
        video_url = data.get('videoUrl')
        voice_id = data.get('voiceId')
        target_language = data.get('targetLanguage', 'hi-IN')

        if not video_url or not voice_id:
            return jsonify({'error': 'Missing required parameters'}), 400

        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        try:
            # Get video ID and transcript
            video_id = get_video_id(video_url)
            if not video_id:
                return jsonify({'error': 'Invalid YouTube URL'}), 400

            transcript_data, _ = get_transcript(video_id)
            if not transcript_data:
                return jsonify({'error': 'Could not get transcript'}), 400

            # Process translation and audio generation
            audio_segments = translate_and_create_timed_audio(
                transcript_data,
                target_language=target_language,
                voice_id=voice_id
            )

            if not audio_segments:
                return jsonify({'error': 'Failed to generate audio'}), 500

            # Return the audio file URL
            audio_url = f"http://localhost:5000/audio/translated_audio.wav"
            return jsonify({
                'success': True,
                'audioUrl': audio_url
            })

        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(debug=True) 