from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, TranscriptsDisabled, CouldNotRetrieveTranscript
from youtube_transcript_api.formatters import TextFormatter
import re
from deep_translator import GoogleTranslator
import os
from gtts import gTTS
import tempfile
import uuid
import shutil
import time
import json
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

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

# Create a directory for audio files if it doesn't exist
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio_files')
os.makedirs(AUDIO_DIR, exist_ok=True)

# Language code mapping
LANGUAGE_MAP = {
    'hi-IN': 'hi',  # Hindi
    'en-US': 'en',  # English (US)
    'en-GB': 'en',  # English (UK)
    'es-ES': 'es',  # Spanish
    'fr-FR': 'fr',  # French
    'de-DE': 'de',  # German
    'it-IT': 'it',  # Italian
    'pt-BR': 'pt',  # Portuguese (Brazil)
    'ru-RU': 'ru',  # Russian
    'ja-JP': 'ja',  # Japanese
    'ko-KR': 'ko',  # Korean
    'zh-CN': 'zh-CN',  # Chinese (Simplified)
    'zh-TW': 'zh-TW',  # Chinese (Traditional)
    'ar-SA': 'ar',  # Arabic
    'nl-NL': 'nl',  # Dutch
    'pl-PL': 'pl',  # Polish
    'tr-TR': 'tr',  # Turkish
    'sv-SE': 'sv',  # Swedish
    'da-DK': 'da',  # Danish
    'fi-FI': 'fi',  # Finnish
    'no-NO': 'no',  # Norwegian
    'el-GR': 'el',  # Greek
    'cs-CZ': 'cs',  # Czech
    'hu-HU': 'hu',  # Hungarian
    'ro-RO': 'ro',  # Romanian
    'sk-SK': 'sk',  # Slovak
    'bg-BG': 'bg',  # Bulgarian
    'hr-HR': 'hr',  # Croatian
    'sl-SI': 'sl',  # Slovenian
    'et-EE': 'et',  # Estonian
    'lv-LV': 'lv',  # Latvian
    'lt-LT': 'lt',  # Lithuanian
    'uk-UA': 'uk',  # Ukrainian
    'vi-VN': 'vi',  # Vietnamese
    'th-TH': 'th',  # Thai
    'id-ID': 'id',  # Indonesian
    'ms-MY': 'ms',  # Malay
    'fil-PH': 'tl',  # Filipino
    'hi': 'hi',     # Hindi (direct code)
    'en': 'en',     # English (direct code)
    'es': 'es',     # Spanish (direct code)
    'fr': 'fr',     # French (direct code)
    'de': 'de',     # German (direct code)
    'it': 'it',     # Italian (direct code)
    'pt': 'pt',     # Portuguese (direct code)
    'ru': 'ru',     # Russian (direct code)
    'ja': 'ja',     # Japanese (direct code)
    'ko': 'ko',     # Korean (direct code)
    'zh': 'zh-CN',  # Chinese (default to Simplified)
    'ar': 'ar',     # Arabic (direct code)
    'nl': 'nl',     # Dutch (direct code)
    'pl': 'pl',     # Polish (direct code)
    'tr': 'tr',     # Turkish (direct code)
    'sv': 'sv',     # Swedish (direct code)
    'da': 'da',     # Danish (direct code)
    'fi': 'fi',     # Finnish (direct code)
    'no': 'no',     # Norwegian (direct code)
    'el': 'el',     # Greek (direct code)
    'cs': 'cs',     # Czech (direct code)
    'hu': 'hu',     # Hungarian (direct code)
    'ro': 'ro',     # Romanian (direct code)
    'sk': 'sk',     # Slovak (direct code)
    'bg': 'bg',     # Bulgarian (direct code)
    'hr': 'hr',     # Croatian (direct code)
    'sl': 'sl',     # Slovenian (direct code)
    'et': 'et',     # Estonian (direct code)
    'lv': 'lv',     # Latvian (direct code)
    'lt': 'lt',     # Lithuanian (direct code)
    'uk': 'uk',     # Ukrainian (direct code)
    'vi': 'vi',     # Vietnamese (direct code)
    'th': 'th',     # Thai (direct code)
    'id': 'id',     # Indonesian (direct code)
    'ms': 'ms',     # Malay (direct code)
    'tl': 'tl',     # Filipino (direct code)
}

