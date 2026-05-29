"""
Twitter/X Upload Script

Uploads videos to Twitter/X using Twitter API (Free Tier Compatible!)

Requirements:
- Twitter Developer Account (FREE tier works!)
- TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET

Free Tier Limits:
- 500-1,500 posts per month
- Video size: max 512 MB
- Video duration: max 140 seconds (2m 20s)
- Format: MP4 (H.264 + AAC audio)
"""

import os
from pathlib import Path
import tweepy
import time
from dotenv import load_dotenv

load_dotenv()

def upload_to_twitter(video_path, caption):
    """Upload video to Twitter/X using API v1.1 (media) + v2 (post)."""
    
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_secret = os.getenv('TWITTER_ACCESS_SECRET')
    
    if not all([api_key, api_secret, access_token, access_secret]):
        print("[twitter] ❌ Missing Twitter credentials")
        return None
    
    print("[twitter] 🐦 Uploading to Twitter/X...")
    
    # Check video file exists and size
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"[twitter] ❌ Video file not found: {video_path}")
    
    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[twitter] Video size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 512:
        raise ValueError(f"[twitter] ❌ Video too large ({file_size_mb:.2f} MB). Max: 512 MB")
    
    try:
        # Authenticate with Twitter API v1.1 for media upload
        print("[twitter] Authenticating with API v1.1 (media upload)...")
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret,
            access_token, access_secret
        )
        api_v1 = tweepy.API(auth)
        
        # Authenticate with Twitter API v2 for posting
        print("[twitter] Authenticating with API v2 (posting)...")
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        # Upload video (uses v1.1 API - works with FREE tier!)
        print("[twitter] Uploading video (this may take a minute)...")
        media = api_v1.media_upload(
            filename=str(video_path),
            media_category='tweet_video',
            chunked=True  # Use chunked upload for reliability
        )
        
        print(f"[twitter] ✅ Video uploaded! Media ID: {media.media_id}")
        
        # Wait for video processing (X needs time to process video)
        print("[twitter] Waiting for video processing...")
        time.sleep(5)  # Give X time to process the video
        
        # Create tweet with video (uses v2 API)
        print("[twitter] Posting tweet...")
        
        # Twitter has 280 character limit
        tweet_text = caption[:280] if len(caption) > 280 else caption
        
        response = client.create_tweet(
            text=tweet_text,
            media_ids=[media.media_id]
        )
        
        tweet_id = response.data['id']
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
        
        print(f"[twitter] ✅ Posted to Twitter!")
        print(f"[twitter] Tweet ID: {tweet_id}")
        print(f"[twitter] URL: {tweet_url}")
        
        return {
            'id': tweet_id,
            'url': tweet_url,
            'platform': 'twitter'
        }
        
    except tweepy.errors.Unauthorized as e:
        print(f"[twitter] ❌ Authentication failed!")
        print(f"[twitter] Error: {e}")
        raise
        
    except tweepy.errors.Forbidden as e:
        print(f"[twitter] ❌ Permission denied!")
        print(f"[twitter] Error: {e}")
        raise
        
    except tweepy.errors.TooManyRequests as e:
        print(f"[twitter] ❌ Rate limit exceeded!")
        print(f"[twitter] Error: {e}")
        raise
        
    except Exception as e:
        print(f"[twitter] ❌ Unexpected error: {e}")
        raise

def main():
    """Test upload to Twitter."""
    import sys
    video_file = Path('output/final_video.mp4')
    
    if not video_file.exists():
        print("[twitter] ❌ No video found at output/final_video.mp4")
        return
        
    caption = sys.argv[2] if len(sys.argv) > 2 else "Test video #TwitterAPI"
    
    try:
        upload_to_twitter(str(video_file), caption)
    except Exception as e:
        print(f"[twitter] ❌ Upload failed: {e}")

if __name__ == '__main__':
    main()
