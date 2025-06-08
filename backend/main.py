from youtube_transcript_api import YouTubeTranscriptApi
from murf import Murf
from deep_translator import GoogleTranslator
import re
import yt_dlp
import subprocess
import os
import glob
import json
import math

# Use the full path to FFmpeg since it's installed in C:\ffmpeg\bin
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"

def get_video_id(url):
    # Extract video ID from YouTube URL
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    if video_id_match:
        return video_id_match.group(1)
    return None

def get_transcript_via_ytdlp(video_url):
    """Alternative method to get transcript using yt-dlp"""
    print("Trying to extract transcript using yt-dlp...")
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'en-US', 'en-GB'],
        'subtitlesformat': 'vtt',
        'skip_download': True,
        'outtmpl': 'subtitle_temp'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # Check if subtitles are available
            if 'subtitles' in info or 'automatic_captions' in info:
                print("Subtitles found, downloading...")
                ydl.download([video_url])
                
                # Look for downloaded subtitle files
                import glob
                subtitle_files = glob.glob('subtitle_temp*.vtt')
                
                if subtitle_files:
                    subtitle_file = subtitle_files[0]
                    print(f"Reading subtitle file: {subtitle_file}")
                    
                    # Parse VTT file and extract text
                    with open(subtitle_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple VTT parser - extract text lines
                    lines = content.split('\n')
                    text_lines = []
                    for line in lines:
                        line = line.strip()
                        # Skip VTT headers, timestamps, and empty lines
                        if (line and 
                            not line.startswith('WEBVTT') and 
                            not line.startswith('NOTE') and
                            '-->' not in line and
                            not line.startswith('<')):
                            text_lines.append(line)
                    
                    # Clean up subtitle file
                    try:
                        for file in subtitle_files:
                            os.remove(file)
                    except:
                        pass
                    
                    transcript = ' '.join(text_lines)
                    if transcript.strip():
                        return transcript
                    
            print("No subtitles found via yt-dlp")
            return None
            
    except Exception as e:
        print(f"Error extracting subtitles via yt-dlp: {e}")
        return None

def get_transcript(video_id, language_code='en'):
    print(f"Attempting to get transcript for video ID: {video_id}")
    try:
        # First, let's check what transcripts are available
        print("Checking available transcripts...")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        available_transcripts = []
        for transcript in transcript_list:
            available_transcripts.append({
                'language': transcript.language,
                'language_code': transcript.language_code,
                'is_generated': transcript.is_generated,
                'is_translatable': transcript.is_translatable
            })
        
        print(f"Available transcripts: For this video ({video_id}) transcripts are available in the following languages:")
        for t in available_transcripts:
            print(f"  - {t['language']} ({t['language_code']}) - Generated: {t['is_generated']}")
        
        # Try different language codes in order of preference
        language_preferences = ['en', 'en-US', 'en-GB', language_code]
        transcript_data = None
        
        for lang in language_preferences:
            try:
                print(f"Trying to get {lang} transcript...")
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                print(f"Found {lang} transcript")
                break
            except Exception as e:
                print(f"Could not get transcript in {lang}: {e}")
                continue
        
        # If specific languages didn't work, try to get any available transcript
        if transcript_data is None:
            try:
                print("Trying to get any available transcript...")
                # Get the first available transcript
                if available_transcripts:
                    first_transcript = available_transcripts[0]
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[first_transcript['language_code']])
                    print(f"Got transcript in {first_transcript['language']}")
                else:
                    print("No transcripts available for this video")
                    return None, None
            except Exception as e:
                print(f"Failed to get any transcript: {e}")
                return None, None
        
        if transcript_data is None:
            print("Could not retrieve transcript data")
            return None, None
        
        # Return both the raw transcript data (with timestamps) and the combined text
        full_text = ' '.join([entry['text'] for entry in transcript_data])
        print(f"Successfully retrieved transcript with {len(transcript_data)} segments")
        return transcript_data, full_text
        
    except Exception as e:
        print(f"Error accessing transcript: {e}")
        # Fallback to yt-dlp method
        print("Trying yt-dlp fallback method...")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        subtitle_text = get_transcript_via_ytdlp(video_url)
        
        if subtitle_text:
            # Convert subtitle text to transcript format
            # Split into segments (simplified - just by sentences)
            sentences = subtitle_text.split('. ')
            transcript_data = []
            
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    transcript_data.append({
                        'text': sentence.strip() + ('.' if not sentence.endswith('.') else ''),
                        'start': i * 3.0,  # Approximate timing
                        'duration': 3.0
                    })
            
            if transcript_data:
                full_text = ' '.join([entry['text'] for entry in transcript_data])
                print(f"Successfully retrieved transcript via yt-dlp with {len(transcript_data)} segments")
                return transcript_data, full_text
        
        return None, None