def map_language_code(language_code):
    """Map language code to Google Translator format."""
    # Convert to lowercase for case-insensitive matching
    language_code = language_code.lower()
    
    # Check if the code is in our mapping
    if language_code in LANGUAGE_MAP:
        return LANGUAGE_MAP[language_code]
    
    # If not found, try to extract the base language code (e.g., 'hi' from 'hi-IN')
    base_code = language_code.split('-')[0]
    if base_code in LANGUAGE_MAP:
        return LANGUAGE_MAP[base_code]
    
    # If still not found, return the original code
    return language_code

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:embed\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id):
    """Get transcript for a YouTube video."""
    try:
        print(f"Attempting to get transcript for video ID: {video_id}")
        
        # Try to get transcript in any available language
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print(f"Available transcripts: For this video ({video_id}) transcripts are available in the following languages:")
        
        # First try to get English transcript
        try:
            print("Trying to get English transcript...")
            transcript = transcript_list.find_transcript(['en'])
            print("Found English transcript")
        except NoTranscriptFound:
            print("English transcript not found, trying any available transcript...")
            # If English not available, get the first available transcript
            transcript = transcript_list.find_transcript()
            print(f"Found transcript in language: {transcript.language_code}")
        
        # Get transcript data with retries
        max_retries = 5  # Increased from 3 to 5
        retry_count = 0
        transcript_data = None
        last_error = None
        
        while retry_count < max_retries:
            try:
                print(f"Fetching transcript data (attempt {retry_count + 1}/{max_retries})...")
                transcript_data = transcript.fetch()
                print(f"Got {len(transcript_data)} transcript segments")
                break
            except Exception as e:
                last_error = str(e)
                print(f"Error fetching transcript data (attempt {retry_count + 1}): {last_error}")
                retry_count += 1
                if retry_count < max_retries:
                    print("Retrying with preserved formatting...")
                    try:
                        transcript_data = transcript.fetch(preserve_formatting=True)
                        print(f"Got {len(transcript_data)} transcript segments with preserved formatting")
                        break
                    except Exception as e2:
                        print(f"Error fetching with preserved formatting: {str(e2)}")
                        time.sleep(1)  # Add delay between retries
                else:
                    # Try alternative method as last resort
                    try:
                        print("Trying alternative transcript fetching method...")
                        transcript_data = transcript.fetch(manual_captions=True)
                        print(f"Got {len(transcript_data)} transcript segments using alternative method")
                        break
                    except Exception as e3:
                        print(f"Alternative method failed: {str(e3)}")
                        raise Exception(f"Could not fetch transcript data after {max_retries} attempts. Last error: {last_error}")
        
        if not transcript_data:
            raise Exception("No transcript data received")
        
        # Format transcript with timestamps
        formatter = TextFormatter()
        formatted_transcript = formatter.format_transcript(transcript_data)
        
        # Clean up the transcript
        formatted_transcript = re.sub(r'\n+', '\n', formatted_transcript)  # Remove multiple newlines
        formatted_transcript = formatted_transcript.strip()  # Remove leading/trailing whitespace
        
        if not formatted_transcript:
            raise Exception("Transcript is empty after formatting")
        
        print("Successfully formatted transcript")
        return formatted_transcript, transcript.language_code
        
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video")
        raise Exception("This video does not have captions available")
    except NoTranscriptFound:
        print("No transcript found for this video")
        raise Exception("No captions are available for this video")
    except CouldNotRetrieveTranscript:
        print("Could not retrieve transcript")
        raise Exception("Could not retrieve captions for this video")
    except Exception as e:
        print(f"Error getting transcript: {str(e)}")
        raise Exception(f"Could not get transcript: {str(e)}")

