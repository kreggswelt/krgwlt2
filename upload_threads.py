"""
Threads Upload - Robust Version with Multiple Fallbacks
Uploads video to tmpfiles.org, file.io, or transfer.sh (fallback), then uses URL for Threads API.
Includes enhanced debugging for HTTP 500 errors.
"""

import os
import requests
import time
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def upload_to_tmpfiles(video_path_obj):
    """Upload to tmpfiles.org"""
    try:
        print(f"[threads] 📤 Uploading to tmpfiles.org...")
        with open(video_path_obj, 'rb') as video_file:
            files = {'file': ('video.mp4', video_file, 'video/mp4')}
            temp_response = requests.post(
                'https://tmpfiles.org/api/v1/upload',
                files=files,
                timeout=180
            )
        
        if temp_response.status_code != 200:
            print(f"[threads] ⚠️ tmpfiles.org upload failed: {temp_response.status_code}")
            return None
            
        temp_data = temp_response.json()
        if temp_data.get('status') != 'success':
            print(f"[threads] ⚠️ tmpfiles.org error: {temp_data}")
            return None
            
        temp_url = temp_data.get('data', {}).get('url', '')
        # DO NOT force https, match Instagram script behavior
        video_url = temp_url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')
        print(f"[threads] ✅ tmpfiles.org URL: {video_url}")
        return video_url
    except Exception as e:
        print(f"[threads] ⚠️ tmpfiles.org exception: {e}")
        return None

def upload_to_fileio(video_path_obj):
    """Upload to file.io"""
    try:
        print(f"[threads] 📤 Uploading to file.io...")
        with open(video_path_obj, 'rb') as f:
            files = {'file': f}
            # Set to 1 day expiry to avoid instant deletion issues
            response = requests.post('https://file.io/?expires=1d', files=files, timeout=120)
            
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    url = data.get('link')
                    print(f"[threads] ✅ file.io URL: {url}")
                    return url
                else:
                    print(f"[threads] ⚠️ file.io error: {data}")
            except:
                print(f"[threads] ⚠️ file.io returned non-JSON: {response.text[:100]}")
        else:
            print(f"[threads] ⚠️ file.io upload failed: {response.status_code}")
        return None
    except Exception as e:
        print(f"[threads] ⚠️ file.io exception: {e}")
        return None