def download_video(url, output_path="original_video.mp4"):
    print("Downloading video...")
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': output_path,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

def combine_video_audio(video_path, audio_path, output_path="final_video.mp4"):
    print("Combining video with translated audio...")
    try:
        # Use ffmpeg to combine video and audio
        command = [
            FFMPEG_PATH,
            '-i', video_path,  # Input video
            '-i', audio_path,  # Input audio
            '-c:v', 'copy',    # Copy video stream without re-encoding
            '-c:a', 'aac',     # Convert audio to AAC
            '-map', '0:v:0',   # Use video from first input
            '-map', '1:a:0',   # Use audio from second input
            '-shortest',       # Match duration to shortest stream
            output_path
        ]
        subprocess.run(command, check=True)
        return output_path
    except Exception as e:
        print(f"Error combining video and audio: {e}")
        return None

def split_text_into_chunks(text, max_length=2000):
    """Split text into chunks that are under the character limit"""
    # Split by sentences first to keep coherent chunks
    sentences = re.split(r'[.!?]+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence would exceed the limit, start a new chunk
        if len(current_chunk) + len(sentence) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # If a single sentence is too long, split it by words
                words = sentence.split()
                for word in words:
                    if len(current_chunk) + len(word) + 1 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = word
                        else:
                            # If a single word is too long, just add it as is
                            chunks.append(word)
                    else:
                        current_chunk += " " + word if current_chunk else word
        else:
            current_chunk += ". " + sentence if current_chunk else sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def combine_audio_files(audio_files, output_file="combined_audio.wav"):
    """Combine multiple audio files into one using ffmpeg"""
    if len(audio_files) == 1:
        # If only one file, just rename it
        os.rename(audio_files[0], output_file)
        return output_file
    
    print(f"Combining {len(audio_files)} audio files...")
    try:
        # Create a file list for ffmpeg
        file_list_path = "audio_files_list.txt"
        with open(file_list_path, 'w') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file}'\n")
        
        # Use ffmpeg to concatenate audio files
        command = [
            FFMPEG_PATH,
            '-f', 'concat',
            '-safe', '0',
            '-i', file_list_path,
            '-c', 'copy',
            output_file
        ]
        subprocess.run(command, check=True)
        
        # Clean up temporary files
        os.remove(file_list_path)
        for audio_file in audio_files:
            try:
                os.remove(audio_file)
            except:
                pass
                
        return output_file
    except Exception as e:
        print(f"Error combining audio files: {e}")
        return None

def group_transcript_segments(transcript_data, max_chars=2500):
    """Group transcript segments to stay within character limits while preserving timing"""
    groups = []
    current_group = {
        'segments': [],
        'text': '',
        'start_time': None,
        'end_time': None
    }
    
    for segment in transcript_data:
        segment_text = segment['text'].strip()
        
        # Check if adding this segment would exceed the character limit
        if len(current_group['text']) + len(segment_text) + 1 > max_chars and current_group['segments']:
            # Save current group and start new one
            groups.append(current_group)
            current_group = {
                'segments': [segment],
                'text': segment_text,
                'start_time': segment['start'],
                'end_time': segment['start'] + segment['duration']
            }
        else:
            # Add to current group
            if not current_group['segments']:
                current_group['start_time'] = segment['start']
            
            current_group['segments'].append(segment)
            current_group['text'] += ' ' + segment_text if current_group['text'] else segment_text
            current_group['end_time'] = segment['start'] + segment['duration']
    
    # Add the last group if it has content
    if current_group['segments']:
        groups.append(current_group)
    
    return groups