def translate_text(text, target_language):
    """Translate text using Google Translate."""
    try:
        # Map the language code
        mapped_language = map_language_code(target_language)
        print(f"Translating text to {mapped_language} (mapped from {target_language})...")
        
        # Split text into chunks to avoid hitting translation limits
        chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
        print(f"Split text into {len(chunks)} chunks")
        translated_chunks = []
        
        translator = GoogleTranslator(source='auto', target=mapped_language)
        for i, chunk in enumerate(chunks):
            print(f"Translating chunk {i+1}/{len(chunks)}...")
            translated = translator.translate(chunk)
            translated_chunks.append(translated)
        
        result = ' '.join(translated_chunks)
        print("Translation completed successfully")
        return result
    except Exception as e:
        print(f"Error translating text: {str(e)}")
        raise Exception(f"Translation failed: {str(e)}")

def text_to_speech(text, language):
    """Convert text to speech using gTTS."""
    try:
        # Map the language code
        mapped_language = map_language_code(language)
        print(f"Converting text to speech in {mapped_language} (mapped from {language})...")
        
        # Create a unique filename
        filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_DIR, filename)
        
        # Split text into chunks to avoid hitting gTTS limits
        chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
        print(f"Split text into {len(chunks)} chunks for TTS")
        audio_files = []
        
        for i, chunk in enumerate(chunks):
            print(f"Generating audio for chunk {i+1}/{len(chunks)}...")
            chunk_filename = f"{uuid.uuid4()}.mp3"
            chunk_path = os.path.join(AUDIO_DIR, chunk_filename)
            
            tts = gTTS(text=chunk, lang=mapped_language, slow=False)
            tts.save(chunk_path)
            audio_files.append(chunk_path)
        
        # If we have multiple chunks, combine them
        if len(audio_files) > 1:
            print("Combining audio chunks...")
            from pydub import AudioSegment
            combined = AudioSegment.from_mp3(audio_files[0])
            for audio_file in audio_files[1:]:
                combined += AudioSegment.from_mp3(audio_file)
            combined.export(audio_path, format="mp3")
            
            # Clean up chunk files
            for file in audio_files:
                os.remove(file)
        else:
            # If only one chunk, just rename it
            os.rename(audio_files[0], audio_path)
        
        print("Audio generation completed successfully")
        return filename
    except Exception as e:
        print(f"Error converting text to speech: {str(e)}")
        raise Exception(f"Text to speech conversion failed: {str(e)}")

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files."""
    try:
        return send_file(
            os.path.join(AUDIO_DIR, filename),
            mimetype='audio/mpeg'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

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
            video_id = extract_video_id(video_url)
            if not video_id:
                return jsonify({'error': 'Invalid YouTube URL'}), 400

            transcript_data, source_language = get_transcript(video_id)
            if not transcript_data:
                return jsonify({'error': 'Could not get transcript'}), 400

            # Translate the transcript
            translated_text = translate_text(transcript_data, target_language)
            if not translated_text:
                return jsonify({'error': 'Translation failed'}), 500

            # Generate audio file
            audio_filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            
            # Convert text to speech
            tts = gTTS(text=translated_text, lang=map_language_code(target_language))
            tts.save(audio_path)

            # Upload to Cloudinary
            try:
                result = cloudinary.uploader.upload(
                    audio_path,
                    resource_type='raw',
                    public_id=f'translated_audio_{video_id}',
                    overwrite=True
                )
                
                # Clean up local file
                os.remove(audio_path)
                
                return jsonify({
                    'success': True,
                    'audioUrl': result['secure_url']
                })
            except Exception as e:
                print(f"Cloudinary upload error: {str(e)}")
                # Fallback to local file serving if Cloudinary fails
                return jsonify({
                    'success': True,
                    'audioUrl': f"http://localhost:5000/audio/{audio_filename}"
                })

        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Clean up old audio files periodically
def cleanup_old_files():
    """Remove audio files older than 1 hour."""
    try:
        current_time = time.time()
        for filename in os.listdir(AUDIO_DIR):
            filepath = os.path.join(AUDIO_DIR, filename)
            if os.path.getmtime(filepath) < current_time - 3600:  # 1 hour
                os.remove(filepath)
    except Exception as e:
        print(f"Error cleaning up files: {str(e)}")

if __name__ == '__main__':
    app.run(
        debug=True,
        port=5000,
        host='localhost'
    ) 