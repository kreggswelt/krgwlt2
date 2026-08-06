import os
import re
import sys
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

NUM_IMAGES = 8
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920
IMAGE_MODEL = "zimage"

STORY_MAX_WORDS = 300

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



TOPICS_FILE = "topics.txt"

def get_all_used_topics():
    """Get all previously used topics to prevent duplicates."""
    used = set()
    if os.path.exists("used_topics.txt"):
        with open("used_topics.txt", "r", encoding="utf-8") as f:
            for line in f:
                if ": " in line:
                    topic = line.split(": ", 1)[1].strip()
                    used.add(topic.lower())
                else:
                    used.add(line.strip().lower())
    return used

def choose_topic_for_today():
    """Select and consume a topic from topics.txt. Auto-generates new unique topics when running low."""
    if not os.path.exists(TOPICS_FILE):
        print(f"[topics] {TOPICS_FILE} not found! Generating initial topics...")
        from generate_topics import generate_german_psychology_topics, save_topics_to_file
        new_topics = generate_german_psychology_topics(100)
        save_topics_to_file(new_topics)

    try:
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            topics = [line.strip() for line in f if line.strip()]
        print(f"[topics] Loaded {len(topics)} topics")
    except Exception as e:
        print(f"[topics] ERROR reading {TOPICS_FILE}: {e}")
        return "Selbstvertrauen aufbauen"

    if len(topics) < 30:
        print(f"[topics] Only {len(topics)} topics left. Generating 100 new unique topics...")
        from generate_topics import generate_german_psychology_topics

        used_topics = get_all_used_topics()
        existing_topics_lower = set(t.lower() for t in topics)
        all_existing = used_topics.union(existing_topics_lower)

        print(f"[topics] Already used/existing: {len(all_existing)} topics")
        attempts = 0
        new_unique_topics = []
        while len(new_unique_topics) < 100 and attempts < 5:
            batch = generate_german_psychology_topics(150)
            for topic in batch:
                if topic.lower() not in all_existing:
                    new_unique_topics.append(topic)
                    all_existing.add(topic.lower())
                    if len(new_unique_topics) >= 100:
                        break
            attempts += 1

        print(f"[topics] Generated {len(new_unique_topics)} unique new topics (0 duplicates)")
        topics.extend(new_unique_topics)
        try:
            with open(TOPICS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(topics) + "\n")
                f.flush()
                os.fsync(f.fileno())
            print(f"[topics] Now {len(topics)} topics available")
        except Exception as e:
            print(f"[topics] ERROR saving new topics: {e}")

    if not topics:
        print("[topics] No topics available! Using fallback.")
        return "Selbstvertrauen aufbauen"

    selected_topic = topics[0]
    remaining_topics = topics[1:]

    print(f"[topics] Topic selected: {selected_topic}")
    print(f"[topics] Remaining: {len(remaining_topics)}")

    try:
        with open(TOPICS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(remaining_topics) + "\n")
            f.flush()
            os.fsync(f.fileno())
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            verification = [line.strip() for line in f if line.strip()]
        if selected_topic in verification:
            print(f"[topics] WARNING: Topic still in file after removal!")
        else:
            print(f"[topics] Topic successfully removed from topics.txt")
    except Exception as e:
        print(f"[topics] ERROR updating {TOPICS_FILE}: {e}")

    try:
        today = datetime.datetime.now()
        with open("used_topics.txt", "a", encoding="utf-8") as f:
            f.write(f"{today.strftime('%Y-%m-%d')}: {selected_topic}\n")
            f.flush()
        print(f"[topics] Topic logged to used_topics.txt")
    except Exception as e:
        print(f"[topics] WARNING: Could not log topic: {e}")

    return selected_topic

