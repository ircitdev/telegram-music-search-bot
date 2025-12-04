"""TOP popular songs handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.searchers.youtube import youtube_searcher
from src.keyboards import create_track_keyboard
from src.utils.cache import cache
from src.utils.logger import logger
from src.database.repositories import user_repo

router = Router()

# TOP tracks for different countries
TOP_TRACKS = {
    "🇷🇺 Россия": [
        "Сплин Время назад",
        "Кино Группа крови",
        "Виктор Цой Кино",
        "Руки Вверх Компромисс",
        "Агата Кристи Все грёзы о любви",
        "Чайф Огурец",
        "Коррозия Металла Демоны",
        "Город 312 Злая собака",
        "Quest Пись",
        "HammAli Navai Мотылек",
    ],
    "🇬🇧 English": [
        "The Weeknd Blinding Lights",
        "Ed Sheeran Shape of You",
        "Dua Lipa Don't Start Now",
        "Post Malone Circles",
        "Drake One Dance",
        "The Weeknd Starboy",
        "Ariana Grande Thank U Next",
        "Billie Eilish Bad Guy",
        "Olivia Rodrigo drivers license",
        "Harry Styles As It Was",
    ],
    "🇺🇿 Uzbek": [
        "Ozodbek Nazarbekov Mehriman",
        "Shahzoda Hammam sham",
        "Jonibek Murodov Yulduz",
        "Navro'z Navro'z Keldi",
        "Dilfuza Rahimova Oyna",
        "Hilola Samirova Oyna",
        "Valijon Va Ramazon Sevgi",
        "Temur Alakbarov Yasam",
        "Moda Ramazon Pakilik",
        "Qani Togayev Tushum bor",
    ],
    "🇰🇿 Kazakh": [
        "Dimash Kudaibergen SOS",
        "Ninety One Samal",
        "Ka Pella Mina Senim",
        "Aydos Shodmanov Oba",
        "Konay Aidynbek Kyz",
        "Alizhan Kuzibaev Kesiyya",
        "Zarina Karimova Kazakhzhan",
        "Taynan Aytugan Amanaman",
        "Gajek Yeraliev Alma",
        "Ramazan Bekbolatov Kyz",
    ],
    "🇹🇷 Turkish": [
        "Ajda Pekkan Unutamazsin",
        "Tarkan Simarik",
        "Sertab Erener Beni Bana Birak",
        "Murat Boz Sensiz",
        "Gokhan Ozen Duymamis Gibi",
        "Yulduz Usmonova Chiroyli",
        "Nilufar Usmonova Yoldosh",
        "Firdavs Abdullayev Navoi",
        "Elbek Akbarov Sevgi",
        "Aziza Zaripova Mehnat",
    ],
}


@router.message(Command("top"))
async def cmd_top(message: Message):
    """Show country selection for TOP tracks."""
    buttons = []
    for country_name in TOP_TRACKS.keys():
        buttons.append(
            [InlineKeyboardButton(
                text=country_name,
                callback_data=f"top_country:{country_name.split()[0]}"
            )]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "🎵 <b>TOP Popular Songs</b>\n\n"
        "Выбери страну:\n\n"
        "<i>Нажми на флаг чтобы увидеть топ 10 треков</i>",
        reply_markup=keyboard
    )
    logger.info(f"User {message.from_user.id} opened TOP menu")


@router.callback_query(F.data.startswith("top_country:"))
async def top_country_callback(callback: CallbackQuery):
    """Show TOP tracks for selected country."""
    try:
        country_code = callback.data.split(":")[1]
        user_id = callback.from_user.id

        # Find country by first emoji character
        country_name = None
        for key in TOP_TRACKS.keys():
            if key.startswith(country_code):
                country_name = key
                break

        if not country_name:
            await callback.answer("❌ Страна не найдена", show_alert=True)
            return

        await callback.message.edit_text("⏳ <b>Загрузка топ треков...</b>")

        # Get top tracks for country
        top_queries = TOP_TRACKS[country_name]
        tracks = []

        logger.info(f"Loading TOP tracks for {country_name} for user {user_id}")

        # Search first 10 tracks
        for i, query in enumerate(top_queries[:10]):
            try:
                results = await youtube_searcher.search(query)
                if results:
                    track = results[0]  # Take first result
                    track.id = f"top_{country_code}_{i}"  # Mark as TOP track
                    tracks.append(track)
                    logger.debug(f"Found track {i+1}: {track.artist} - {track.title}")
            except Exception as e:
                logger.error(f"Error searching track '{query}': {e}")
                continue

        if not tracks:
            await callback.message.edit_text(
                "❌ <b>Ошибка загрузки</b>\n\n"
                "Не удалось загрузить топ треки. Попробуй позже."
            )
            return

        # Cache tracks
        cache_key = f"search:{user_id}"
        cache.set(cache_key, tracks, ttl=3600)  # 1 hour
        cache.set(f"query:{user_id}", f"TOP {country_name}", ttl=3600)

        # Format TOP list
        text = f"🎵 <b>TOP Popular Songs</b>\n"
        text += f"{country_name}\n\n"

        for i, track in enumerate(tracks, 1):
            icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<b>{i}</b>."
            text += (
                f"{icon} <b>{track.artist}</b>\n"
                f"   🎤 <i>{track.title}</i>\n"
                f"   ⏱️ <code>{track.formatted_duration}</code>\n\n"
            )

        text += "👇 <b>Выбери номер трека (1-10):</b>"

        keyboard = create_track_keyboard(tracks)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

        # Record in database
        await user_repo.increment_searches(user_id)
        logger.info(f"User {user_id} viewed TOP {country_name}")

    except Exception as e:
        logger.error(f"Error in top_country_callback: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
