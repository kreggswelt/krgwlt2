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



def generate_topic() -> str:
    """Generate a random self-help topic using AI."""
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "openai",
        "messages": [
            {"role": "system", "content": "Du gibst NUR das Thema aus, nichts sonst."},
            {"role": "user", "content": "Generiere ein kurzes, einprägsames Thema aus Selbsthilfe und Positiver Psychologie auf Deutsch. Für alle geeignet. Zum Beispiel: 'Selbstliebe im Alltag' oder 'Die Kraft der kleinen Schritte'. NUR das Thema, keine Erklärung, kein Zusatztext."}
        ]
    }
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                topic = r.json()["choices"][0]["message"]["content"].strip().strip('"').strip("'")
                if topic:
                    return topic
        except Exception as e:
            print(f"[topic] Fehler: {e}")
            time.sleep(2)
    return "Selbstvertrauen aufbauen"

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
        f"Generate exactly {NUM_IMAGES} stickman scene descriptions in ENGLISH "
        f"that visually explain the concepts from the text. "
        f"Each scene shows a CLEAN, WELL-DRAWN stick figure on a soft pastel background doing an action. "
        f"Make the descriptions vivid and specific about the pose and action. "
        f"Variety of poses: meditating, climbing, watering a plant, embracing, writing in a journal, "
        f"releasing a balloon, standing tall, walking through a door. "
        f"Example: 'Stickman meditating peacefully with glowing thoughts above head, soft blue background' "
        f"or 'Stickman climbing steps toward a shining star, warm sunset colors behind' "
        f"Output ONLY {NUM_IMAGES} descriptions, one per line. No numbering."
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

def generate_image(scene: str, idx: int) -> Path:
    """Generate stickman image using Pollinations.ai with paid API key."""
    seed = hash(scene + str(idx)) % 1000000
    
    prompt = (
        f"Aesthetic clean stick figure illustration, minimalist vector art style, "
        f"well-proportioned stickman on soft gradient pastel background, {scene}, "
        f"polished flat design, smooth thin black lines, beautiful minimalist artwork, "
        f"elegant simple composition, soft calming pastel colors, professional quality"
    )
    safe_prompt = quote(prompt)
    
    negative = quote(
        "deformed, disfigured, ugly, bad anatomy, extra limbs, "
        "blurry, bad proportions, low quality, low resolution, "
        "photorealistic, 3d render, photograph, hyperrealistic, "
        "cluttered, messy, chaotic, complex background, graffiti, "
        "scribble, hand-drawn, sketchy, rough, stick figure, "
        "crude, childish, amateur, pixelated"
    )
    
    url = (
        f"https://gen.pollinations.ai/image/{safe_prompt}"
        f"?model={IMAGE_MODEL}&seed={seed}&nologo=true"
        f"&width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}"
        f"&negative_prompt={negative}"
    )
    
    headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"}
    out = IMAGES_DIR / f"scene_{idx:02d}.jpg"
    
    print(f"[image] Bild {idx+1}/{NUM_IMAGES} generieren (API): {scene[:45]}...")
    
    for attempt in range(5):
        try:
            r = requests.get(url, headers=headers, timeout=180)
            if r.status_code == 402:
                print(f"[image] 402 - warte 30s und wiederhole...")
                time.sleep(30)
                continue
            r.raise_for_status()
            if len(r.content) < 1000:
                raise ValueError("Image too small")
            out.write_bytes(r.content)
            print(f"[image] ✅ Bild {idx+1}: {len(r.content)//1024}KB")
            time.sleep(3)
            return out
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 402:
                print(f"[image] 402 - warte 30s und wiederhole...")
                time.sleep(30)
                continue
            if attempt < 4:
                time.sleep((attempt + 1) * 10)
        except Exception as e:
            if attempt < 4:
                time.sleep((attempt + 1) * 10)
            else:
                break
    
    raise Exception(f"Bild {idx+1} konnte nicht generiert werden (API Error)")

def generate_images(scenes: list):
    """Generate stickman images using Pollinations.ai API."""
    print(f"[image] {NUM_IMAGES} Stickman-Bilder via Pollinations API...")
    images = []
    for i, scene in enumerate(scenes):
        try:
            img = generate_image(scene, i)
            images.append(img)
        except Exception as e:
            print(f"[image] ⚠️ Bild {i+1} fehlgeschlagen: {e}")
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
            placeholder = IMAGES_DIR / f"scene_{i:02d}.jpg"
            img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            palettes = [(210, 230, 255), (255, 220, 230), (220, 255, 220), (255, 230, 200), (230, 220, 255), (255, 240, 210), (210, 240, 240), (240, 220, 240)]
            r1, g1, b1 = palettes[i % 8]
            r2 = min(r1 + 60, 255); g2 = min(g1 + 50, 255); b2 = min(b1 + 40, 255)
            for y in range(IMAGE_HEIGHT):
                t = y / IMAGE_HEIGHT
                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)
                draw.line([(0, y), (IMAGE_WIDTH, y)], fill=(r, g, b))
            img = img.filter(ImageFilter.GaussianBlur(radius=5))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except Exception:
                font = ImageFont.load_default()
            draw.text((IMAGE_WIDTH//2 - 250, IMAGE_HEIGHT//2 - 30), f"Scene {i+1}", fill=(80, 60, 120), font=font)
            img.save(str(placeholder), 'JPEG', quality=90)
            images.append(placeholder)
            print(f"[image] Platzhalter {i+1} erstellt")
    if not images:
        raise Exception("Keine Bilder konnten generiert werden!")
    return images

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
    
        topic = generate_topic()
        print(f"[topics] 🎯 Selbsthilfe-Thema: '{topic}'")
        print("=" * 60)
        print(f"=== Topic: {topic}")
        print("=" * 60)
        
        # Log topic to used_topics.txt so the monitoring system sees rotation
        try:
            today = datetime.datetime.now()
            with open("used_topics.txt", "a", encoding="utf-8") as f:
                f.write(f"{today.strftime('%Y-%m-%d')}: {topic}\n")
                f.flush()
            print(f"[topics] ✅ Thema protokolliert in used_topics.txt")
        except Exception as e:
            print(f"[topics] ⚠️ Konnte Thema nicht protokollieren: {e}")

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

