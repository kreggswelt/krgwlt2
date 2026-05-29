import os
import re
import datetime
import subprocess
import random
from pathlib import Path
from urllib.parse import quote
import requests
import time
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------- CONFIG ----------------

# LANGUAGE SETTINGS (Change this for different languages)
LANGUAGE_CONFIG = {
    "name": "German",          # Language name for prompts
    "native_name": "auf Deutsch",   # Native name for instructions
    "voice": "de-DE-KatjaNeural", # Edge-TTS voice
    "vosk_model": "vosk-model-small-de-0.15",
    "vosk_url": "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip",
    "vosk_zip": "vosk-model-de.zip",
    "subtitle_font": "Arial"
}

# For German, you would just change to:
# LANGUAGE_CONFIG = {
#     "name": "German",
#     "native_name": "auf Deutsch",
#     "voice": "de-DE-KatjaNeural",
#     "vosk_model": "vosk-model-small-de-0.15", 
#     ...
# }

NUM_IMAGES = 8  # 8 unique scenes (faster generation)
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920
IMAGE_MODEL = "flux"

STORY_MAX_WORDS = 130

TOPICS_FILE = "topics.txt"

IMAGES_DIR = Path("images")
OUTPUT_DIR = Path("output")
AUDIO_DIR = Path("audio")

MUSIC_FILE = AUDIO_DIR / "music.mp3"

NARRATION_FILE = OUTPUT_DIR / "narration.mp3"
STORY_FILE = OUTPUT_DIR / "story.txt"
SCENES_FILE = OUTPUT_DIR / "scenes.txt"
SUBS_FILE = OUTPUT_DIR / "subtitles.ass"
ANIMATED_VIDEO = OUTPUT_DIR / "animated.mp4"
VIDEO_WITH_SUBS = OUTPUT_DIR / "video_with_subs.mp4"
FINAL_VIDEO = OUTPUT_DIR / "final_video.mp4"

WHISPER_MODEL_NAME = "small"

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
if not POLLINATIONS_API_KEY:
    print("⚠️ WARNING: POLLINATIONS_API_KEY not found in environment. API calls may fail or fallback to free tier/errors.")

# ----------------------------------------

def ensure_dirs():
    IMAGES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    AUDIO_DIR.mkdir(exist_ok=True)
    
    # Clean old images
    for f in IMAGES_DIR.glob("*.jpg"):
        f.unlink()
        
    # Clean old output files to prevent staying state
    for f in OUTPUT_DIR.glob("*"):
        if f.is_file() and f.name != ".gitkeep":
            try:
                f.unlink()
            except Exception:
                pass

def get_all_used_topics():
    """Get all previously used topics to prevent duplicates."""
    used = set()
    if os.path.exists("used_topics.txt"):
        with open("used_topics.txt", "r", encoding="utf-8") as f:
            for line in f:
                # Extract topic from "YYYY-MM-DD: Topic" format
                if ": " in line:
                    topic = line.split(": ", 1)[1].strip()
                    used.add(topic.lower())
                else:
                    used.add(line.strip().lower())
    return used

