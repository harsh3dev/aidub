from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, TranscriptsDisabled, CouldNotRetrieveTranscript
from youtube_transcript_api.formatters import TextFormatter
import re
from deep_translator import GoogleTranslator
import os
from murf import Murf
import requests
import tempfile
import uuid
import shutil
import time
import json
import subprocess
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import yt_dlp  # Alternative for transcript extraction
import random

# Load environment variables
load_dotenv()

# Check if API key is loaded
murf_api_key = os.getenv('MURF_API_KEY')
if not murf_api_key or murf_api_key == 'your_murf_api_key_here':
    print("WARNING: MURF_API_KEY not set or using placeholder value!")
    print("Please set your actual Murf API key in the .env file")
else:
    print(f"Murf API key loaded: {murf_api_key[:10]}...")

# Initialize Murf client
murf_client = Murf(
    api_key=murf_api_key
)

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

# Murf voice mapping
MURF_VOICE_MAP = {
    'hi-IN-shaan': 'hi-IN-shaan',        # Hindi Male
    'hi-IN-priya': 'hi-IN-priya',        # Hindi Female
    'en-US-terrell': 'en-US-terrell',    # English Male
    'en-US-sarah': 'en-US-sarah',        # English Female
    'es-ES-diego': 'es-ES-diego',        # Spanish Male
    'es-ES-lucia': 'es-ES-lucia',        # Spanish Female
    'fr-FR-antoine': 'fr-FR-antoine',    # French Male
    'fr-FR-marie': 'fr-FR-marie',        # French Female
    'de-DE-klaus': 'de-DE-klaus',        # German Male
    'de-DE-anna': 'de-DE-anna',          # German Female
    'it-IT-marco': 'it-IT-marco',        # Italian Male
    'it-IT-sofia': 'it-IT-sofia',        # Italian Female
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
    """Get transcript for a YouTube video with improved error handling."""
    try:
        print(f"Attempting to get transcript for video ID: {video_id}")
        
        # Setup session with random user agent to avoid blocking
        session = setup_youtube_session()
        
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))  # Random delay between 1-3 seconds
        
        # Try to get transcript in any available language with retry logic
        max_list_retries = 3
        transcript_list = None
        
        for attempt in range(max_list_retries):
            try:
                print(f"Attempting to list transcripts (attempt {attempt + 1}/{max_list_retries})...")
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                print(f"Available transcripts found for video {video_id}")
                break
            except Exception as list_error:
                print(f"Error listing transcripts (attempt {attempt + 1}): {list_error}")
                if attempt < max_list_retries - 1:
                    wait_time = random.uniform(2, 5) * (attempt + 1)
                    print(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    raise list_error
        
        # List available transcripts for debugging
        available_languages = []
        for transcript in transcript_list:
            print(f"  - {transcript.language}: {transcript.language_code} (generated: {transcript.is_generated})")
            available_languages.append(transcript.language_code)
        
        # Try multiple language codes in order of preference
        language_preferences = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU']
        transcript = None
        
        # First try preferred English variants
        for lang_code in language_preferences:
            if lang_code in available_languages:
                try:
                    print(f"Trying to get {lang_code} transcript...")
                    transcript = transcript_list.find_transcript([lang_code])
                    print(f"Found {lang_code} transcript: {transcript.language_code}")
                    break
                except Exception as e:
                    print(f"Failed to get {lang_code} transcript: {e}")
                    continue
        
        # If no English transcript found, try any available transcript
        if not transcript:
            print("English transcript not found, trying any available transcript...")
            for available_transcript in transcript_list:
                try:
                    transcript = available_transcript
                    print(f"Using transcript in language: {transcript.language_code}")
                    break
                except Exception as e:
                    print(f"Failed to use transcript {available_transcript.language_code}: {e}")
                    continue
        
        if not transcript:
            raise Exception("No accessible transcript found")
        
        # Get transcript data with improved retry logic and error handling
        max_retries = 3  # Reduced from 5 to avoid excessive delays
        retry_count = 0
        transcript_data = None
        last_error = None
        
        while retry_count < max_retries:
            try:
                print(f"Fetching transcript data (attempt {retry_count + 1}/{max_retries})...")
                
                # Add progressive delay between retries to avoid rate limiting
                if retry_count > 0:
                    wait_time = min(5 + (retry_count * 3), 12)  # Progressive backoff, max 12 seconds
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                
                # Clear any cached session data to avoid stale connections
                session = setup_youtube_session()
                
                # Try to fetch transcript data with session management
                transcript_data = transcript.fetch()
                
                if transcript_data and len(transcript_data) > 0:
                    print(f"Successfully got {len(transcript_data)} transcript segments")
                    break
                else:
                    raise Exception("Empty transcript data received")
                    
            except Exception as e:
                last_error = str(e)
                print(f"Error fetching transcript data (attempt {retry_count + 1}): {last_error}")
                
                # Handle specific XML parsing errors - these usually indicate rate limiting or API issues
                if ("no element found" in last_error.lower() or 
                    "xml" in last_error.lower() or 
                    "parsing" in last_error.lower() or
                    "not well-formed" in last_error.lower()):
                    print("XML parsing error detected - likely YouTube API rate limiting or temporary issue")
                    
                    # For XML parsing errors, immediately try the fallback method after first failure
                    if retry_count == 0:
                        print("Trying yt-dlp fallback immediately due to XML parsing error...")
                        fallback_transcript, fallback_lang = get_transcript_via_ytdlp(video_id)
                        if fallback_transcript:
                            print("Successfully retrieved transcript using yt-dlp fallback")
                            return fallback_transcript, fallback_lang
                
                retry_count += 1
        
        if not transcript_data:
            # Try alternative approach with different transcript if available
            print("Primary transcript failed, trying alternative transcripts...")
            for alt_transcript in transcript_list:
                if alt_transcript != transcript:
                    try:
                        print(f"Trying alternative transcript: {alt_transcript.language_code}")
                        time.sleep(2)  # Delay before trying alternative
                        transcript_data = alt_transcript.fetch()
                        if transcript_data and len(transcript_data) > 0:
                            print(f"Successfully got alternative transcript with {len(transcript_data)} segments")
                            transcript = alt_transcript
                            break
                    except Exception as alt_e:
                        print(f"Alternative transcript {alt_transcript.language_code} also failed: {alt_e}")
                        continue
        
        if not transcript_data:
            raise Exception(f"Could not fetch transcript data after {max_retries} attempts and trying alternatives. Last error: {last_error}")
        
        # Format transcript with error handling
        try:
            formatter = TextFormatter()
            formatted_transcript = formatter.format_transcript(transcript_data)
              # Clean up the transcript
            formatted_transcript = re.sub(r'\n+', '\n', formatted_transcript)  # Remove multiple newlines
            formatted_transcript = formatted_transcript.strip()  # Remove leading/trailing whitespace
            
            if not formatted_transcript:
                # Fallback: manually format transcript if formatter fails
                print("Formatter produced empty result, using manual formatting...")
                formatted_transcript = ' '.join([entry.get('text', '') for entry in transcript_data])
                formatted_transcript = formatted_transcript.strip()
            
            if not formatted_transcript:
                raise Exception("Transcript is empty after all formatting attempts")
                
        except Exception as format_error:
            print(f"Formatting error: {format_error}")
            # Manual fallback formatting
            formatted_transcript = ' '.join([entry.get('text', '') for entry in transcript_data])
            if not formatted_transcript:
                raise Exception("Could not format transcript data")
        
        print("Successfully formatted transcript")
        return formatted_transcript, transcript.language_code
    
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video")
        raise Exception("This video has disabled captions/subtitles")
    except NoTranscriptFound:
        print("No transcript found for this video")
        raise Exception("No captions/subtitles are available for this video")
    except CouldNotRetrieveTranscript:
        print("Could not retrieve transcript")
        raise Exception("Could not retrieve captions for this video - video may be private or restricted")
    except Exception as e:
        error_msg = str(e)
        print(f"YouTube Transcript API failed: {error_msg}")
        
        # Try fallback method using yt-dlp
        print("Attempting fallback method using yt-dlp...")
        fallback_transcript, fallback_lang = get_transcript_via_ytdlp(video_id)
        
        if fallback_transcript:
            print("Successfully retrieved transcript using fallback method")
            return fallback_transcript, fallback_lang
        
        # If fallback also fails, provide more specific error messages
        if "no element found" in error_msg.lower():
            raise Exception("Failed to parse video data - this may be due to rate limiting or network issues. Please try again in a few minutes.")
        elif "video unavailable" in error_msg.lower():
            raise Exception("This video is unavailable or private")
        elif "http" in error_msg.lower() and ("40" in error_msg or "50" in error_msg):
            raise Exception("Network error occurred while fetching video data. Please check your connection and try again.")
        else:
            raise Exception(f"Could not get transcript using any method: {error_msg}")

def get_transcript_via_ytdlp(video_id):
    """Fallback method to get transcript using yt-dlp when YouTube Transcript API fails."""
    try:
        print(f"Attempting to get transcript via yt-dlp for video ID: {video_id}")
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Configure yt-dlp options for subtitle extraction
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU'],
            'subtitlesformat': 'vtt',
            'skip_download': True,
            'outtmpl': f'temp_subtitle_{video_id}',
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info to check available subtitles
            info = ydl.extract_info(video_url, download=False)
            
            # Check if subtitles are available
            has_subtitles = False
            if 'subtitles' in info and info['subtitles']:
                has_subtitles = True
                print("Manual subtitles found")
            elif 'automatic_captions' in info and info['automatic_captions']:
                has_subtitles = True
                print("Automatic captions found")
            
            if not has_subtitles:
                raise Exception("No subtitles available via yt-dlp")
            
            # Download subtitles
            ydl.download([video_url])
            
            # Look for downloaded subtitle files
            import glob
            subtitle_patterns = [
                f'temp_subtitle_{video_id}.*.vtt',
                f'temp_subtitle_{video_id}.vtt'
            ]
            
            subtitle_files = []
            for pattern in subtitle_patterns:
                subtitle_files.extend(glob.glob(pattern))
            
            if not subtitle_files:
                raise Exception("No subtitle files were downloaded")
            
            # Use the first available subtitle file
            subtitle_file = subtitle_files[0]
            print(f"Reading subtitle file: {subtitle_file}")
            
            # Parse VTT file and extract text
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse VTT content
            lines = content.split('\n')
            text_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip VTT headers, timestamps, style tags, and empty lines
                if (line and 
                    not line.startswith('WEBVTT') and 
                    not line.startswith('NOTE') and
                    not line.startswith('STYLE') and
                    '-->' not in line and
                    not line.startswith('<') and
                    not line.endswith('>') and
                    not line.isdigit()):
                    # Clean up subtitle artifacts
                    line = re.sub(r'<[^>]+>', '', line)  # Remove HTML tags
                    line = re.sub(r'\{[^}]+\}', '', line)  # Remove styling tags
                    if line.strip():
                        text_lines.append(line.strip())
            
            # Clean up subtitle files
            try:
                for file in subtitle_files:
                    if os.path.exists(file):
                        os.remove(file)
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up subtitle files: {cleanup_error}")
            
            # Join text and clean up
            transcript = ' '.join(text_lines)
            transcript = re.sub(r'\s+', ' ', transcript)  # Normalize whitespace
            transcript = transcript.strip()
            
            if not transcript:
                raise Exception("Extracted transcript is empty")
            
            print(f"Successfully extracted transcript via yt-dlp: {len(transcript)} characters")
            return transcript, 'en'  # Assume English for yt-dlp extracted content
            
    except Exception as e:
        print(f"yt-dlp transcript extraction failed: {e}")
        return None, None

def translate_text(text, target_language):
    """Translate text using Murf API."""
    try:
        # Map the language code
        mapped_language = map_language_code(target_language)
        print(f"Translating text to {mapped_language} (mapped from {target_language})...")
        
        # Split text into chunks to avoid hitting translation limits
        chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
        print(f"Split text into {len(chunks)} chunks")
        translated_chunks = []
        
        translator = GoogleTranslator(source='auto', target=mapped_language)
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            print(f"Translating chunk {i+1}/{len(chunks)}...")
            try:
                translated = translator.translate(chunk)
                
                # Format response to match Murf's API response structure
                mock_response = type('MockResponse', (), {
                    'translations': [
                        type('Translation', (), {
                            'translated_text': translated
                        })()
                    ]
                })
                
                # Extract translated text (matching Murf's response structure)
                translated_texts = [translation.translated_text for translation in mock_response.translations]
                translated_chunks.extend(translated_texts)
                
                print(f"Chunk {i+1} translated successfully")
                
            except Exception as chunk_error:
                print(f"Error translating chunk {i+1}: {str(chunk_error)}")
                raise Exception(f"Failed to translate chunk {i+1}: {str(chunk_error)}")
        
        # Join all translated chunks
        result = ' '.join(translated_chunks)
        print("Translation completed successfully")
        return result
        
    except Exception as e:
        print(f"Error translating text: {str(e)}")
        raise Exception(f"Translation failed: {str(e)}")

def text_to_speech(text, voice_id):
    """Convert text to speech using Murf AI."""
    try:
        print(f"Converting text to speech using Murf with voice: {voice_id}...")
        print(f"Text length: {len(text)} characters")
        
        # Check if text exceeds Murf's limit (3000 characters)
        max_length = 2800  # Use slightly less than 3000 to be safe
        
        if len(text) <= max_length:
            # Generate audio using Murf API directly
            res = murf_client.text_to_speech.generate(
                text=text,
                voice_id=voice_id,
            )
            
            print(f"Generated audio file URL: {res.audio_file}")
            
            # Create a unique filename
            filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(AUDIO_DIR, filename)
            
            # Download and save the audio file response = requests.get(res.audio_file)
            response.raise_for_status()
            
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            print("Audio generation completed successfully")
            return filename
        else:
            # Split text into chunks and combine audio files
            print(f"Text is too long ({len(text)} chars), splitting into chunks...")
            
            # Split text into chunks of reasonable size
            chunks = []
            # Split by sentences first, then combine sentences into chunks
            sentences = re.split(r'(?<=[.!?])\s+', text)
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # Test if adding this sentence would exceed the limit
                test_chunk = current_chunk + " " + sentence if current_chunk else sentence
                
                if len(test_chunk) <= max_length:
                    current_chunk = test_chunk
                else:
                    # If current_chunk is empty and single sentence is too long, split it further
                    if not current_chunk and len(sentence) > max_length:
                        # Split long sentence into smaller parts
                        words = sentence.split()
                        temp_chunk = ""
                        for word in words:
                            test_word_chunk = temp_chunk + " " + word if temp_chunk else word
                            if len(test_word_chunk) <= max_length:
                                temp_chunk = test_word_chunk
                            else:
                                if temp_chunk:
                                    chunks.append(temp_chunk)
                                temp_chunk = word
                        if temp_chunk:
                            chunks.append(temp_chunk)
                    else:
                        # Add current chunk and start new one
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
            
            # Add the last chunk if it exists
            if current_chunk:
                chunks.append(current_chunk)
            
            print(f"Split text into {len(chunks)} chunks")
            
            # Debug: print chunk sizes
            for i, chunk in enumerate(chunks):
                print(f"Chunk {i+1}: {len(chunk)} characters")
            
            # Generate audio for each chunk
            chunk_files = []
            for i, chunk in enumerate(chunks):
                print(f"Generating audio for chunk {i+1}/{len(chunks)}...")
                
                res = murf_client.text_to_speech.generate(
                    text=chunk,
                    voice_id=voice_id,
                )
                
                # Download chunk audio
                chunk_filename = f"{uuid.uuid4()}_chunk_{i+1}.mp3"
                chunk_path = os.path.join(AUDIO_DIR, chunk_filename)
                
                response = requests.get(res.audio_file)
                response.raise_for_status()
                
                with open(chunk_path, 'wb') as f:
                    f.write(response.content)
                
                chunk_files.append(chunk_path)
                print(f"Chunk {i+1} completed")
            
            # Use pydub to concatenate MP3 files (more reliable than ffmpeg for this case)
            final_filename = f"{uuid.uuid4()}.mp3"
            final_path = os.path.join(AUDIO_DIR, final_filename)
            
            try:
                from pydub import AudioSegment
                print("Using pydub to combine audio chunks...")
                
                # Load the first audio file
                combined = AudioSegment.from_mp3(chunk_files[0])
                
                # Add each subsequent file
                for chunk_file in chunk_files[1:]:
                    audio_segment = AudioSegment.from_mp3(chunk_file)
                    combined += audio_segment
                
                # Export the combined audio
                combined.export(final_path, format="mp3")
                
                # Clean up chunk files
                for chunk_file in chunk_files:
                    if os.path.exists(chunk_file):
                        os.remove(chunk_file)
                
                print("Audio chunks combined successfully with pydub")
                
            except ImportError:
                print("pydub not available, using simple concatenation...")
                
                # Fallback to simple concatenation (may have audio glitches)
                with open(final_path, 'wb') as final_file:
                    for chunk_file in chunk_files:
                        with open(chunk_file, 'rb') as cf:
                            final_file.write(cf.read())
                        # Clean up chunk file                        os.remove(chunk_file)
                
                print("Audio chunks combined with simple concatenation")
            
            return final_filename
    
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
        print(f"Received request to translate video: {video_url}, voice ID: {voice_id}, target language: {target_language}")

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
                return jsonify({'error': 'Translation failed'}), 500            # Generate audio file using Murf AI
            audio_filename = text_to_speech(translated_text, voice_id)
            audio_path = os.path.join(AUDIO_DIR, audio_filename)

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

# User agents for rotation to avoid blocking
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
]

def setup_youtube_session():
    """Setup a session with random user agent for YouTube requests."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

if __name__ == '__main__':
    # Configure Flask to avoid auto-reload issues during audio generation
    app.run(
        debug=False,  # Disable debug mode to prevent auto-reload interruptions
        port=5000,
        host='localhost'
    )