def upload_to_transfersh(video_path_obj):
    """Upload to transfer.sh"""
    try:
        print(f"[threads] 📤 Uploading to transfer.sh...")
        filename = video_path_obj.name
        with open(video_path_obj, 'rb') as f:
            response = requests.put(f'https://transfer.sh/{filename}', data=f, timeout=300)
            
        if response.status_code == 200:
            url = response.text.strip()
            print(f"[threads] ✅ transfer.sh URL: {url}")
            return url
        else:
            print(f"[threads] ⚠️ transfer.sh upload failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"[threads] ⚠️ transfer.sh exception: {e}")
        return None

def create_threads_container(user_id, access_token, video_url, text):
    """Attempt to create a media container with extra debugging"""
    api_version = 'v1.0'
    container_url = f"https://graph.threads.net/{api_version}/{user_id}/threads"
    
    payload = {
        'media_type': 'VIDEO',
        'video_url': video_url,
        'text': text,
        'access_token': access_token
    }
    
    # Order matters: Threads sometimes prefers Params for video containers
    methods = [
        ('Params', lambda: requests.post(container_url, params=payload, timeout=60)),
        ('Data', lambda: requests.post(container_url, data=payload, timeout=60))
    ]
    
    last_error_data = None
    
    for name, call in methods:
        try:
            print(f"[threads] Calling API via {name}...")
            resp = call()
            if resp.status_code == 200:
                cid = resp.json().get('id')
                if cid: return cid, None
            
            error_data = resp.text
            try:
                error_data = resp.json()
            except:
                pass
            
            print(f"[threads] ⚠️ {name} failed. Status: {resp.status_code}, Body: {resp.text}")
            last_error_data = f"Status: {resp.status_code}, Body: {resp.text}"
        except Exception as e:
            last_error_data = str(e)
            
    return None, last_error_data

def upload_to_threads(video_path, text, publish=True, video_url=None):
    """Main upload function"""
    print("\n" + "=" * 60)
    print("🧵 THREADS UPLOAD STARTING")
    print("=" * 60)
    
    # Credentials
    access_token = os.getenv('THREADS_ACCESS_TOKEN')
    user_id = os.getenv('THREADS_USER_ID')
    
    if not access_token or not user_id:
        print(f"[threads] ❌ Missing credentials in .env")
        return None
    
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        print(f"[threads] ❌ Video not found: {video_path}")
        return None
    
    # Text limit 500
    text_limited = text[:500] if len(text) > 500 else text
    
    container_id = None
    last_api_error = "None"

    # Try provided URL first
    if video_url:
        print(f"[threads] 🔗 Using provided video URL: {video_url}")
        cid, error = create_threads_container(user_id, access_token, video_url, text_limited)
        if cid:
            container_id = cid
        else:
            print(f"[threads] ⚠️ Provided URL failed, falling back to new uploads... Error: {error}")
            last_api_error = error
    
    if not container_id:
        # Hosts to try in order
        hosts = [
            ("tmpfiles.org", upload_to_tmpfiles),
            ("file.io", upload_to_fileio),
            ("transfer.sh", upload_to_transfersh)
        ]
        
        for host_name, upload_func in hosts:
            v_url = upload_func(video_path_obj)
            if v_url:
                # 10s sleep for better propagation
                print(f"[threads] Sleeping 10s for propagation on {host_name}...")
                time.sleep(10)
                
                cid, error = create_threads_container(user_id, access_token, v_url, text_limited)
                if cid:
                    container_id = cid
                    break
                else:
                    last_api_error = error
                    print(f"[threads] 🔄 API rejection on {host_name}, trying next host...")
            else:
                print(f"[threads] 🔄 Host {host_name} upload failed.")

    if not container_id:
        print(f"[threads] ❌ ALL HOSTS FAILED. Last API Error: {last_api_error}")
        raise Exception(f"Threads container creation failed. Meta Response: {last_api_error}")
    
    # Waiting
    print(f"[threads] ⏳ Waiting for processing (max 5 mins)...")
    max_wait = 300
    waited = 0
    while waited < max_wait:
        status_url = f"https://graph.threads.net/v1.0/{container_id}"
        params = {'fields': 'status,error_message', 'access_token': access_token}
        try:
            r = requests.get(status_url, params=params, timeout=30).json()
            status = r.get('status', 'UNKNOWN')
            print(f"[threads] Status: {status} ({waited}s)")
            if status == 'FINISHED': break
            if status == 'ERROR':
                raise Exception(f"Threads Video Processing Error: {r.get('error_message')}")
        except Exception as e:
            print(f"[threads] ⚠️ Status check failed: {e}")
        time.sleep(20)
        waited += 20
        
    if waited >= max_wait:
        raise Exception("Threads video processing timeout")
        
    # Publish
    if publish:
        print(f"[threads] 📤 Publishing to Threads...")
        pub_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
        p_res = requests.post(pub_url, params={'creation_id': container_id, 'access_token': access_token}, timeout=60)
        if p_res.status_code == 200:
            tid = p_res.json().get('id')
            print(f"[threads] ✅ SUCCESS! Thread ID: {tid}")
            return {'id': tid, 'platform': 'threads', 'status': 'success'}
        else:
            print(f"[threads] ❌ Publish failed: {p_res.text}")
            raise Exception(f"Publish failed: {p_res.text}")
    else:
        print(f"[threads] ✅ Container created successfully: {container_id}")
        return {'id': container_id, 'platform': 'threads', 'status': 'container_created'}

if __name__ == '__main__':
    v = Path('output/final_video.mp4')
    if v.exists():
        try:
            upload_to_threads(str(v), "Automated upload test", publish=False)
        except Exception as e:
            print(f"FAILED: {e}")
    else:
        print("No video found")
