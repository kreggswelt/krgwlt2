"""
Upload videos to VK (VKontakte) using vk_api library
This method is MUCH easier and handles OAuth automatically!
"""
import os
import vk_api
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upload_to_vk(video_path, description="", title=""):
    """
    Upload video to VK community using vk_api library
    
    This is the EASY way - vk_api handles all the complex OAuth stuff!
    
    Args:
        video_path: Path to video file
        description: Video description/caption
        title: Video title
        
    Returns:
        dict: Upload result with video_id and post_id
    """
    # Get credentials from environment
    access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    
    if not access_token:
        # Check standard logging or raise error, keeping it simple as per inspiration
        print("VK_ACCESS_TOKEN not found in environment variables")
        return None
    if not group_id:
        print("VK_GROUP_ID not found in environment variables")
        return None
    
    # Ensure group_id is positive for vk_api (it handles the negative conversion)
    group_id_clean = str(group_id).lstrip('-')
    group_id_int = int(group_id_clean)
    
    print(f"🇷🇺 Starting VK upload using vk_api...")
    print(f"📁 Video: {video_path}")
    print(f"👥 Group ID: {group_id}")
    
    try:
        # Initialize VK session
        print("\n🔑 Initializing VK session...")
        
        # Use app_id if available for potentially better permissions context
        app_id = os.getenv('VK_APP_ID')
        if app_id:
            print(f"   Using App ID: {app_id}")
            vk_session = vk_api.VkApi(token=access_token, app_id=app_id)
        else:
            vk_session = vk_api.VkApi(token=access_token)
            
        vk = vk_session.get_api()
        upload = vk_api.VkUpload(vk_session)
        
        # Prepare message
        message = description if description else "✨ Eine neue Kindergeschichte!\n\n#Kindergeschichten #Märchen #Deutsch"
        
        # Ensure message is not empty (VK requirement)
        if not message.strip():
            message = "💭 New video!"
        
        # Upload video
        print("\n📤 Uploading video to VK Community...")
        print("⏳ This may take a few minutes depending on video size...")

        # Strict Group Upload (No fallback to user profile)
        try:
            video = upload.video(
                video_file=str(video_path),
                name=title or 'Kindergeschichten für Kinder',
                description=description[:220] if description else '',
                group_id=group_id_int, 
                wallpost=0
            )
        except vk_api.exceptions.ApiError as e:
            print(f"\n❌ VK API Error during upload: {e}")
            if "Access denied" in str(e) or "owner has not right" in str(e):
                 print("⛔ PERMISSION DENIED: The token does not have rights to upload to this Group.")
                 print("   Please verify your Access Token has 'groups', 'video', and 'wall' scopes.")
                 print("   Also verify you are an Admin/Editor of the group in the API's eyes.")
            raise e
        
        print(f"✅ Video uploaded successfully to Group!")
        print(f"📹 Video ID: {video['video_id']}")
        print(f"👤 Owner ID: {video['owner_id']}")
        
        # Post video to community wall
        print("\n📝 Posting to community wall...")
        
        attachment = f"video{video['owner_id']}_{video['video_id']}"
        
        post_result = vk.wall.post(
            owner_id=-group_id_int,  # Negative for community
            from_group=1,  # Post on behalf of community
            message=message,
            attachments=attachment
        )
        
        post_id = post_result['post_id']
        post_url = f"https://vk.com/wall-{group_id_int}_{post_id}"
        
        print(f"✅ Posted to wall successfully!")
        print(f"📌 Post ID: {post_id}")
        print(f"🔗 View post: {post_url}")
        
        result = {
            'success': True,
            'video_id': video['video_id'],
            'owner_id': video['owner_id'],
            'post_id': post_id,
            'post_url': post_url,
            'message': 'Video uploaded and posted to VK Community successfully'
        }
        
        print(f"\n🎉 VK Upload Complete!")
        
        return result
        
    except vk_api.exceptions.ApiError as e:
        error_msg = f"VK API Error: {e}"
        print(f"\n❌ {error_msg}")
        
        # Provide helpful error messages
        if "Access denied" in str(e):
            print("\n💡 Solution:")
            print("   Your token doesn't have the required permissions.")
            print("   You need a USER token with 'video', 'wall', and 'groups' permissions.")
        
        raise Exception(error_msg)
        
    except FileNotFoundError:
        raise Exception(f"Video file not found: {video_path}")
        
    except Exception as e:
        raise Exception(f"Failed to upload to VK: {e}")


def main():
    """Test VK upload"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python upload_vk.py <video_path> [description] [title]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else "Eine neue Kindergeschichte! ✨"
    title = sys.argv[3] if len(sys.argv) > 3 else "Kindergeschichte für Kinder"
    
    try:
        result = upload_to_vk(video_path, description, title)
        print("\n✅ Success!")
        print(f"Post URL: {result['post_url']}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