def save_transcript_with_timestamps(transcript_data, output_file, is_translated=False):
    """Save transcript with timestamps to a file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Timestamp\tText\n")
            f.write("---------\t----\n")
            for segment in transcript_data:
                start_time = segment['start']
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                milliseconds = int((start_time % 1) * 1000)
                timestamp = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
                text = segment['text'] if not is_translated else segment.get('translated_text', segment['text'])
                f.write(f"{timestamp}\t{text}\n")
        print(f"Saved transcript to: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return False

def translate_and_create_timed_audio(transcript_data, target_language="es-ES", voice_id="es-ES-alvaro"):
    """Translate transcript segments and create audio files with proper timing"""
    print(f"Using voice_id: {voice_id} for target_language: {target_language}")
    client = Murf(
        api_key=os.getenv("MURF_API_KEY")  # Use environment variable or default key
    )
    
    # Group transcript segments
    print("Grouping transcript segments...")
    groups = group_transcript_segments(transcript_data)
    print(f"Created {len(groups)} groups from transcript")
    
    audio_segments = []
    translated_segments = []
    
    for i, group in enumerate(groups):
        print(f"Processing group {i+1}/{len(groups)} (duration: {group['end_time'] - group['start_time']:.2f}s)...")
        
        try:
            # Translate the group text
            print(f"Translating group {i+1}...")
            translation_response = client.text.translate(
                target_language=target_language,
                texts=[group['text']]
            )
            
            translated_text = translation_response.translations[0].translated_text
            print(f"Translation completed for group {i+1}!")
            
            # Store translated text with original timing
            for segment in group['segments']:
                segment_copy = segment.copy()
                segment_copy['translated_text'] = translated_text
                translated_segments.append(segment_copy)
            
            # Check if translated text is still too long
            if len(translated_text) > 3000:
                print(f"Translated text is {len(translated_text)} characters, splitting further...")
                # Split into smaller chunks and handle each
                chunks = split_text_into_chunks(translated_text, max_length=2500)
                
                chunk_duration = (group['end_time'] - group['start_time']) / len(chunks)
                
                for j, chunk in enumerate(chunks):
                    chunk_start = group['start_time'] + (j * chunk_duration)
                    chunk_end = group['start_time'] + ((j + 1) * chunk_duration)
                    
                    # Generate audio for this chunk
                    res = client.text_to_speech.stream(
                        text=chunk,
                        voice_id=voice_id
                    )
                    
                    audio_file = f"audio_segment_{i+1}_{j+1}.wav"
                    with open(audio_file, "wb") as f:
                        for audio_chunk in res:
                            f.write(audio_chunk)
                    
                    audio_segments.append({
                        'file': audio_file,
                        'start_time': chunk_start,
                        'end_time': chunk_end,
                        'duration': chunk_end - chunk_start
                    })
                    
                    print(f"Created audio segment {i+1}.{j+1}: {chunk_start:.2f}s - {chunk_end:.2f}s")
            else:
                # Generate audio for the entire group
                print(f"Converting group {i+1} to speech...")
                res = client.text_to_speech.stream(
                    text=translated_text,
                    voice_id=voice_id
                )
                
                audio_file = f"audio_segment_{i+1}.wav"
                with open(audio_file, "wb") as f:
                    for audio_chunk in res:
                        f.write(audio_chunk)
                
                audio_segments.append({
                    'file': audio_file,
                    'start_time': group['start_time'],
                    'end_time': group['end_time'],
                    'duration': group['end_time'] - group['start_time']
                })
                
                print(f"Created audio segment {i+1}: {group['start_time']:.2f}s - {group['end_time']:.2f}s")
                
        except Exception as e:
            print(f"Error processing group {i+1}: {e}")
            # Clean up any created files
            for segment in audio_segments:
                try:
                    os.remove(segment['file'])
                except:
                    pass
            return None
    
    # Save both original and translated transcripts
    save_transcript_with_timestamps(transcript_data, "original_transcript.txt")
    save_transcript_with_timestamps(translated_segments, "translated_transcript.txt", is_translated=True)
    
    return audio_segments

def adjust_audio_speed(input_file, speed_factor, output_file):
    """Adjust the speed of an audio file using FFmpeg's atempo filter"""
    try:
        # FFmpeg's atempo filter can only handle speed changes between 0.5x and 2.0x
        # For larger changes, we need to chain multiple atempo filters
        if speed_factor < 0.5 or speed_factor > 2.0:
            # Calculate how many atempo filters we need
            num_filters = int(abs(math.log2(speed_factor))) + 1
            atempo_chain = []
            remaining_speed = speed_factor
            
            for i in range(num_filters):
                if remaining_speed > 2.0:
                    atempo_chain.append("atempo=2.0")
                    remaining_speed /= 2.0
                elif remaining_speed < 0.5:
                    atempo_chain.append("atempo=0.5")
                    remaining_speed *= 2.0
                else:
                    atempo_chain.append(f"atempo={remaining_speed:.2f}")
                    break
            
            filter_complex = ",".join(atempo_chain)
        else:
            filter_complex = f"atempo={speed_factor:.2f}"
        
        command = [
            FFMPEG_PATH,
            '-i', input_file,
            '-filter_complex', filter_complex,
            '-y',
            output_file
        ]
        
        subprocess.run(command, check=True)
        return output_file
    except Exception as e:
        print(f"Error adjusting audio speed: {e}")
        return None

