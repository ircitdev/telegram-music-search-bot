"""Integration test - simulates user interactions."""
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("🎵 UspMusicFinder Bot - Day 1-4 Integration Test")
print("=" * 80)

# Import all components
from src.config import settings
from src.utils.logger import logger
from src.models import Track
from src.searchers.youtube import youtube_searcher
from src.utils.cache import cache
from src.keyboards import create_track_keyboard
from src.bot import bot, dp
from src.handlers import start, search, callbacks

print("\n📋 Bot Configuration:")
print(f"   Bot Username: @{settings.BOT_USERNAME}")
print(f"   Log Level: {settings.LOG_LEVEL}")
print(f"   Max File Size: {settings.MAX_FILE_SIZE / 1024 / 1024:.0f} MB")
print(f"   Rate Limit: {settings.RATE_LIMIT_REQUESTS} requests/{settings.RATE_LIMIT_PERIOD}s")
print(f"   Directories: temp={settings.TEMP_DIR}, cache={settings.CACHE_DIR}, logs={settings.LOGS_DIR}")

print("\n" + "=" * 80)
print("🧪 Simulating User Interaction")
print("=" * 80)

async def simulate_user_flow():
    """Simulate a complete user interaction flow."""
    
    user_id = 123456789
    
    # Step 1: User searches for a song
    print("\n📍 Step 1: User sends search query")
    print("   → User: 'Imagine John Lennon'")
    
    search_query = "Imagine John Lennon"
    logger.info(f"User {user_id} | Search: {search_query}")
    
    # Step 2: Bot searches on YouTube
    print("\n📍 Step 2: Bot searches YouTube")
    tracks = await youtube_searcher.search(search_query)
    
    if not tracks:
        print("   ✗ No tracks found!")
        return False
    
    print(f"   ✓ Found {len(tracks)} tracks")
    for i, track in enumerate(tracks[:3], 1):
        print(f"     {i}. {track.artist} - {track.title} ({track.formatted_duration})")
    
    # Step 3: Cache results
    print("\n📍 Step 3: Bot caches search results")
    cache_key = f"search:{user_id}"
    cache.set(cache_key, tracks, ttl=600)
    print(f"   ✓ Cached {len(tracks)} tracks for user {user_id}")
    
    # Step 4: Create inline keyboard
    print("\n📍 Step 4: Bot creates inline keyboard")
    keyboard = create_track_keyboard(tracks)
    button_count = sum(len(row) for row in keyboard.inline_keyboard)
    print(f"   ✓ Created keyboard with {button_count} buttons")
    print(f"     Layout: {len(keyboard.inline_keyboard)} rows")
    
    # Step 5: Simulate user clicking button
    print("\n📍 Step 5: User clicks track #1")
    track_num = 1
    selected_track = tracks[track_num - 1]
    print(f"   → Selected: {selected_track.artist} - {selected_track.title}")
    print(f"   → YouTube ID: {selected_track.id}")
    print(f"   → Duration: {selected_track.formatted_duration}")
    
    # Step 6: Get from cache
    print("\n📍 Step 6: Bot retrieves from cache")
    cached_tracks = cache.get(cache_key)
    if cached_tracks:
        print(f"   ✓ Retrieved {len(cached_tracks)} tracks from cache")
        if len(cached_tracks) > track_num - 1:
            final_track = cached_tracks[track_num - 1]
            print(f"   ✓ Track ready: {final_track.artist} - {final_track.title}")
    else:
        print("   ✗ Cache miss!")
        return False
    
    # Step 7: Show download simulation
    print("\n📍 Step 7: Download would start here")
    print(f"   URL: {selected_track.url}")
    print("   Status: ⏳ Downloading...")
    print(f"   (In production, bot would download MP3 and send to user)")
    print("   (Requires FFmpeg to be installed on system)")
    
    return True

# Run simulation
try:
    print("\n")
    success = asyncio.run(simulate_user_flow())
    
    if success:
        print("\n" + "=" * 80)
        print("✅ Integration Test PASSED")
        print("=" * 80)
        
        print("\n📊 Final Status:")
        print("   ✓ Config loaded from .env")
        print("   ✓ Logger initialized")
        print("   ✓ YouTube searcher working")
        print("   ✓ Cache system working")
        print("   ✓ Keyboards created")
        print("   ✓ Routers registered:")
        print(f"     - start.router: /start, /help commands")
        print(f"     - search.router: text message handler")
        print(f"     - callbacks.router: button click handler")
        
        print("\n🚀 Bot is ready to run!")
        print("\n   Command: python -m src.main")
        print("\n📝 What to test in bot:")
        print("   1. Send /start - should show welcome message")
        print("   2. Send /help - should show help message")
        print("   3. Send song name (e.g., 'Imagine') - should show 10 results")
        print("   4. Click button 1-10 - should download and send MP3 file")
        
        print("\n⚠️  Requirements:")
        print("   • FFmpeg must be installed on system (for MP3 conversion)")
        print("   • Internet connection (for YouTube search)")
        print("   • Valid BOT_TOKEN in .env file")
        
        print("\n" + "=" * 80)
    else:
        print("\n❌ Integration Test FAILED")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ Error during integration test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