def choose_topic_for_today():
    """Select and consume a topic. Auto-generates new unique topics when running low."""
    # Check if we need to generate initial topics
    if not os.path.exists(TOPICS_FILE):
        print(f"[topics] {TOPICS_FILE} nicht gefunden! Generiere 500 initiale Themen...")
        from generate_topics import generate_german_kids_topics, save_topics_to_file
        new_topics = generate_german_kids_topics(500)
        save_topics_to_file(new_topics)
    
    # Read topics with error handling
    try:
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            topics = [line.strip() for line in f if line.strip()]
        print(f"[topics] 📚 Geladene Themen: {len(topics)}")
    except Exception as e:
        print(f"[topics] ❌ FEHLER beim Lesen von {TOPICS_FILE}: {e}")
        return "Der kleine Bär im Wald"
    
    # If running low on topics (< 50), generate more with strict duplicate checking
    if len(topics) < 50:
        print(f"[topics] ⚠️  Nur noch {len(topics)} Themen übrig. Generiere 200 neue EINZIGARTIGE Themen...")
        from generate_topics import generate_german_kids_topics
        
        # Get all used topics to prevent duplicates
        used_topics = get_all_used_topics()
        existing_topics_lower = set(t.lower() for t in topics)
        all_existing = used_topics.union(existing_topics_lower)
        
        print(f"[topics] Bereits verwendet/vorhanden: {len(all_existing)} Themen")
        
        # Generate new topics and filter out duplicates
        attempts = 0
        new_unique_topics = []
        while len(new_unique_topics) < 200 and attempts < 5:
            batch = generate_german_kids_topics(250)  # Generate extra to account for duplicates
            for topic in batch:
                if topic.lower() not in all_existing:
                    new_unique_topics.append(topic)
                    all_existing.add(topic.lower())
                    if len(new_unique_topics) >= 200:
                        break
            attempts += 1
            if len(new_unique_topics) < 200:
                print(f"[topics] Versuch {attempts}: {len(new_unique_topics)} einzigartige Themen gefunden, generiere mehr...")
        
        print(f"[topics] ✅ {len(new_unique_topics)} EINZIGARTIGE neue Themen generiert (0 Duplikate)")
        
        # Add new topics to the end of existing ones
        topics.extend(new_unique_topics)
        try:
            with open(TOPICS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(topics) + "\n")
                f.flush()
                os.fsync(f.fileno())
            print(f"[topics] Jetzt {len(topics)} Themen verfügbar")
        except Exception as e:
            print(f"[topics] ❌ FEHLER beim Speichern neuer Themen: {e}")
    
    if not topics:
        print("[topics] ❌ Keine Themen verfügbar! Verwende Fallback.")
        return "Der kleine Bär im Wald"
    
    # Select the first topic and remove it from the list
    selected_topic = topics[0]
    remaining_topics = topics[1:]
    
    print(f"[topics] 🎯 Ausgewähltes Thema: '{selected_topic}'")
    print(f"[topics] 📊 Vor Entfernung: {len(topics)} Themen")
    print(f"[topics] 📊 Nach Entfernung: {len(remaining_topics)} Themen")
    
    # Save remaining topics back to file with atomic operation and verification
    max_retries = 3
    write_success = False
    
    for attempt in range(max_retries):
        try:
            # Write with flush and fsync for atomic operation
            with open(TOPICS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(remaining_topics) + "\n")
                f.flush()
                os.fsync(f.fileno())
            
            # Verify the write was successful by reading back
            with open(TOPICS_FILE, "r", encoding="utf-8") as f:
                verification = [line.strip() for line in f if line.strip()]
            
            # Check that the selected topic is NOT in the file anymore
            if selected_topic in verification:
                print(f"[topics] ⚠️  WARNUNG: Thema wurde nicht entfernt! Versuch {attempt + 1}/{max_retries}")
                time.sleep(0.5)  # Brief delay before retry
                continue
            
            # Check that we have the expected number of topics
            if len(verification) != len(remaining_topics):
                print(f"[topics] ⚠️  WARNUNG: Themenanzahl stimmt nicht überein! Erwartet: {len(remaining_topics)}, Gefunden: {len(verification)}")
                print(f"[topics] Versuch {attempt + 1}/{max_retries}")
                time.sleep(0.5)
                continue
            
            # Success!
            print(f"[topics] ✅ Thema erfolgreich entfernt und verifiziert")
            print(f"[topics] ✅ Verbleibende Themen: {len(verification)}")
            write_success = True
            break
            
        except Exception as e:
            print(f"[topics] ❌ FEHLER beim Speichern (Versuch {attempt + 1}/{max_retries}): {e}")
            time.sleep(0.5)
    
    if not write_success:
        print(f"[topics] ❌ KRITISCHER FEHLER: Konnte Thema nicht aus {TOPICS_FILE} entfernen!")
        print(f"[topics] ⚠️  Das gleiche Thema könnte beim nächsten Mal erneut ausgewählt werden!")
    
    # Log to used topics history with error handling
    try:
        today = datetime.datetime.now()
        with open("used_topics.txt", "a", encoding="utf-8") as f:
            f.write(f"{today.strftime('%Y-%m-%d')}: {selected_topic}\n")
            f.flush()
            os.fsync(f.fileno())
        print(f"[topics] ✅ Thema protokolliert in used_topics.txt")
    except Exception as e:
        print(f"[topics] ⚠️  WARNUNG: Konnte Thema nicht in used_topics.txt protokollieren: {e}")
    
    return selected_topic