def create_synced_audio_track(audio_segments, total_duration):
    """Create a single audio track with proper timing using ffmpeg"""
    print("Creating synchronized audio track...")
    
    try:
        # First, combine all audio segments into one file
        temp_combined = "temp_combined.wav"
        filter_parts = []
        input_files = []
        
        for i, segment in enumerate(audio_segments):
            input_files.extend(['-i', segment['file']])
            filter_parts.append(f"[{i}]adelay={int(segment['start_time'] * 1000)}|{int(segment['start_time'] * 1000)}[delayed{i}]")
        
        # Mix all delayed audio segments
        if len(audio_segments) > 1:
            inputs = ''.join([f"[delayed{i}]" for i in range(len(audio_segments))])
            mix_filter = f"{inputs}amix=inputs={len(audio_segments)}:duration=longest[out]"
            filter_parts.append(mix_filter)
            output_map = "[out]"
        else:
            output_map = "[delayed0]"
        
        # Combine all filter parts
        complex_filter = ";".join(filter_parts)
        
        # Build ffmpeg command for initial combination
        command = [FFMPEG_PATH] + input_files + [
            '-filter_complex', complex_filter,
            '-map', output_map,
            '-t', str(total_duration),
            '-y',
            temp_combined
        ]
        
        print("Running ffmpeg to create initial combined audio...")
        subprocess.run(command, check=True)
        
        # Calculate the actual duration of the combined audio
        probe_command = [
            FFMPEG_PATH,
            '-i', temp_combined,
            '-f', 'null',
            '-'
        ]
        result = subprocess.run(probe_command, capture_output=True, text=True)
        
        # Extract duration from ffmpeg output
        duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", result.stderr)
        if duration_match:
            hours, minutes, seconds = map(float, duration_match.groups())
            actual_duration = hours * 3600 + minutes * 60 + seconds
            
            # Calculate speed adjustment factor
            if actual_duration > 0:
                speed_factor = actual_duration / total_duration
                print(f"Adjusting audio speed by factor: {speed_factor:.2f}")
                
                # Adjust the speed
                final_audio = adjust_audio_speed(temp_combined, speed_factor, "synced_translated_audio.wav")
                
                # Clean up temporary file
                try:
                    os.remove(temp_combined)
                except:
                    pass
                
                return final_audio
        
        # If we couldn't calculate the speed factor, return the unadjusted audio
        os.rename(temp_combined, "synced_translated_audio.wav")
        return "synced_translated_audio.wav"
        
    except Exception as e:
        print(f"Error creating synced audio track: {e}")
        return None

