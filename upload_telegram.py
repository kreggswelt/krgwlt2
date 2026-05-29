"""
Upload video to Telegram channel
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def upload_to_telegram(video_path, caption):
    """
    Upload video to Telegram channel
    """
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
    
    if not bot_token or not channel_id:
        print("Missing Telegram credentials. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID")
        return None
        
    # Clean token - if secret starts with 'bot', strip it because we add it in the URL
    if bot_token.lower().startswith('bot'):
        bot_token = bot_token[3:]
    
    # Telegram API endpoint
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    
    # Prepare the video file
    with open(video_path, 'rb') as video_file:
        files = {
            'video': video_file
        }
        
        data = {
            'chat_id': channel_id,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        
        print(f"Uploading to Telegram channel: {channel_id}")
        try:
            response = requests.post(url, files=files, data=data, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"✅ Successfully uploaded to Telegram!")
                    return result
                else:
                    error_desc = result.get('description')
                    print(f"❌ Telegram API Error: {error_desc}")
                    # If 404 and it's from API, maybe the channel_id is wrong or bot not in channel
                    return None
            elif response.status_code == 404:
                print(f"❌ Telegram Error 404: Not Found. Check your TELEGRAM_BOT_TOKEN.")
                print(f"DEBUG: URL used: https://api.telegram.org/bot{bot_token[:5]}...{bot_token[-5:]}/sendVideo")
                return None
            else:
                print(f"❌ Telegram HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Telegram connection error: {e}")
            return None

if __name__ == "__main__":
    # Test upload
    test_video = Path("output") / "final_video.mp4"
    if test_video.exists():
        try:
            result = upload_to_telegram(
                str(test_video),
                "Test video upload to Telegram"
            )
            print(f"Upload result: {result}")
        except Exception as e:
            print(f"Failed: {e}")
    else:
        print("No test video found")