def generate_story_with_pollinations(topic: str) -> str:
    """Generate a self-help / psychological reflection in German for women 18+."""
    
    lang_name = LANGUAGE_CONFIG["name"]
    
    system_prompt = (
        "Du bist eine einfühlsame Psychologin und Life-Coach. "
        "Deine Worte sind warm, ermutigend und weise."
    )
    full_prompt = (
        f"Schreibe eine kurze, einfühlsame Selbsthilfe- und Positive-Psychologie-Reflexion auf {lang_name} "
        f"zum Thema: {topic}. "
        f"Wende dich direkt an die Leserin oder den Leser. "
        f"Sei warmherzig, psychologisch fundiert und motivierend. "
        f"Integriere Prinzipien aus positiver Psychologie, Achtsamkeit und Selbstmitgefühl. "
        f"Gib konkrete, alltagstaugliche Einsichten. "
        f"Länge: 80-120 Wörter. Kein Titel. Nur der Inhalt."
    )
    
    print(f"[story] Selbsthilfe-Text generieren ({lang_name}): {topic}")
    
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai",
        "temperature": 1.3,
        "messages": [
            {"role": "system", "content": system_prompt},
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
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                break
                
            data = r.json()
            if "choices" in data and data["choices"]:
                text = data["choices"][0]["message"]["content"].strip()
            else:
                print(f"[story] Unexpected API response format: {data}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                break

            words = text.split()
            
            if len(words) < 50:
                print(f"[story] ⚠️ Geschichte zu kurz ({len(words)} Wörter), neuer Versuch {attempt + 1}/{max_retries}...")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                break

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
                continue
            break
    
    # Fallback after all retries exhausted
    fallback = (
        f"Manchmal vergessen wir, wie stark wir wirklich sind. {topic} "
        f"Du darfst dir Zeit nehmen. Du darfst Nein sagen. "
        f"Deine Gefühle sind wichtig. Deine Bedürfnisse zählen. "
        f"Jeder Tag ist eine neue Chance, dir selbst näherzukommen. "
        f"Sei sanft mit dir. Wachse in deinem eigenen Tempo. "
        f"Du bist genug, genau so wie du bist."
    )
    print(f"[story] ⚠️ Verwende Fallback-Geschichte")
    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write(fallback)
    return fallback

FALLBACK_SCENES = [
    "stickman meditating with peaceful thoughts around head",
    "stickman looking in mirror seeing their best self",
    "stickman watering a small growing plant of confidence",
    "stickman letting go of a balloon representing fear",
    "stickman climbing a mountain step by step",
    "stickman embracing another stickman in friendship",
    "stickman writing goals on a whiteboard",
    "stickman standing tall with arms wide open",
    "stickman holding a glowing heart in their hands",
    "stickman walking through a door of new opportunities",
    "stickman sitting at a desk thinking creatively",
    "stickman planting seeds of kindness around them",
    "stickman reaching up to touch a star",
    "stickman holding hands in a circle of support",
    "stickman reading a book under a tree of wisdom",
    "stickman building blocks one on top of another",
    "stickman jumping with joy arms in the air",
    "stickman painting a colorful canvas of their future",
    "stickman balancing on one leg finding inner peace",
    "stickman opening a curtain to bright sunlight",
    "stickman feeding positive thoughts into their mind",
    "stickman letting go of heavy weights labeled stress",
    "stickman hugging themselves with self love",
    "stickman drawing a map of their life journey",
    "stickman standing at a crossroads choosing wisely",
    "stickman meditating under a glowing moon",
    "stickman planting a garden of good habits",
    "stickman climbing a ladder of personal growth",
    "stickman sharing food with someone in need",
    "stickman dancing freely with joy",
    "stickman holding a candle of hope in darkness",
    "stickman building a bridge between hearts",
    "stickman flying a kite of dreams",
    "stickman watering flowers of friendship",
    "stickman standing firm like a strong tree",
    "stickman opening a book of possibilities",
    "stickman blowing dandelion seeds of kindness",
    "stickman holding an umbrella of protection over others",
    "stickman skipping stones across a calm lake",
    "stickman weaving a tapestry of their experiences",
    "stickman standing at the start line of a race",
    "stickman folding paper cranes of wishes",
    "stickman lighting lamps of knowledge",
    "stickman catching stars in a jar of dreams",
    "stickman building a nest of comfort for themselves",
    "stickman playing a musical instrument of joy",
    "stickman doing yoga in a peaceful pose",
    "stickman writing a letter of gratitude",
    "stickman blowing bubbles of positive energy",
    "stickman stretching toward their highest potential",
    "stickman holding a compass of inner guidance",
    "stickman sitting by a warm fire of contentment",
    "stickman collecting moments of happiness in a basket",
    "stickman painting a rainbow after the rain",
    "stickman pushing a boulder of challenge uphill",
    "stickman sitting quietly watching a sunrise of hope",
    "stickman tying a knot of commitment to themselves",
    "stickman arranging puzzle pieces of their life",
    "stickman holding a mirror reflecting inner beauty",
    "stickman climbing a tree of knowledge",
    "stickman weaving a crown of self worth",
    "stickman holding a lantern of wisdom",
    "stickman building a tower of achievements",
    "stickman embracing their own shadow with acceptance",
    "stickman planting flags of victory on goals reached",
    "stickman arranging flowers of gratitude in a vase",
    "stickman sailing a boat of dreams on calm waters",
]

def generate_visual_prompts(story: str) -> list:
    """Generate beautiful scene descriptions for self-help content."""
    print(f"[scenes] Szenenbeschreibungen auf Englisch generieren...")
    
    lang_name = LANGUAGE_CONFIG["name"]
    
    prompt = (
        f"Read this {lang_name} self-help text: '{story}'\n"
        f"Generate exactly {NUM_IMAGES} UNIQUE stickman scene descriptions in ENGLISH "
        f"that visually explain the concepts from the text. "
        f"Each scene shows a CLEAN, WELL-DRAWN stick figure on a soft pastel background doing an action. "
        f"Be CREATIVE and make each scene DIFFERENT from any other. "
        f"Think of original metaphors and actions based on the text. "
        f"Vary the background colors, the stickman poses, and the symbolic elements. "
        f"IMPORTANT: No books, no letters, no signs, no labels, no screens, no writing in the scene. "
        f"No visible text, no words, no letters anywhere. "
        f"Output ONLY {NUM_IMAGES} descriptions, one per line. No numbering."
    )
    
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai",
        "temperature": 1.4,
        "seed": random.randint(1, 999999),
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    # Retry mechanism for prompt generation
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if r.status_code != 200:
                 print(f"[scenes] API Error (Attempt {attempt+1}/{max_retries}): {r.status_code}")
                 if attempt < max_retries - 1:
                     time.sleep(2)
                     continue
                 break
                  
            data = r.json()
            if "choices" in data:
                text = data["choices"][0]["message"]["content"].strip()
            else:
                 text = str(data)
            
            lines = [line.strip().lstrip('0123456789.- ') for line in text.split('\n') if line.strip()]
            
            if len(lines) >= NUM_IMAGES:
                scenes = lines[:NUM_IMAGES]
                with open(SCENES_FILE, "w", encoding="utf-8") as f:
                    for i, scene in enumerate(scenes):
                        f.write(f"{i+1}. {scene}\n")
                print(f"[scenes] {len(scenes)} Szenen via API erstellt")
                return scenes
            
            print(f"[scenes] Nur {len(lines)} von {NUM_IMAGES} erhalten, verwende Fallback")
            break
            
        except Exception as e:
            print(f"[scenes] Fehler (Versuch {attempt+1}): {e}")
            time.sleep(2)

    print(f"[scenes] Verwende Fallback-Szenen...")
    scenes = [
        "Stickman meditating with glowing peaceful thoughts above head, soft blue background",
        "Stickman looking in a mirror seeing their best self reflected, warm pink background",
        "Stickman climbing steps toward a shining star, sunset gradient background",
        "Stickman watering a small plant growing from the ground, soft green background",
        "Stickman releasing a balloon labeled fear into the sky, lavender background",
        "Stickman writing goals in a journal at a desk, cozy warm background",
        "Stickman walking through an open door into bright light, golden background",
        "Stickman standing tall with arms open wide, soft teal background",
    ]
    with open(SCENES_FILE, "w", encoding="utf-8") as f:
        for i, scene in enumerate(scenes):
            f.write(f"{i+1}. {scene}\n")
    print(f"[scenes] {len(scenes)} Fallback-Szenen gespeichert")
    return scenes

def download_image_from_drive(idx: int) -> Path:
    """Pick a random stickman image from Google Drive folder (weighted by least-used)."""
    import json
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    out = IMAGES_DIR / f"scene_{idx:02d}.jpg"

    service_key = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    folder_id = os.environ.get(
        "GOOGLE_DRIVE_FOLDER_ID",
        "1E9NZSg5Ef-bcRIwMVcrJ-KsrmG0R1Zgv",
    ).strip().strip('"').strip("'")
    if not service_key:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY environment variable required")
    if not folder_id:
        raise ValueError("GOOGLE_DRIVE_FOLDER_ID environment variable required")

    cred = service_account.Credentials.from_service_account_info(
        json.loads(service_key), scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=cred)

    all_files = []
    page_token = None
    while True:
        r = service.files().list(
            q=f"'{folder_id}' in parents and mimeType contains 'image/'",
            fields="files(id, name)", pageSize=200, pageToken=page_token
        ).execute()
        all_files.extend(r.get("files", []))
        page_token = r.get("nextPageToken")
        if not page_token:
            break

    if not all_files:
        raise RuntimeError(f"No image files found in Google Drive folder: {folder_id}")

    used_log = Path("used_images.json")
    usage = {}
    if used_log.exists():
        try:
            usage = json.loads(used_log.read_text())
        except Exception:
            usage = {}

    for f in all_files:
        if f["name"] not in usage:
            usage[f["name"]] = 0

    min_usage = min(usage.values())
    weights = [1.0 / (usage[f["name"]] - min_usage + 1) for f in all_files]
    chosen = random.choices(all_files, weights=weights, k=1)[0]
    usage[chosen["name"]] += 1
    used_log.write_text(json.dumps(usage, indent=2))

    print(f"[image] Lade Bild von Google Drive: {chosen['name']} ...", flush=True)
    request = service.files().get_media(fileId=chosen["id"])
    from googleapiclient.http import MediaIoBaseDownload
    import io
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    out.write_bytes(fh.read())
    print(f"  Gespeichert: {out.name} ({out.stat().st_size // 1024} KB)", flush=True)
    return out

def generate_image(scene: str, idx: int, topic: str = "") -> Path:
    """Bild zufällig aus Google Drive statt KI-Generierung auswählen."""
    return download_image_from_drive(idx)

def generate_images(scenes: list, topic: str = ""):
    """Bilder zufällig aus Google Drive für jede Szene herunterladen."""
    print(f"[image] {NUM_IMAGES} Bilder zufällig aus Google Drive herunterladen...")
    return [generate_image(scene, i, topic) for i, scene in enumerate(scenes)]

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
    
    # Create ASS subtitle file - white bold text with thick black outline for visibility on any background
    ass_content = f"""[Script Info]
Title: Selbsthilfe
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},13,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,0,2,10,10,80,1

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
    print("=== SELBSTHILFE VIDEO GENERATOR ===")
    print("=" * 60)
    
    image_count = len(list(IMAGES_DIR.glob("*.jpg")))
    output_count = len([f for f in OUTPUT_DIR.glob("*") if f.is_file() and f.name != ".gitkeep"])
    print(f"[status] 🖼️  Alte Bilder bereinigt: {image_count} verbleibend (sollte 0 sein)")
    print(f"[status] 📁 Alte Output-Dateien bereinigt: {output_count} verbleibend (sollte 0 sein)")
    
    print("=" * 60)
    print()

    try:
    
        topic = choose_topic_for_today()
        print(f"[topics] Topic: '{topic}'")
        print("=" * 60)
        print(f"=== Topic: {topic}")
        print("=" * 60)


        # 1. Generate story with Pollinations AI
        story = generate_story_with_pollinations(topic)
        
        # 2. Generate detailed ENGLISH visual prompts from the story
        scenes = generate_visual_prompts(story)
        
        # 3. Generate unique images for each scene
        images = generate_images(scenes, topic)

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