def map_language_code(murf_language_code):
    """Map Murf language codes to Google Translator language codes"""
    # Common language code mappings
    language_map = {
        'hi-IN': 'hi',  # Hindi
        'es-ES': 'es',  # Spanish
        'fr-FR': 'fr',  # French
        'de-DE': 'de',  # German
        'it-IT': 'it',  # Italian
        'pt-BR': 'pt',  # Portuguese
        'ru-RU': 'ru',  # Russian
        'ja-JP': 'ja',  # Japanese
        'ko-KR': 'ko',  # Korean
        'zh-CN': 'zh-CN',  # Chinese (Simplified)
        'ar-SA': 'ar',  # Arabic
        'nl-NL': 'nl',  # Dutch
        'pl-PL': 'pl',  # Polish
        'tr-TR': 'tr',  # Turkish
        'sv-SE': 'sv',  # Swedish
        'da-DK': 'da',  # Danish
        'fi-FI': 'fi',  # Finnish
        'no-NO': 'no',  # Norwegian
        'el-GR': 'el',  # Greek
        'he-IL': 'iw',  # Hebrew
        'id-ID': 'id',  # Indonesian
        'ms-MY': 'ms',  # Malay
        'th-TH': 'th',  # Thai
        'vi-VN': 'vi',  # Vietnamese
        'cs-CZ': 'cs',  # Czech
        'hu-HU': 'hu',  # Hungarian
        'ro-RO': 'ro',  # Romanian
        'sk-SK': 'sk',  # Slovak
        'uk-UA': 'uk',  # Ukrainian
        'bg-BG': 'bg',  # Bulgarian
        'hr-HR': 'hr',  # Croatian
        'sl-SI': 'sl',  # Slovenian
        'et-EE': 'et',  # Estonian
        'lv-LV': 'lv',  # Latvian
        'lt-LT': 'lt',  # Lithuanian
        'fa-IR': 'fa',  # Persian
        'bn-IN': 'bn',  # Bengali
        'ta-IN': 'ta',  # Tamil
        'te-IN': 'te',  # Telugu
        'kn-IN': 'kn',  # Kannada
        'ml-IN': 'ml',  # Malayalam
        'gu-IN': 'gu',  # Gujarati
        'mr-IN': 'mr',  # Marathi
        'pa-IN': 'pa',  # Punjabi
    }
    
    # Extract the base language code (e.g., 'hi' from 'hi-IN')
    base_code = murf_language_code.split('-')[0]
    
    # Return the mapped code if it exists, otherwise return the base code
    return language_map.get(murf_language_code, base_code)

def translate_transcript_file(input_file, target_language, output_file):
    """Translate a transcript file while maintaining timestamps using deep-translator"""
    try:
        # Map the language code to Google Translator format
        google_language_code = map_language_code(target_language)
        print(f"Using language code: {google_language_code} for translation")
        
        # Initialize translator
        translator = GoogleTranslator(source='auto', target=google_language_code)
        
        translated_lines = []
        with open(input_file, 'r', encoding='utf-8') as f:
            # Skip header lines
            header1 = f.readline()
            header2 = f.readline()
            translated_lines.extend([header1, header2])
            
            # Process each line
            for line in f:
                if line.strip():
                    timestamp, text = line.split('\t', 1)
                    # Translate the text using deep-translator
                    translated_text = translator.translate(text.strip())
                    translated_lines.append(f"{timestamp}\t{translated_text}\n")
        
        # Save translated transcript
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(translated_lines)
        
        print(f"Translated transcript saved to: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error translating transcript file: {e}")
        return None

