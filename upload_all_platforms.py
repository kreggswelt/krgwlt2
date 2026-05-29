"""
Multi-Platform Upload Script

Uploads videos to:
- YouTube Shorts
- Instagram Reels
- TikTok
- Facebook Reels
- Threads
- Twitter
- VK
- Telegram

Each platform requires its own API credentials.
"""

import os
from pathlib import Path
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import platform-specific uploaders
from upload_to_youtube import upload_to_youtube
from upload_instagram import upload_to_instagram
from upload_tiktok import upload_to_tiktok
from upload_facebook import upload_to_facebook
from upload_threads import upload_to_threads
from upload_twitter import upload_to_twitter
from upload_vk import upload_to_vk
from upload_telegram import upload_to_telegram

def main():
    """Upload video to all configured platforms."""
    video_file = Path('output/final_video.mp4')
    
    if not video_file.exists():
        print("[upload] ❌ No video found at output/final_video.mp4")
        return
    
    # Read topic from used_topics.txt (unique each run)
    title = "Kindergeschichte"
    if os.path.exists("used_topics.txt"):
        with open("used_topics.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            if lines:
                last_line = lines[-1]
                # Remove date prefix if present (format: "YYYY-MM-DD: Topic")
                if ": " in last_line:
                    title = last_line.split(": ", 1)[1]
                else:
                    title = last_line
    
    # Read story text for description (unique each run)
    story_text = ""
    story_file = Path('output/story.txt')
    if story_file.exists():
        story_text = story_file.read_text(encoding='utf-8')
    
    description = f"""{title}

{story_text}

#Kindergeschichten #Märchen #Deutsch #FürKinder #Shorts #Geschichten #Lernen"""

    
    tags = [
        'Kindergeschichten', 'Märchen', 'Deutsch', 'Für Kinder',
        'Shorts', 'Animation', 'Lernen', 'Bildung'
    ]
    
    results = {}
    
    # Debug: Show which credentials are detected
    print("\n" + "="*60)
    print("🔍 CREDENTIAL DETECTION STATUS")
    print("="*60)
    print(f"YouTube: {'✅' if all([os.getenv('YT_CLIENT_ID'), os.getenv('YT_CLIENT_SECRET'), os.getenv('YT_REFRESH_TOKEN')]) else '❌'}")
    print(f"Instagram: {'✅' if (all([os.getenv('INSTAGRAM_ACCESS_TOKEN'), os.getenv('INSTAGRAM_ACCOUNT_ID')]) or all([os.getenv('INSTAGRAM_ACCESS_TOKEN'), os.getenv('IG_USER_ID')])) else '❌'}")
    print(f"Facebook: {'✅' if all([os.getenv('FACEBOOK_ACCESS_TOKEN'), os.getenv('FACEBOOK_PAGE_ID')]) else '❌'}")
    print(f"VK: {'✅' if (os.getenv('VK_ACCESS_TOKEN') and os.getenv('VK_GROUP_ID')) else '❌'}")
    print(f"Threads: {'✅' if all([os.getenv('THREADS_ACCESS_TOKEN'), os.getenv('THREADS_USER_ID')]) else '❌'}")
    print(f"Twitter: {'✅' if all([os.getenv('TWITTER_API_KEY'), os.getenv('TWITTER_API_SECRET'), os.getenv('TWITTER_ACCESS_TOKEN')]) else '❌'}")
    print(f"Telegram: {'✅' if (os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHANNEL_ID')) else '❌'}")
    print("="*60)
    
    # --- YouTube ---
    if all([
        os.getenv('YT_CLIENT_ID'),
        os.getenv('YT_CLIENT_SECRET'),
        os.getenv('YT_REFRESH_TOKEN')
    ]):
        print("\n" + "="*60)
        print("📺 Uploading to YouTube...")
        print("="*60)
        try:
            # YouTube takes title, description, tags, category_id
            result = upload_to_youtube(video_file, title, description, tags)
            results['youtube'] = result
            if result:
                 print(f"✅ YouTube: https://youtube.com/shorts/{result['id']}")
        except Exception as e:
            print(f"❌ YouTube failed: {e}")
            results['youtube'] = None
    else:
        print("⏭️  Skipping YouTube (credentials not set)")
    
    shared_video_url = None
    
    # --- Instagram ---
    if all([os.getenv('INSTAGRAM_ACCESS_TOKEN'), os.getenv('INSTAGRAM_ACCOUNT_ID')]) or \
       all([os.getenv('INSTAGRAM_ACCESS_TOKEN'), os.getenv('IG_USER_ID')]):
        print("\n" + "="*60)
        print("📸 Uploading to Instagram...")
        print("="*60)
        try:
            result = upload_to_instagram(str(video_file), description)
            results['instagram'] = result
            if result:
                print(f"✅ Instagram: Uploaded successfully")
                if result.get('video_url'):
                    shared_video_url = result.get('video_url')
        except Exception as e:
            print(f"❌ Instagram failed: {e}")
            results['instagram'] = None
    else:
        print("⏭️  Skipping Instagram (credentials not set)")
    
    # --- TikTok ---
    if os.getenv('TIKTOK_ACCESS_TOKEN'):
        print("\n" + "="*60)
        print("🎵 Uploading to TikTok...")
        print("="*60)
        try:
            result = upload_to_tiktok(str(video_file), title, description)
            results['tiktok'] = result
            if result:
                print(f"✅ TikTok: Uploaded successfully")
        except Exception as e:
            print(f"❌ TikTok failed: {e}")
            results['tiktok'] = None
    else:
        print("⏭️  Skipping TikTok (credentials not set)")
    
    # --- Facebook ---
    if all([os.getenv('FACEBOOK_ACCESS_TOKEN'), os.getenv('FACEBOOK_PAGE_ID')]):
        print("\n" + "="*60)
        print("📘 Uploading to Facebook...")
        print("="*60)
        try:
            result = upload_to_facebook(str(video_file), description)
            results['facebook'] = result
            if result:
                print(f"✅ Facebook: Uploaded successfully")
        except Exception as e:
            print(f"❌ Facebook failed: {e}")
            results['facebook'] = None
    else:
        print("⏭️  Skipping Facebook (credentials not set)")
    
    # --- Threads ---
    if all([os.getenv('THREADS_ACCESS_TOKEN'), os.getenv('THREADS_USER_ID')]):
        print("\n" + "="*60)
        print("🧵 Uploading to Threads...")
        print("="*60)
        try:
            result = upload_to_threads(str(video_file), description, video_url=shared_video_url)
            results['threads'] = result
            if result:
                print(f"✅ Threads: Uploaded successfully")
        except Exception as e:
            print(f"❌ Threads failed: {e}")
            results['threads'] = None
    else:
        print("⏭️  Skipping Threads (credentials not set)")
    
    # --- Twitter/X ---
    if all([
        os.getenv('TWITTER_API_KEY'),
        os.getenv('TWITTER_API_SECRET'),
        os.getenv('TWITTER_ACCESS_TOKEN')
    ]):
        print("\n" + "="*60)
        print("🐦 Uploading to Twitter/X...")
        print("="*60)
        try:
            result = upload_to_twitter(str(video_file), description)
            results['twitter'] = result
            if result:
                print(f"✅ Twitter: Uploaded successfully")
        except Exception as e:
            print(f"❌ Twitter failed: {e}")
            results['twitter'] = None
    else:
        print("⏭️  Skipping Twitter (credentials not set)")
        
    # --- VK ---
    if os.getenv('VK_ACCESS_TOKEN') and os.getenv('VK_GROUP_ID'):
        print("\n" + "="*60)
        print("🇷🇺 Uploading to VK...")
        print("="*60)
        try:
            result = upload_to_vk(str(video_file), description, title)
            results['vk'] = result
            if result:
                print(f"✅ VK: Uploaded successfully")
        except Exception as e:
            print(f"❌ VK failed: {e}")
            results['vk'] = None
    else:
        print("⏭️  Skipping VK (credentials not set)")

    # --- Telegram ---
    if os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHANNEL_ID'):
        print("\n" + "="*60)
        print("✈️ Uploading to Telegram...")
        print("="*60)
        try:
            result = upload_to_telegram(str(video_file), description)
            results['telegram'] = result
            if result:
                print(f"✅ Telegram: Uploaded successfully")
        except Exception as e:
            print(f"❌ Telegram failed: {e}")
            results['telegram'] = None
    else:
        print("⏭️  Skipping Telegram (credentials not set)")
    
    # Summary
    print("\n" + "="*60)
    print("📊 Upload Summary")
    print("="*60)
    for platform, result in results.items():
        status = "✅ Success" if result else "❌ Failed"
        print(f"{platform.capitalize()}: {status}")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n[upload] ❌ Upload pipeline error: {e}")
        print("[upload] Continuing gracefully...")