def generate_story_with_pollinations(topic: str) -> str:
    """Generate a short children's story in the target language using Paid Pollinations API."""
    
    lang_name = LANGUAGE_CONFIG["name"]
    
    # Combine system and prompt into one clear instruction
    full_prompt = (
        f"Write a short children's story in {lang_name} language (ages 3-8) strictly about the topic: {topic}. "
        f"Do not change the animals or the subject. The story must be exactly about the title. "
        f"Length: 80-120 words. Simple language. Only the story content, no title."
    )
    
    print(f"[story] Geschichte generieren ({lang_name}): {topic}")
    
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai",
        "messages": [
            {"role": "system", "content": "You are a creative children's story author."},
            {"role": "user", "content": full_prompt}
        ]
    }
    
    # Retry mechanism for story generation
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code != 200:
                print(f"[story] API Error (Attempt {attempt+1}/{max_retries}): {r.status_code} - {r.text}")
                continue
                
            data = r.json()
            if "choices" in data and data["choices"]:
                text = data["choices"][0]["message"]["content"].strip()
            else:
                print(f"[story] Unexpected API response format: {data}")
                continue

            words = text.split()
            
            # VALIDATION: Ensure minimum story length to prevent short videos
            if len(words) < 50:
                print(f"[story] ⚠️ Geschichte zu kurz ({len(words)} Wörter), neuer Versuch {attempt + 1}/{max_retries}...")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    raise ValueError(f"Geschichte zu kurz nach {max_retries} Versuchen: {len(words)} Wörter")

            if len(words) > STORY_MAX_WORDS:
                text = " ".join(words[:STORY_MAX_WORDS])

            with open(STORY_FILE, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"[story] Geschichte generiert ({len(text.split())} Wörter)")
            return text
            
        except Exception as e:
            print(f"[story] Exception (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                 # Fallback story to ensure pipeline continuity
                fallback = f"Es war einmal {topic}. Es war ein schöner Tag. Die Tiere spielten zusammen im Wald. Sie waren sehr glücklich. Sie sangen und tanzten. Die Sonne schien am Himmel. Die Vögel flogen überall. Es war wunderbar. Alle Freunde hatten viel Spaß. Und sie lebten glücklich bis ans Ende ihrer Tage."
                print(f"[story] ⚠️ Verwende Fallback-Geschichte")
                with open(STORY_FILE, "w", encoding="utf-8") as f:
                    f.write(fallback)
                return fallback

def generate_visual_prompts(story: str) -> list:
    """Generate 8 distinct ENGLISH visual descriptions from the story using Paid Pollinations API."""
    print(f"[scenes] Visuelle Beschreibungen auf Englisch generieren...")
    
    lang_name = LANGUAGE_CONFIG["name"]
    
    prompt = (
        f"Read this {lang_name} story: '{story}'\n"
        f"Generate exactly {NUM_IMAGES} detailed, visual image descriptions in ENGLISH based on this story. "
        f"Describe the animals, expressions, and environment clearly. "
        f"Make them cute and suitable for a 3D Pixar-style animation. "
        f"Output ONLY the {NUM_IMAGES} descriptions, one per line. No numbering."
    )
    
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    # Retry mechanism for prompt generation
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if r.status_code != 200:
                 print(f"[scenes] API Error (Attempt {attempt+1}/{max_retries}): {r.status_code}")
                 continue
                 
            data = r.json()
            if "choices" in data:
                text = data["choices"][0]["message"]["content"].strip()
            else:
                 text = str(data)
            
            # Clean up lines
            lines = [line.strip().lstrip('0123456789.- ') for line in text.split('\n') if line.strip()]
            
            # Ensure we have exactly NUM_IMAGES
            if len(lines) < NUM_IMAGES:
                while len(lines) < NUM_IMAGES:
                    lines.append(lines[-1] + " close up view" if lines else "Cute animal scene")
            
            scenes = lines[:NUM_IMAGES]
            
            # Save scenes
            with open(SCENES_FILE, "w", encoding="utf-8") as f:
                for i, scene in enumerate(scenes):
                    f.write(f"{i+1}. {scene}\n")
            
            print(f"[scenes] {len(scenes)} visuelle Beschreibungen erstellt")
            return scenes
            
        except Exception as e:
            print(f"[scenes] Fehler bei der Generierung (Versuch {attempt+1}): {e}")
            time.sleep(2)

    raise Exception(f"Failed to generate visual prompts after {max_retries} attempts.")

def generate_image(scene: str, idx: int) -> Path:
    """Generate high-quality 3D animated animal image for each scene using Pollinations AI."""
    # Create unique seed for each image based on scene content + index
    seed = hash(scene + str(idx)) % 1000000
    
    # Improved prompt with full negative prompts from French version
    prompt = (
        f"Professional 3D Pixar Disney animation style, ultra high quality 8K render, {scene}, "
        f"perfect symmetrical faces, flawless facial features, anatomically correct proportions, "
        f"cute adorable animal characters with correct anatomy, "
        f"professional character design, crystal clear details, "
        f"vibrant colorful children's book illustration, cinematic lighting, "
        f"magical forest atmosphere, child-friendly, happy joyful expression, "
        f"masterpiece quality, sharp focus, beautiful composition, "
        f"NEGATIVE PROMPT: deformed, disfigured, ugly, bad anatomy, "
        f"extra limbs, missing limbs, floating limbs, disconnected limbs, "
        f"mutated hands, poorly drawn hands, malformed hands, "
        f"poorly drawn face, mutation, deformed face, asymmetric face, "
        f"blurry, bad proportions, extra fingers, fused fingers, "
        f"too many fingers, cloned face, duplicate features, "
        f"disfigured, gross proportions, malformed limbs, "
        f"extra arms, extra legs, missing arms, missing legs, "
        f"deformed eyes, cross-eyed, misaligned eyes, extra eyes, "
        f"deformed mouth, extra mouth, bad teeth, "
        f"low quality, worst quality, low resolution, distorted"
    )
    safe_prompt = quote(prompt)
    
    # URL construction matching French version
    url = (
        f"https://gen.pollinations.ai/image/{safe_prompt}"
        f"?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}&model={IMAGE_MODEL}&seed={seed}&nologo=true"
    )
    
    print(f"[image] 3D-Bild generieren {idx+1}/{NUM_IMAGES}: {scene[:50]}...")
    
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
    }

    out = IMAGES_DIR / f"scene_{idx:02d}.jpg"

    # Retry logic with exponential backoff
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Note: params are now in URL, so we don't pass them here
            r = requests.get(url, headers=headers, timeout=180)
            r.raise_for_status()
            out.write_bytes(r.content)
            time.sleep(2)  # Small delay between successful requests
            return out
        except requests.exceptions.HTTPError as e:
            # Handle 429 rate limits with much longer waits
            if e.response.status_code == 429:
                wait_time = (attempt + 1) * 20
                if attempt < max_retries - 1:
                    print(f"[image] Rate-Limit erreicht! Wiederholung {attempt+1}/{max_retries} (warte {wait_time}s)")
                    time.sleep(wait_time)
                else:
                    print(f"[image] Bild {idx+1} konnte nicht generiert werden: Rate-Limit überschritten")
                    raise e
            else:
                wait_time = (attempt + 1) * 5
                if attempt < max_retries - 1:
                    print(f"[image] HTTP {e.response.status_code}. Wiederholung {attempt+1}/{max_retries} (warte {wait_time}s)")
                    time.sleep(wait_time)
                else:
                    print(f"[image] Bild {idx+1} konnte nicht generiert werden: {e}")
                    raise e
        except Exception as e:
            wait_time = (attempt + 1) * 5
            if attempt < max_retries - 1:
                print(f"[image] Wiederholung {attempt+1}/{max_retries} (warte {wait_time}s)")
                time.sleep(wait_time)
            else:
                print(f"[image] Bild {idx+1} konnte nicht generiert werden: {e}")
                raise e
    return out

