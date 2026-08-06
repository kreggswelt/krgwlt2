"""
Facebook Reels Upload (Resumable 3-Step Reels API v21.0)

Verified pattern from production repos:
  1. Start   -> /video_reels  upload_phase=start   -> returns video_id + upload_url
  2. Transfer-> POST upload_url with OAuth header + raw bytes
  3. Finish  -> /video_reels  upload_phase=finish video_state=PUBLISHED
Plus: masked credential logging, pinned-comment with sleep-based retry, and
no unnecessary polling/API calls.
"""

import os
import time
import requests
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GRAPH_API = "https://graph.facebook.com/v21.0"


def _mask(s):
    if s and len(s) > 8:
        return f"{s[:4]}...{s[-4:]}"
    if s == "***":
        return "PLACEHOLDER (***)"
    return "MISSING"


def _post_pinned_comment(video_id, description, access_token):
    """Post description as a pinned comment with sleep-based retry (no wasted calls)."""
    print("[facebook] Posting description as pinned comment...")

    max_retries = 5
    comment_id = None

    for attempt in range(max_retries):
        try:
            comment_url = f"{GRAPH_API}/{video_id}/comments"
            comment_data = {
                'access_token': access_token,
                'message': description[:500]
            }
            res_comment = requests.post(comment_url, data=comment_data, timeout=30)

            if res_comment.status_code == 200:
                resp = res_comment.json()
                comment_id = resp.get('id')
                if comment_id:
                    print(f"[facebook] ✅ Comment posted! ID: {comment_id}")
                    break
                print(f"[facebook] Comment response missing ID: {resp}")
            elif res_comment.status_code == 404 and attempt < max_retries - 1:
                wait = (attempt + 1) * 10
                print(f"[facebook] Video not ready for comments yet, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"[facebook] Comment post failed: {res_comment.status_code} - {res_comment.text[:200]}")
                break
        except Exception as e:
            print(f"[facebook] Comment post error: {e}")
            break

    if comment_id:
        try:
            pin_url = f"{GRAPH_API}/{comment_id}"
            pin_data = {
                'access_token': access_token,
                'is_pinned': 'true'
            }
            res_pin = requests.post(pin_url, data=pin_data, timeout=15)
            if res_pin.status_code == 200:
                print(f"[facebook] ✅ Comment pinned to top!")
            else:
                print(f"[facebook] Pin attempt: {res_pin.status_code} - {res_pin.text[:200]}")
        except Exception as e:
            print(f"[facebook] Pin attempt error: {e}")
    else:
        print("[facebook] Could not post comment (video may need processing time)")


def upload_to_facebook(video_path, description, title="Psychologie & Selbstverbesserung"):
    """
    Upload video to Facebook Page as a Reel using the RESUMABLE 3-step Reels API.
    Returns dict with upload status and details.
    """
    print("\n" + "=" * 60)
    print("📘 FACEBOOK UPLOAD STARTING (RESUMABLE 3-STEP)")
    print("=" * 60)

    # Get credentials
    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN') or os.getenv('META_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID') or os.getenv('FB_PAGE_ID')

    # Debug info (masked - never log full tokens)
    print(f"[facebook] Page ID: {page_id}")
    print(f"[facebook] Access Token: {_mask(access_token)}")

    if not access_token:
        print("[facebook] ⚠️  Skipping Facebook upload - FACEBOOK_ACCESS_TOKEN not set")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'facebook'}

    if not page_id:
        print("[facebook] ⚠️  Skipping Facebook upload - FACEBOOK_PAGE_ID not set")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'facebook'}

    print("[facebook] ✅ Credentials loaded")

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"[facebook] Video file not found: {video_path}")

    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[facebook] ✅ Video file found: {video_path}")
    print(f"[facebook] Video size: {file_size_mb:.2f} MB")

    try:
        file_size = video_path_obj.stat().st_size

        # Step 1: Start resumable session
        print("[facebook] Step 1: Initiating resumable upload session...")
        start_url = f"{GRAPH_API}/{page_id}/video_reels"
        start_data = {
            'access_token': access_token,
            'upload_phase': 'start',
            'file_size': file_size
        }
        res_start = requests.post(start_url, data=start_data, timeout=30)

        if res_start.status_code != 200:
            raise Exception(f"Start Phase Failed: {res_start.text[:300]}")

        start_json = res_start.json()
        video_id = start_json.get('video_id')
        upload_url = start_json.get('upload_url')

        if not video_id:
            raise Exception(f"No video_id returned. Response: {start_json}")

        # Step 2: Transfer over OAuth
        print("[facebook] Step 2: Transferring file to Facebook Servers...")
        headers = {
            'Authorization': f'OAuth {access_token}',
            'offset': '0',
            'file_size': str(file_size)
        }
        with open(video_path, 'rb') as f:
            res_transfer = requests.post(upload_url, headers=headers, data=f, timeout=600)

        if res_transfer.status_code != 200:
            raise Exception(f"Transfer Phase Failed: {res_transfer.text[:300]}")

        # Step 3: Finish
        print("[facebook] Step 3: Publishing Reel...")
        finish_url = f"{GRAPH_API}/{page_id}/video_reels"
        finish_data = {
            'access_token': access_token,
            'upload_phase': 'finish',
            'video_id': video_id,
            'description': description,
            'video_state': 'PUBLISHED'
        }
        res_finish = requests.post(finish_url, data=finish_data, timeout=60)

        if res_finish.status_code == 200 and res_finish.json().get('success'):
            print("[facebook] ✅ SUCCESS! Reel uploaded to Facebook!")
            print(f"[facebook] Video ID: {video_id}")

            # Post description as a pinned comment (sleep-based retry)
            _post_pinned_comment(video_id, description, access_token)

            print("[facebook] Check your Facebook Page Reels tab to see the post.")
            print("=" * 60)
            return {
                'id': video_id,
                'platform': 'facebook',
                'status': 'success',
                'url': f"https://facebook.com/{video_id}"
            }
        else:
            raise Exception(f"Finish Phase Failed: {res_finish.text[:300]}")

    except requests.exceptions.Timeout:
        raise Exception("⏱️ Upload timed out (video too large or slow connection)")

    except requests.exceptions.ConnectionError as e:
        raise Exception(f"🌐 Connection error: {str(e)[:200]}")

    except Exception as e:
        print(f"[facebook] ❌ UNEXPECTED ERROR: {e}")
        raise