def translate_and_convert_to_speech(text, target_language="es-ES", voice_id="es-ES-alvaro"):
    """Translate text using deep-translator and convert to speech using Murf AI"""
    try:
        # Map the language code to Google Translator format
        google_language_code = map_language_code(target_language)
        print(f"Using language code: {google_language_code} for translation")
        
        # Initialize translator
        translator = GoogleTranslator(source='auto', target=google_language_code)
        
        # Split text into manageable chunks
        print("Splitting text into chunks...")
        text_chunks = split_text_into_chunks(text)
        print(f"Text split into {len(text_chunks)} chunks")
        
        # Translate chunks
        translated_chunks = []
        for i, chunk in enumerate(text_chunks):
            print(f"Translating chunk {i+1}/{len(text_chunks)}...")
            translated_text = translator.translate(chunk)
            translated_chunks.append(translated_text)
            print(f"Translation completed for chunk {i+1}!")
        
        # Initialize Murf client for text-to-speech
        client = Murf(
            api_key=os.getenv("MURF_API_KEY"),
        )
        
        audio_files = []
        
        # Convert translated chunks to speech
        for i, translated_chunk in enumerate(translated_chunks):
            print(f"Converting chunk {i+1} to speech...")
            
            try:
                # Check if translated text is still too long and split further if needed
                if len(translated_chunk) > 3000:
                    print(f"Translated text is {len(translated_chunk)} characters, splitting further...")
                    # Split the translated text into smaller chunks
                    sub_chunks = split_text_into_chunks(translated_chunk, max_length=1500)
                    
                    for j, sub_chunk in enumerate(sub_chunks):
                        print(f"Converting sub-chunk {j+1}/{len(sub_chunks)} of chunk {i+1} to speech...")
                        res = client.text_to_speech.stream(
                            text=sub_chunk,
                            voice_id=voice_id
                        )
                        
                        # Save the audio to a file
                        output_file = f"translated_audio_chunk_{i+1}_{j+1}.wav"
                        with open(output_file, "wb") as f:
                            for audio_chunk in res:
                                f.write(audio_chunk)
                        
                        audio_files.append(output_file)
                        print(f"Sub-chunk {j+1} of chunk {i+1} completed!")
                else:
                    # Convert the translated text to speech
                    res = client.text_to_speech.stream(
                        text=translated_chunk,
                        voice_id=voice_id
                    )
                    
                    # Save the audio to a file
                    output_file = f"translated_audio_chunk_{i+1}.wav"
                    with open(output_file, "wb") as f:
                        for audio_chunk in res:
                            f.write(audio_chunk)
                    
                    audio_files.append(output_file)
                    print(f"Chunk {i+1} completed!")
                
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
                # Clean up any created files
                for audio_file in audio_files:
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                return None
        
        # Combine all audio files into one
        final_audio = combine_audio_files(audio_files, "translated_audio.wav")
        return final_audio
        
    except Exception as e:
        print(f"Error in translation and speech conversion: {e}")
        return None

def create_audio_from_transcript(transcript_file, voice_id, output_audio):
    """Create audio from transcript file using Murf AI"""
    try:
        client = Murf(
            api_key=os.getenv("MURF_API_KEY"),
        )
        
        # Read transcript and group by timestamps
        segments = []
        with open(transcript_file, 'r', encoding='utf-8') as f:
            # Skip header lines
            next(f)
            next(f)
            
            for line in f:
                if line.strip():
                    timestamp, text = line.split('\t', 1)
                    # Convert timestamp to seconds
                    minutes, seconds = timestamp.split(':')
                    seconds, milliseconds = seconds.split('.')
                    start_time = int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
                    
                    segments.append({
                        'start': start_time,
                        'text': text.strip()
                    })
        
        # Sort segments by start time
        segments.sort(key=lambda x: x['start'])
        
        # Create audio segments
        audio_segments = []
        for i, segment in enumerate(segments):
            print(f"Processing segment {i+1}/{len(segments)}...")
            
            try:
                # Convert text to speech
                res = client.text_to_speech.stream(
                    text=segment['text'],
                    voice_id=voice_id
                )
                
                # Save audio segment
                audio_file = f"audio_segment_{i+1}.wav"
                with open(audio_file, "wb") as f:
                    for audio_chunk in res:
                        f.write(audio_chunk)
                
                audio_segments.append({
                    'file': audio_file,
                    'start_time': segment['start'],
                    'duration': 0  # Will be calculated later
                })
                
            except Exception as e:
                print(f"Error processing segment {i+1}: {e}")
                # Clean up any created files
                for segment in audio_segments:
                    try:
                        os.remove(segment['file'])
                    except:
                        pass
                return None
        
        # Calculate total duration
        total_duration = max(segment['start'] + 5 for segment in segments)  # Add 5 seconds buffer
        
        # Create synchronized audio track
        final_audio = create_synced_audio_track(audio_segments, total_duration)
        if final_audio:
            # Rename to desired output file
            os.rename(final_audio, output_audio)
            return output_audio
        return None
        
    except Exception as e:
        print(f"Error creating audio from transcript: {e}")
        return None