def generate_images(scenes: list):
    """Generate unique 3D animated images for each scene SEQUENTIALLY (avoids rate limits)"""
    print(f"[image] {NUM_IMAGES} 3D-Bilder sequenziell generieren (Rate-Limits vermeiden)...")
    return [generate_image(scene, i) for i, scene in enumerate(scenes)]

def generate_tts(story: str):
    """Generate narration using edge-tts (free Microsoft TTS)."""
    import asyncio
    try:
        import edge_tts
    except ImportError:
        subprocess.run(["pip", "install", "edge-tts"], check=True)
        import edge_tts
    
    lang_name = LANGUAGE_CONFIG["name"]
    voice = LANGUAGE_CONFIG["voice"]
    print(f"[tts] Sprachausgabe generieren ({lang_name}) mit edge-tts...")
    
    async def generate():
        communicate = edge_tts.Communicate(story, voice)
        await communicate.save(str(NARRATION_FILE))
    
    asyncio.run(generate())
    print(f"[tts] Sprachausgabe gespeichert in {NARRATION_FILE}")
    
    # VALIDATION: Check audio duration (inspired by French version)
    audio_duration = get_audio_duration(NARRATION_FILE)
    print(f"[validation] 🎵 Audio-Dauer: {audio_duration:.2f} Sekunden")
    
    if audio_duration < 10:
         raise ValueError(f"❌ Audio zu kurz ({audio_duration:.2f}s)! Minimum 10 Sekunden erforderlich.")
    
    print(f"[validation] ✅ Audio-Dauer gültig")

