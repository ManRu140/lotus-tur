"""
Начальные данные — туры и достижения.
Запускается один раз при инициализации БД.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tour import Tour
from app.models.achievement import Achievement


TOURS_SEED = [
    {
        "id": "askold",
        "tag": "Остров",
        "name": "Остров Аскольд",
        "description": "Старинные маяки, заброшенные военные батареи, нетронутая природа и стада пятнистых оленей посреди океана.",
        "price": 7500,
        "img_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-02,2026-06-03,2026-06-08,2026-06-12,2026-06-15,2026-06-22,2026-06-23,2026-06-30",
    },
    {
        "id": "triozerye",
        "tag": "Бухта",
        "name": "Бухта Триозерье",
        "description": "Бирюзовая чистейшая вода, знаменитый белый песок и живописные гранитные скалы-перья.",
        "price": 8000,
        "img_url": "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-01,2026-06-05,2026-06-06,2026-06-13,2026-06-14,2026-06-20,2026-06-21,2026-06-27",
    },
    {
        "id": "safari",
        "tag": "Драйв",
        "name": "Морской Сафари-тур",
        "description": "Скоростной тур на катерах к лежбищам нерп и тюленей Ларга в заливе Петра Великого.",
        "price": 9500,
        "img_url": "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-03,2026-06-04,2026-06-10,2026-06-11,2026-06-17,2026-06-18,2026-06-24,2026-06-25",
    },
    {
        "id": "sestra",
        "tag": "Треккинг",
        "name": "Гора Сестра",
        "description": "Восхождение на знаменитую вершину у устья реки Сучан, откуда открывается панорамный вид на залив Находка.",
        "price": 6000,
        "img_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-06,2026-06-07,2026-06-13,2026-06-14,2026-06-20,2026-06-21,2026-06-27,2026-06-28",
    },
    {
        "id": "okunevaya",
        "tag": "Релакс",
        "name": "Бухта Окуневая",
        "description": "Уединенные пляжи, лазурные волны и палаточные стоянки вдали от цивилизации.",
        "price": 7000,
        "img_url": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-09,2026-06-10,2026-06-16,2026-06-17,2026-06-23,2026-06-24,2026-06-30",
    },
    {
        "id": "petrova",
        "tag": "Легенда",
        "name": "Остров Петрова",
        "description": "Экскурсия в мистическую тисовую рощу острова, хранящую тайны древнего государства Бохай.",
        "price": 11000,
        "img_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-02,2026-06-09,2026-06-16,2026-06-23,2026-06-30",
    },
    {
        "id": "ocean",
        "tag": "Экскурсия",
        "name": "Морской Океанариум",
        "description": "Полноценный научно-познавательный тур на остров Русский с посещением одного из крупнейших океанариумов мира.",
        "price": 5500,
        "img_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-04,2026-06-11,2026-06-18,2026-06-25",
    },
]

ACHIEVEMENTS_SEED = [
    {
        "icon": "🌱",
        "title": "Первый шаг",
        "description": "Совершил первое путешествие с Лотос-тур.",
    },
    {
        "icon": "⛵",
        "title": "Морская душа",
        "description": "Побывал на морской прогулке на катере.",
    },
    {
        "icon": "🏝️",
        "title": "Исследователь островов",
        "description": "Посетил остров Аскольд или Путятин.",
    },
    {
        "icon": "⛰️",
        "title": "Покоритель вершин",
        "description": "Поднялся на сопку Сестра.",
    },
    {
        "icon": "🐅",
        "title": "Друг природы",
        "description": "Побывал в Сафари Парке.",
    },
    {
        "icon": "🐬",
        "title": "Житель глубин",
        "description": "Посетил Приморский океанариум.",
    },
    {
        "icon": "🏙️",
        "title": "Знаток Владивостока",
        "description": "Прошёл пешеходную экскурсию по Владивостоку.",
    },
    {
        "icon": "🌸",
        "title": "Хранитель лотоса",
        "description": "Увидел цветение лотосов на острове Путятин.",
    },
    {
        "icon": "💧",
        "title": "Охотник за водопадами",
        "description": "Посетил водопад Стеклянуха.",
    },
    {
        "icon": "🌅",
        "title": "Ранняя пташка",
        "description": "Забронировал тур за 7 и более дней до начала.",
    },
    {
        "icon": "🌟",
        "title": "Социальная звезда",
        "description": "Привёл друга по реферальной ссылке.",
    },
    {
        "icon": "🏖️",
        "title": "Пляжный маньяк",
        "description": "Посетил три разных пляжа и бухты.",
    },
    {
        "icon": "📸",
        "title": "Фотоохотник",
        "description": "Побывал на пяти различных турах.",
    },
    {
        "icon": "🧭",
        "title": "Штурман",
        "description": "Побывал и на морской, и на наземной экскурсии.",
    },
    {
        "icon": "🌿",
        "title": "Ботаник",
        "description": "Посетил ботанический сад во Владивостоке.",
    },
    {
        "icon": "🔦",
        "title": "Маяк",
        "description": "Увидел маяк Токаревский или Лихачёва.",
    },
    {
        "icon": "🏆",
        "title": "Преданный путешественник",
        "description": "Совершил десять путешествий с Лотос-тур.",
    },
    {
        "icon": "💎",
        "title": "Жемчужина Ливадии",
        "description": "Побывал в бухте Рифовая.",
    },
]


async def seed_initial_data(session: AsyncSession) -> None:
    """Добавляет туры и достижения, если таблицы пустые.

    Достижения досеиваются по названию: если в БД уже есть часть из них
    (например, старые 5), недостающие добавятся при следующем старте.
    """
    # Туры
    existing = await session.execute(select(Tour).limit(1))
    if not existing.scalar_one_or_none():
        for data in TOURS_SEED:
            session.add(Tour(**data))

    # Достижения — добавляем недостающие по title
    existing_titles_result = await session.execute(select(Achievement.title))
    existing_titles = {row[0] for row in existing_titles_result.all()}
    for data in ACHIEVEMENTS_SEED:
        if data["title"] not in existing_titles:
            session.add(Achievement(**data))

    await session.commit()
