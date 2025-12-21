"""English translations."""

MESSAGES = {
    # General
    "welcome": (
        "🎵 <b>Welcome to UspMusicFinder Bot!</b>\n\n"
        "I'll help you find and download music from YouTube Music.\n\n"
        "<b>How to use:</b>\n"
        "1️⃣ Send me a song name or artist\n"
        "2️⃣ Choose a track from the list (buttons 1-10)\n"
        "3️⃣ Get your MP3 file!\n\n"
        "💡 Use menu buttons or just type a song name!\n\n"
        "Try searching for a song! 🎶"
    ),
    "help": (
        "🎵 <b>UspMusicFinder Bot - Help</b>\n\n"
        "<b>🔍 How to use:</b>\n"
        "1️⃣ Send a song name or artist\n"
        "2️⃣ Press the track number button (1-10)\n"
        "3️⃣ Get your MP3 file with metadata!\n\n"
        "<b>📝 Search examples:</b>\n"
        "• Bohemian Rhapsody\n"
        "• Queen\n"
        "• The Beatles Help\n\n"
        "<b>⚡ Commands:</b>\n"
        "  /start - Start the bot\n"
        "  /help - This help\n"
        "  /top - Popular songs 🔥\n"
        "  /recommendations - Personal recommendations 🎵\n"
        "  /history - Download history\n"
        "  /favorites - Favorite songs\n"
        "  /referral - Referral program\n"
        "  /lang - Change language\n\n"
        "💡 <b>Tip:</b> Be specific for better results!"
    ),

    # Keyboard buttons
    "btn_top": "🏆 Top Tracks",
    "btn_recommendations": "🎵 For You",
    "btn_history": "📜 History",
    "btn_favorites": "❤️ Favorites",
    "btn_premium": "⭐ Premium",
    "btn_referral": "👥 Referrals",
    "input_placeholder": "🔍 Enter song name...",

    # Search
    "search_results": "🎵 <b>Search results:</b> <code>{query}</code>\n<i>Found: {count} tracks</i>\n\n",
    "search_no_results": (
        "❌ <b>Nothing found</b>\n\n"
        "💡 Try:\n"
        "• Check the spelling\n"
        "• Use English\n"
        "• Type only the song or artist name"
    ),
    "search_choose_track": "👇 <b>Choose a track (1-{count})</b>",
    "search_page": "📄 Page {current}/{total}",

    # Rate limit
    "rate_limit": (
        "⏳ <b>Too many requests</b>\n\n"
        "Please wait {seconds} seconds\n\n"
        "<i>Limit: {limit} searches per minute</i>"
    ),

    # Download
    "downloading": "⏳ <b>Downloading...</b>\n\n🎵 {title}\n👤 {artist}",
    "download_success": "✅ Done!",
    "download_error": "❌ <b>Download error</b>\n\nTrack unavailable. Try another one.",
    "download_too_long": "⚠️ Track is too long (over 60 minutes). Choose another.",
    "track_promo": "🎵 Any music in seconds @UspMusicFinder_bot",

    # History
    "history_title": "📜 <b>Last 20 downloads:</b>\n\n",
    "history_empty": (
        "📜 <b>Download history is empty</b>\n\n"
        "You haven't downloaded any tracks yet.\n"
        "Send a song name to start searching!"
    ),
    "history_total": "📊 <b>Total downloaded:</b> {count} tracks",

    # Favorites
    "favorites_title": "❤️ <b>Favorites:</b>\n\n",
    "favorites_empty": (
        "❤️ <b>Favorites is empty</b>\n\n"
        "Add tracks to favorites with ❤️ button\n"
        "when viewing search results."
    ),
    "favorites_total": "📊 <b>Total in favorites:</b> {count}",
    "favorites_choose": "👇 <b>Press number to download</b>",
    "favorite_added": "❤️ Added to favorites!",
    "favorite_removed": "💔 Removed from favorites",
    "favorites_cleared": "🗑 <b>Favorites cleared</b>\n\nAll tracks removed from favorites.",

    # Top
    "top_title": "🏆 <b>TOP DOWNLOADED TRACKS</b>\n\nChoose period:",
    "top_period_day": "📅 Today",
    "top_period_week": "📆 Week",
    "top_period_month": "📊 Month",
    "top_period_all": "🏆 All time",
    "top_loading": "⏳ Loading top...",
    "top_empty": "📭 <b>Top {period}</b>\n\nNo downloads for this period yet.",
    "top_header": "🏆 <b>TOP-{count} {period}</b>\n\n",
    "top_choose": "👇 Choose a track number to download",
    "top_downloads": "downloads",

    # Recommendations
    "rec_title": "🎵 <b>RECOMMENDATIONS FOR YOU</b>\n\nBased on your {count} downloads:",
    "rec_no_history": (
        "🎵 <b>RECOMMENDATIONS</b>\n\n"
        "You don't have download history yet.\n"
        "Here are popular tracks this week:"
    ),
    "rec_error": "❌ Couldn't generate recommendations. Try later.",
    "rec_list_title": "🎵 <b>Recommended tracks:</b>\n\n",

    # Premium
    "premium_title": "⭐ <b>PREMIUM SUBSCRIPTION</b>\n\n",
    "premium_active": "✅ <b>You have Premium!</b>\n📅 Active until: {until}\n\n",
    "premium_inactive": "❌ <b>You don't have Premium subscription</b>\n\n",
    "premium_benefits": (
        "<b>Premium benefits:</b>\n"
        "• ♾ Unlimited downloads\n"
        "• 🚀 Queue priority\n"
        "• 🎵 Unlimited music recognition\n"
        "• ❤️ Unlimited favorites\n"
        "• 🎁 x2 referral bonuses\n\n"
        "<b>Choose a plan:</b>"
    ),
    "premium_thanks": (
        "🎉 <b>Thank you for your purchase!</b>\n\n"
        "✅ Premium activated!\n"
        "📅 Active until: {until}\n\n"
        "Enjoy unlimited downloads! 🎵"
    ),

    # Referral
    "referral_title": "👥 <b>REFERRAL PROGRAM</b>\n\nInvite friends and get bonuses!\n\n",
    "referral_rewards": (
        "🎁 <b>Rewards:</b>\n"
        "• +5 downloads for each invite\n"
        "• +10 downloads when they download 5 tracks\n\n"
    ),
    "referral_stats": (
        "📊 <b>Your stats:</b>\n"
        "• Invited: {referred}\n"
        "• Active: {active}\n"
        "• Bonuses: {bonus}\n\n"
    ),
    "referral_link": "🔗 <b>Your referral link:</b>\n<code>{link}</code>\n\n👇 Press button to share!",
    "referral_share": "📤 Share link",
    "referral_new": (
        "🎉 <b>New referral!</b>\n\n"
        "User {name} joined via your link.\n"
        "You got +5 bonus downloads!"
    ),

    # Language
    "lang_title": "🌐 <b>Choose language / Tilni tanlang / Выбери язык</b>",
    "lang_changed": "✅ Language changed to English",

    # Donate
    "donate_title": (
        "☕ <b>SUPPORT THE PROJECT</b>\n\n"
        "Your support helps develop the bot!\n\n"
        "All donations go to:\n"
        "• 🖥 Server costs\n"
        "• 🛠 New features development\n"
        "• 🐛 Bug fixes\n\n"
        "<b>Choose amount:</b>"
    ),
    "donate_thanks": (
        "❤️ <b>Thank you so much for your support!</b>\n\n"
        "Your donation helps the bot grow!\n"
        "We really appreciate your help! 🙏"
    ),

    # Recognition
    "recognize_title": "🎤 <b>MUSIC RECOGNITION</b>\n\n",
    "recognize_send_audio": "Send a voice message or audio,\nand I'll identify the song!",
    "recognize_processing": "🔍 Analyzing audio...",
    "recognize_not_found": "😕 Couldn't recognize the track.\nTry recording a clearer fragment.",
    "recognize_found": (
        "🎵 <b>Song found!</b>\n\n"
        "🎤 <b>{artist}</b>\n"
        "🎵 <b>{title}</b>\n"
        "{album}"
    ),

    # Errors
    "error_general": "❌ An error occurred. Try again later.",
    "error_expired": "❌ Results expired. Try searching again.",
    "error_refresh": "❌ Refresh the list",

    # Limits
    "limit_reached": (
        "⚠️ <b>Daily limit reached</b>\n\n"
        "Free: {free} downloads per day\n"
        "Remaining: {remaining}\n\n"
        "💎 Get Premium for unlimited!\n"
        "👥 Or invite a friend (+5 downloads)"
    ),
}