def generate_word_subtitles():
    """Generate WORD-BY-WORD subtitles using Vosk (lightweight!)."""
    print("[subs] Wort-für-Wort-Untertitel mit Vosk generieren...")
    
    import json
    import wave
    from vosk import Model, KaldiRecognizer
    import os
    
    # Download Vosk model if not exists
    model_name = LANGUAGE_CONFIG["vosk_model"]
    model_url = LANGUAGE_CONFIG["vosk_url"]
    zip_path = LANGUAGE_CONFIG["vosk_zip"]
    
    if not os.path.exists(model_name):
        print(f"[subs] Vosk-Modell wird heruntergeladen ({model_name})...")
        import urllib.request
        import zipfile
        
        urllib.request.urlretrieve(model_url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        os.remove(zip_path)
        print("[subs] Modell heruntergeladen!")
    
    # Convert MP3 to WAV for Vosk
    wav_file = "output/narration.wav"
    os.system(f'ffmpeg -y -i {NARRATION_FILE} -ar 16000 -ac 1 {wav_file}')
    
    # Load Vosk model
    model = Model(model_name)
    
    # Open WAV file
    wf = wave.open(wav_file, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)  # Enable word-level timestamps
    
    # Process audio
    words = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if 'result' in result:
                for word_info in result['result']:
                    words.append({
                        'word': word_info['word'].upper(),
                        'start': word_info['start'],
                        'end': word_info['end']
                    })
    
    # Final result
    final_result = json.loads(rec.FinalResult())
    if 'result' in final_result:
        for word_info in final_result['result']:
            words.append({
                'word': word_info['word'].upper(),
                'start': word_info['start'],
                'end': word_info['end']
            })
    
    font_name = LANGUAGE_CONFIG.get("subtitle_font", "Arial")
    
    # Create ASS subtitle file with kid-friendly styling
    ass_content = f"""[Script Info]
Title: Kindergeschichte
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},20,&H00FFFF00,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,5,10,10,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    for word in words:
        start = word['start']
        end = word['end']
        text = word['word']
        
        start_time = f"{int(start//3600)}:{int((start%3600)//60):02d}:{start%60:.2f}"
        end_time = f"{int(end//3600)}:{int((end%3600)//60):02d}:{end%60:.2f}"
        
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
    
    # Save ASS file
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        f.write(ass_content)
    
    print(f"[subs] Untertitel gespeichert ({len(words)} Wörter)")

def get_audio_duration(audio_file):
    """Get duration of audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def create_animated_slideshow(image_paths):
    """Create animated slideshow with Ken Burns zoom effect."""
    print("[video] Animierte Diashow mit Ken-Burns-Effekt erstellen...")
    
    # Get audio duration to match video length
    duration = get_audio_duration(NARRATION_FILE)
    per_image = duration / len(image_paths)
    
    # Create individual animated clips with zoom effect
    clips = []
    for i, img_path in enumerate(image_paths):
        clip_file = OUTPUT_DIR / f"clip_{i:02d}.mp4"
        clips.append(clip_file)
        
        # Calculate frames (30 fps)
        frames = max(int(per_image * 30), 60)
        
        # Alternate between zoom in and zoom out for variety
        if i % 2 == 0:
            # Zoom in effect
            zoom_start = 1.0
            zoom_end = 1.3
        else:
            # Zoom out effect  
            zoom_start = 1.3
            zoom_end = 1.0
        
        # Simple zoom with scale filter (more reliable on Windows)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", (
                f"scale=8000:-1,"
                f"zoompan=z='if(lte(on,1),{zoom_start},{zoom_start}+(({zoom_end}-{zoom_start})/{frames})*on)':"
                f"d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps=30"
            ),
            "-t", str(per_image),
            "-c:v", "libx264",
            "-preset", "slow",  # Better quality
            "-crf", "18",  # High quality (lower = better, 18-23 is good)
            "-pix_fmt", "yuv420p",
            str(clip_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[video] Zoom für Clip {i+1} fehlgeschlagen, verwende Fallback...")
            # Fallback: simple static with slight movement
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(img_path),
                "-vf", f"scale={IMAGE_WIDTH}:{IMAGE_HEIGHT}:force_original_aspect_ratio=increase,crop={IMAGE_WIDTH}:{IMAGE_HEIGHT},fps=30",
                "-t", str(per_image),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(clip_file)
            ]
            subprocess.run(cmd_fallback, check=True, capture_output=True)
        
        print(f"[video] Animierter Clip {i+1}/{len(image_paths)}")
    
    # Create concat list
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")
    
    # Concatenate all clips
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(ANIMATED_VIDEO)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Animierte Diashow gespeichert in {ANIMATED_VIDEO}")
    
    # Cleanup individual clips
    for clip in clips:
        if clip.exists():
            clip.unlink()

