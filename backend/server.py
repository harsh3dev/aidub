from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from main import translate_and_create_timed_audio, get_transcript, get_video_id
import tempfile
import shutil
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import ssl
from fastapi.middleware.cors import CORSMiddleware


# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

app = Flask(__name__)
CORS(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can also be ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],    # or restrict to ["GET", "POST"]
    allow_headers=["*"],
)


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
        try:            # Get video ID and transcript
            video_id = get_video_id(video_url)
            if not video_id:
                return jsonify({'error': 'Invalid YouTube URL'}), 400

            transcript_data, transcript_text = get_transcript(video_id)
            if not transcript_data:
                return jsonify({'error': 'This video does not have captions available. Please try a different video with captions/subtitles.'}), 400

            print(f"Retrieved transcript with {len(transcript_data)} segments")
            
            # Process translation and audio generation
            audio_segments = translate_and_create_timed_audio(
                transcript_data,
                target_language=target_language,
                voice_id=voice_id
            )

            if not audio_segments:
                return jsonify({'error': 'Failed to generate audio'}), 500

            # Upload audio file to Cloudinary
            result = cloudinary.uploader.upload(
                'translated_audio_only.wav',
                resource_type='raw',
                public_id=f'translated_audio_{video_id}'
            )

            # Return the Cloudinary URL
            return jsonify({
                'success': True,
                'audioUrl': result['secure_url']
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
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    
    # Run the app with SSL
    app.run(debug=True, ssl_context=context, host='0.0.0.0', port=5000) 