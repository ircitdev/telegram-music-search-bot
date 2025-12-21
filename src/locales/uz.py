"""Uzbek translations."""

MESSAGES = {
    # General
    "welcome": (
        "🎵 <b>UspMusicFinder Bot-ga xush kelibsiz!</b>\n\n"
        "Men sizga YouTube Music'dan musiqa topib, yuklab olishga yordam beraman.\n\n"
        "<b>Qanday foydalanish:</b>\n"
        "1️⃣ Menga qo'shiq yoki ijrochi nomini yuboring\n"
        "2️⃣ Ro'yxatdan trekni tanlang (1-10 tugmalar)\n"
        "3️⃣ MP3 faylingizni oling!\n\n"
        "💡 Menyu tugmalaridan foydalaning yoki qo'shiq nomini yozing!\n\n"
        "Qo'shiq qidirib ko'ring! 🎶"
    ),
    "help": (
        "🎵 <b>UspMusicFinder Bot - Yordam</b>\n\n"
        "<b>🔍 Qanday foydalanish:</b>\n"
        "1️⃣ Qo'shiq yoki ijrochi nomini yuboring\n"
        "2️⃣ Trek raqami tugmasini bosing (1-10)\n"
        "3️⃣ Metama'lumotli MP3 faylingizni oling!\n\n"
        "<b>📝 Qidiruv misollari:</b>\n"
        "• Bohemian Rhapsody\n"
        "• Queen\n"
        "• The Beatles Help\n\n"
        "<b>⚡ Buyruqlar:</b>\n"
        "  /start - Botni ishga tushirish\n"
        "  /help - Yordam\n"
        "  /top - Mashhur qo'shiqlar 🔥\n"
        "  /recommendations - Shaxsiy tavsiyalar 🎵\n"
        "  /history - Yuklab olish tarixi\n"
        "  /favorites - Sevimli qo'shiqlar\n"
        "  /referral - Referal dasturi\n"
        "  /lang - Tilni o'zgartirish\n\n"
        "💡 <b>Maslahat:</b> Yaxshi natija uchun aniq yozing!"
    ),

    # Keyboard buttons
    "btn_top": "🏆 Top treklar",
    "btn_recommendations": "🎵 Siz uchun",
    "btn_history": "📜 Tarix",
    "btn_favorites": "❤️ Sevimlilar",
    "btn_premium": "⭐ Premium",
    "btn_referral": "👥 Referallar",
    "input_placeholder": "🔍 Qo'shiq nomini kiriting...",

    # Search
    "search_results": "🎵 <b>Qidiruv natijalari:</b> <code>{query}</code>\n<i>Topildi: {count} ta trek</i>\n\n",
    "search_no_results": (
        "❌ <b>Hech narsa topilmadi</b>\n\n"
        "💡 Urinib ko'ring:\n"
        "• Yozuvni tekshiring\n"
        "• Ingliz tilida yozing\n"
        "• Faqat qo'shiq yoki ijrochi nomini yozing"
    ),
    "search_choose_track": "👇 <b>Trekni tanlang (1-{count})</b>",
    "search_page": "📄 Sahifa {current}/{total}",

    # Rate limit
    "rate_limit": (
        "⏳ <b>Juda ko'p so'rov</b>\n\n"
        "Iltimos, {seconds} soniya kuting\n\n"
        "<i>Limit: daqiqada {limit} ta qidiruv</i>"
    ),

    # Download
    "downloading": "⏳ <b>Yuklanmoqda...</b>\n\n🎵 {title}\n👤 {artist}",
    "download_success": "✅ Tayyor!",
    "download_error": "❌ <b>Yuklashda xato</b>\n\nTrek mavjud emas. Boshqasini sinab ko'ring.",
    "download_too_long": "⚠️ Trek juda uzun (60 daqiqadan ko'p). Boshqasini tanlang.",
    "track_promo": "🎵 Soniyalarda istalgan musiqa @UspMusicFinder_bot",

    # History
    "history_title": "📜 <b>Oxirgi 20 ta yuklab olish:</b>\n\n",
    "history_empty": (
        "📜 <b>Yuklab olish tarixi bo'sh</b>\n\n"
        "Siz hali hech qanday trek yuklamadingiz.\n"
        "Qidirishni boshlash uchun qo'shiq nomini yuboring!"
    ),
    "history_total": "📊 <b>Jami yuklangan:</b> {count} ta trek",

    # Favorites
    "favorites_title": "❤️ <b>Sevimlilar:</b>\n\n",
    "favorites_empty": (
        "❤️ <b>Sevimlilar bo'sh</b>\n\n"
        "Qidiruv natijalarini ko'rishda ❤️ tugmasi bilan\n"
        "treklarni sevimlilarga qo'shing."
    ),
    "favorites_total": "📊 <b>Jami sevimlilarda:</b> {count}",
    "favorites_choose": "👇 <b>Yuklash uchun raqamni bosing</b>",
    "favorite_added": "❤️ Sevimlilarga qo'shildi!",
    "favorite_removed": "💔 Sevimlilardan o'chirildi",
    "favorites_cleared": "🗑 <b>Sevimlilar tozalandi</b>\n\nBarcha treklar o'chirildi.",

    # Top
    "top_title": "🏆 <b>ENG KO'P YUKLANGAN TREKLAR</b>\n\nDavrni tanlang:",
    "top_period_day": "📅 Bugun",
    "top_period_week": "📆 Hafta",
    "top_period_month": "📊 Oy",
    "top_period_all": "🏆 Hammasi",
    "top_loading": "⏳ Top yuklanmoqda...",
    "top_empty": "📭 <b>Top {period}</b>\n\nBu davr uchun hali yuklab olish yo'q.",
    "top_header": "🏆 <b>TOP-{count} {period}</b>\n\n",
    "top_choose": "👇 Yuklash uchun trek raqamini tanlang",
    "top_downloads": "ta yuklab olish",

    # Recommendations
    "rec_title": "🎵 <b>SIZ UCHUN TAVSIYALAR</b>\n\n{count} ta yuklashingiz asosida:",
    "rec_no_history": (
        "🎵 <b>TAVSIYALAR</b>\n\n"
        "Sizda hali yuklab olish tarixi yo'q.\n"
        "Mana bu haftaning mashhur treklari:"
    ),
    "rec_error": "❌ Tavsiyalar tuzib bo'lmadi. Keyinroq urinib ko'ring.",
    "rec_list_title": "🎵 <b>Tavsiya etilgan treklar:</b>\n\n",

    # Premium
    "premium_title": "⭐ <b>PREMIUM OBUNA</b>\n\n",
    "premium_active": "✅ <b>Sizda Premium bor!</b>\n📅 Amal qiladi: {until}\n\n",
    "premium_inactive": "❌ <b>Sizda Premium obuna yo'q</b>\n\n",
    "premium_benefits": (
        "<b>Premium afzalliklari:</b>\n"
        "• ♾ Cheksiz yuklab olish\n"
        "• 🚀 Navbatda ustuvorlik\n"
        "• 🎵 Cheksiz musiqa aniqlash\n"
        "• ❤️ Cheksiz sevimlilar\n"
        "• 🎁 x2 referal bonuslari\n\n"
        "<b>Tarifni tanlang:</b>"
    ),
    "premium_thanks": (
        "🎉 <b>Xaridingiz uchun rahmat!</b>\n\n"
        "✅ Premium faollashtirildi!\n"
        "📅 Amal qiladi: {until}\n\n"
        "Cheksiz yuklab olishdan rohatlaning! 🎵"
    ),

    # Referral
    "referral_title": "👥 <b>REFERAL DASTURI</b>\n\nDo'stlaringizni taklif qiling va bonuslar oling!\n\n",
    "referral_rewards": (
        "🎁 <b>Mukofotlar:</b>\n"
        "• Har bir taklif uchun +5 yuklab olish\n"
        "• Ular 5 trek yuklaganida +10 yuklab olish\n\n"
    ),
    "referral_stats": (
        "📊 <b>Sizning statistikangiz:</b>\n"
        "• Taklif qilingan: {referred}\n"
        "• Faol: {active}\n"
        "• Bonuslar: {bonus}\n\n"
    ),
    "referral_link": "🔗 <b>Sizning referal havolangiz:</b>\n<code>{link}</code>\n\n👇 Ulashish uchun tugmani bosing!",
    "referral_share": "📤 Havolani ulashish",
    "referral_new": (
        "🎉 <b>Yangi referal!</b>\n\n"
        "Foydalanuvchi {name} sizning havolangiz orqali qo'shildi.\n"
        "Siz +5 bonus yuklab olish oldingiz!"
    ),

    # Language
    "lang_title": "🌐 <b>Tilni tanlang / Choose language / Выбери язык</b>",
    "lang_changed": "✅ Til O'zbek tiliga o'zgartirildi",

    # Donate
    "donate_title": (
        "☕ <b>LOYIHANI QO'LLAB-QUVVATLASH</b>\n\n"
        "Sizning yordamingiz botni rivojlantirishga yordam beradi!\n\n"
        "Barcha xayriyalar quyidagilarga ketadi:\n"
        "• 🖥 Server xarajatlari\n"
        "• 🛠 Yangi funksiyalar ishlab chiqish\n"
        "• 🐛 Xatolarni tuzatish\n\n"
        "<b>Summani tanlang:</b>"
    ),
    "donate_thanks": (
        "❤️ <b>Yordamingiz uchun katta rahmat!</b>\n\n"
        "Sizning xayriyangiz bot rivojlanishiga yordam beradi!\n"
        "Yordamingizni juda qadrlaymiz! 🙏"
    ),

    # Recognition
    "recognize_title": "🎤 <b>MUSIQA ANIQLASH</b>\n\n",
    "recognize_send_audio": "Ovozli xabar yoki audio yuboring,\nva men qo'shiqni aniqlayman!",
    "recognize_processing": "🔍 Audio tahlil qilinmoqda...",
    "recognize_not_found": "😕 Trekni aniqlab bo'lmadi.\nAniqroq parcha yozib ko'ring.",
    "recognize_found": (
        "🎵 <b>Qo'shiq topildi!</b>\n\n"
        "🎤 <b>{artist}</b>\n"
        "🎵 <b>{title}</b>\n"
        "{album}"
    ),

    # Errors
    "error_general": "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
    "error_expired": "❌ Natijalar eskirgan. Qaytadan qidiring.",
    "error_refresh": "❌ Ro'yxatni yangilang",

    # Limits
    "limit_reached": (
        "⚠️ <b>Kunlik limit tugadi</b>\n\n"
        "Bepul: kuniga {free} ta yuklab olish\n"
        "Qolgan: {remaining}\n\n"
        "💎 Cheksiz uchun Premium oling!\n"
        "👥 Yoki do'stingizni taklif qiling (+5 yuklab olish)"
    ),
}