def add_subtitles():
    """Overlay ASS subtitles on video."""
    print("[video] GROSSBUCHSTABEN-Untertitel hinzufügen...")
    
    # Windows path needs special handling for FFmpeg filter
    subs_path = str(SUBS_FILE.resolve()).replace("\\", "/").replace(":", "\\:")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(ANIMATED_VIDEO),
        "-vf", f"ass='{subs_path}'",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(VIDEO_WITH_SUBS)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Video mit Untertiteln gespeichert in {VIDEO_WITH_SUBS}")

def merge_audio():
    """Merge video with narration and background music."""
    print("[merge] Audio mit Hintergrundmusik zusammenführen...")
    
    if MUSIC_FILE.exists():
        # Merge narration + background music (music at lower volume)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-i", str(MUSIC_FILE),
            "-filter_complex", "[2:a]volume=0.25[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    else:
        print("[merge] Keine music.mp3 gefunden, verwende nur Sprachausgabe")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-map", "0:v",
            "-map", "1:a",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    
    subprocess.run(cmd, check=True)
    print(f"[merge] Finales Video gespeichert in {FINAL_VIDEO}")

def main():
    ensure_dirs()
    
    # Diagnostic logging
    print("=" * 60)
    print("=== SYSTEM STATUS CHECK ===")
    print("=" * 60)
    
    # Check topics.txt status
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, "r", encoding="utf-8") as f:
                current_topics = [line.strip() for line in f if line.strip()]
            print(f"[status] 📚 Topics verfügbar: {len(current_topics)}")
            if current_topics:
                print(f"[status] 🔝 Nächstes Thema: '{current_topics[0]}'")
        except Exception as e:
            print(f"[status] ❌ Fehler beim Lesen von topics.txt: {e}")
    else:
        print(f"[status] ⚠️  topics.txt existiert nicht")
    
    # Check used_topics.txt status
    if os.path.exists("used_topics.txt"):
        try:
            with open("used_topics.txt", "r", encoding="utf-8") as f:
                used = f.readlines()
            print(f"[status] 📝 Verwendete Themen: {len(used)}")
            if used:
                print(f"[status] 🕒 Letztes verwendetes Thema: {used[-1].strip()}")
        except Exception as e:
            print(f"[status] ❌ Fehler beim Lesen von used_topics.txt: {e}")
    else:
        print(f"[status] ℹ️  used_topics.txt existiert noch nicht")
    
    # Check cleanup status
    image_count = len(list(IMAGES_DIR.glob("*.jpg")))
    output_count = len([f for f in OUTPUT_DIR.glob("*") if f.is_file() and f.name != ".gitkeep"])
    print(f"[status] 🖼️  Alte Bilder bereinigt: {image_count} verbleibend (sollte 0 sein)")
    print(f"[status] 📁 Alte Output-Dateien bereinigt: {output_count} verbleibend (sollte 0 sein)")
    
    print("=" * 60)
    print()

    try:
    
    # Check if topics.txt exists and try to read from it
        # Check if topics.txt exists and try to read from it
        if os.path.exists(TOPICS_FILE):
            try:
                with open(TOPICS_FILE, "r", encoding="utf-8") as f:
                    # Read lines and filter empty ones
                    lines = [line.strip() for line in f if line.strip()]
                    if not lines:
                        # File exists but is empty
                        print(f"[topics] ⚠️ {TOPICS_FILE} ist leer. Generiere neue Themen...")
                        from generate_topics import generate_german_kids_topics, save_topics_to_file
                        new_topics = generate_german_kids_topics(500)
                        save_topics_to_file(new_topics)
            except Exception as e:
                print(f"[topics] ❌ Fehler beim Lesen von {TOPICS_FILE}: {e}")
        else:
             # File doesn't exist
            print(f"[topics] ⚠️ {TOPICS_FILE} nicht gefunden! Generiere 500 initiale Themen...")
            from generate_topics import generate_german_kids_topics, save_topics_to_file
            new_topics = generate_german_kids_topics(500)
            save_topics_to_file(new_topics)

        topic = choose_topic_for_today()
        print("=" * 60)
        print(f"=== Topic: {topic}")
        print("=" * 60)

        # 1. Generate story with Pollinations AI
        story = generate_story_with_pollinations(topic)
        
        # 2. Generate detailed ENGLISH visual prompts from the story
        scenes = generate_visual_prompts(story)
        
        # 3. Generate unique images for each scene
        images = generate_images(scenes)

        # 4. Generate narration with TTS
        generate_tts(story)
        
        # 5. Generate word-level UPPERCASE subtitles with Whisper
        generate_word_subtitles()
        
        # 6. Create animated slideshow with Ken Burns effect
        create_animated_slideshow(images)
        
        # 7. Add subtitles overlay
        add_subtitles()
        
        # 8. Merge audio (narration + background music)
        merge_audio()

        print("=" * 60)
        print(f"✅ DONE. Video ready: {FINAL_VIDEO}")
        print("=" * 60)
        
    except Exception as e:
        print("\n\n" + "!"*60)
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("!"*60 + "\n")
        exit(1)

if __name__ == "__main__":
    main()