def main():
    # Get YouTube URL from user
    youtube_url = input("Enter YouTube video URL: ")
    
    # Extract video ID
    video_id = get_video_id(youtube_url)
    if not video_id:
        print("Invalid YouTube URL")
        return

    # Get transcript with timestamps (trying YouTube Transcript API first, then yt-dlp as fallback)
    transcript_data, transcript_text = get_transcript(video_id)
    if not transcript_data and not transcript_text:
        print("YouTube Transcript API failed, trying yt-dlp method...")
        transcript_text = get_transcript_via_ytdlp(youtube_url)
        if not transcript_text:
            print("Could not get transcript using any method")
            return
        # If we got text from yt-dlp, we don't have timestamps, so fall back to old method
        transcript_data = None
        
    if transcript_data:
        print(f"Original transcript with timestamps: {len(transcript_data)} segments")
        print("Sample:", transcript_text[:200] + "..." if len(transcript_text) > 200 else transcript_text)
    else:
        print("Original transcript (no timestamps):", transcript_text[:200] + "..." if len(transcript_text) > 200 else transcript_text)
    
    # Get target language and voice ID
    target_language = input("Enter target language code (e.g., 'es-ES' for Spanish, 'hi-IN' for Hindi): ")
    voice_id = input("Enter Murf voice ID for the target language (e.g., 'es-ES-alvaro' for Spanish): ")
    
    # Download the original video
    video_path = download_video(youtube_url)
    if not video_path:
        print("Failed to download video")
        return
    
    # Save original transcript
    if transcript_data:
        save_transcript_with_timestamps(transcript_data, "original_transcript.txt")
        
        # Translate the transcript file
        translated_transcript = translate_transcript_file("original_transcript.txt", target_language, "translated_transcript.txt")
        if not translated_transcript:
            print("Failed to translate transcript")
            return
            
        # Create audio from translated transcript
        audio_path = create_audio_from_transcript(translated_transcript, voice_id, "translated_audio.wav")
        if not audio_path:
            print("Failed to create translated audio")
            return
    else:
        print("Using basic translation without timestamps...")
        # Fall back to old method
        audio_path = translate_and_convert_to_speech(transcript_text, target_language, voice_id)
        if not audio_path:
            print("Failed to create translated audio")
            return
    
    # Combine video with translated audio
    final_video = combine_video_audio(video_path, audio_path)
    if final_video:
        print(f"Final video with translated audio saved to: {final_video}")
    else:
        print("Failed to create final video")
        
    # Clean up temporary files
    try:
        os.remove(video_path)
        os.remove(audio_path)
        # Also clean up any remaining chunk files
        for i in range(1, 100):  # Clean up any leftover chunk files
            chunk_file = f"translated_audio_chunk_{i}.wav"
            if os.path.exists(chunk_file):
                os.remove(chunk_file)
            else:
                break
        # Clean up audio segment files
        for i in range(1, 100):
            segment_file = f"audio_segment_{i}.wav"
            if os.path.exists(segment_file):
                os.remove(segment_file)
            else:
                break
            # Also check for sub-segments
            for j in range(1, 10):
                sub_segment_file = f"audio_segment_{i}_{j}.wav"
                if os.path.exists(sub_segment_file):
                    os.remove(sub_segment_file)
    except:
        pass

if __name__ == "__main__":
    main()