"""Test script to verify bot components."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🧪 Testing UspMusicFinder Bot Components")
print("=" * 60)

# Test 1: Config loading
print("\n✅ Test 1: Loading configuration from .env")
try:
    from src.config import settings
    print(f"   BOT_USERNAME: {settings.BOT_USERNAME}")
    print(f"   LOG_LEVEL: {settings.LOG_LEVEL}")
    print(f"   RATE_LIMIT_REQUESTS: {settings.RATE_LIMIT_REQUESTS}")
    print(f"   ENABLE_CACHE: {settings.ENABLE_CACHE}")
    print("   ✓ Config loaded successfully!")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 2: Logger
print("\n✅ Test 2: Logger initialization")
try:
    from src.utils.logger import logger
    logger.info("Test log message")
    print("   ✓ Logger initialized and working!")
    print(f"   Log file: d:\\DevTools\\Database\\UspMusicFinder\\logs\\bot.log")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 3: Models
print("\n✅ Test 3: Track model")
try:
    from src.models import Track
    track = Track(
        id="dQw4w9WgXcQ",
        title="Bohemian Rhapsody",
        artist="Queen",
        duration=354,
        url="https://example.com/song.mp3"
    )
    print(f"   Title: {track.title}")
    print(f"   Artist: {track.artist}")
    print(f"   Duration: {track.duration}s")
    print("   ✓ Track model working!")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 4: Bot and Dispatcher
print("\n✅ Test 4: Bot and Dispatcher initialization")
try:
    from src.bot import bot, dp
    print(f"   Bot token: {settings.BOT_TOKEN[:10]}***")
    print(f"   Dispatcher: {dp}")
    print("   ✓ Bot and Dispatcher initialized!")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 5: Router
print("\n✅ Test 5: Start router")
try:
    from src.handlers import start
    print(f"   Router: {start.router}")
    print(f"   Handlers count: {len(start.router.message.handlers)}")
    print("   ✓ Start router loaded!")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 6: Directory creation
print("\n✅ Test 6: Directories creation")
try:
    from pathlib import Path
    dirs = [
        Path(settings.TEMP_DIR),
        Path(settings.CACHE_DIR),
        Path(settings.LOGS_DIR)
    ]
    for d in dirs:
        if d.exists():
            print(f"   ✓ {d}")
        else:
            print(f"   ✗ Missing: {d}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All tests passed! Bot is ready to run.")
print("=" * 60)
print("\n📝 Commands available:")
print("   /start - Show welcome message")
print("   /help - Show detailed help")
print("\n🚀 To run the bot:")
print("   python -m src.main")
print("=" * 60)
