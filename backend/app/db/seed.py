from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tour import Tour
from app.models.achievement import Achievement


TOURS_SEED = [
    {
        "id": "askold",
        "tag": "Остров",
        "name": "Остров Аскольд",
        "description": "Морской переход, тюлени ларги на лежбищах, руины старинных построек и величественный маяк Аскольд.",
        "price": 7500,
        "img_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-07,2026-06-14,2026-06-21,2026-06-28,2026-07-05,2026-07-12,2026-07-19,2026-07-26",
    },
    {
        "id": "triozerye",
        "tag": "Бухта",
        "name": "Бухта Триозерье",
        "description": "Белый песок с золотыми бликами, кристально чистая вода и гранитные скалы причудливых форм. Спокойный отдых у моря.",
        "price": 3000,
        "img_url": "img/tours/3_ozera_3.JPG",
        "booked_dates": None,
    },
    {
        "id": "okunevaya",
        "tag": "Релакс",
        "name": "Бухта Окуневая",
        "description": "Изумрудное море и белоснежный песок — идеальный спокойный отдых без групповых мероприятий.",
        "price": 3500,
        "img_url": "img/tours/okunev_1.JPG",
        "booked_dates": None,
    },
    {
        "id": "sea-cruise",
        "tag": "Море",
        "name": "Морская прогулка на катере",
        "description": "Прогулка по заливу Восток: утренние, дневные и закатные рейсы. Рыбалка на окуня, треску, камбалу и кальмар.",
        "price": 3000,
        "img_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=500&q=80",
        "booked_dates": None,
    },
    {
        "id": "safari",
        "tag": "Дикая природа",
        "name": "Сафари Парк (три парка)",
        "description": "Тигры, леопарды, медведи и олени в естественной среде обитания. Без клеток и ограждений.",
        "price": 5100,
        "img_url": "img/tours/safari_1.jpg",
        "booked_dates": "2026-06-08,2026-06-15,2026-06-22,2026-06-29,2026-07-06,2026-07-13,2026-07-20,2026-07-27",
    },
    {
        "id": "ocean",
        "tag": "Экскурсия",
        "name": "Приморский Океанариум",
        "description": "Один из крупнейших океанариумов мира на острове Русский. Обитатели всех океанов и климатических зон Земли.",
        "price": 3500,
        "img_url": "img/tours/oreonarium_2.JPG",
        "booked_dates": "2026-06-09,2026-06-16,2026-06-23,2026-06-30,2026-07-07,2026-07-14,2026-07-21,2026-07-28",
    },
    {
        "id": "livadia",
        "tag": "Побережье",
        "name": "Ливадийское побережье и бухта Рифовая",
        "description": "Экскурсия по Ливадийским бухтам, посещение музея и отдых на пляже бухты Рифовой.",
        "price": 3500,
        "img_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-10,2026-06-17,2026-06-24,2026-07-01,2026-07-08,2026-07-15",
    },
    {
        "id": "sestra",
        "tag": "Треккинг",
        "name": "Сопка Сестра + Бухта Лашкевича",
        "description": "Живописный подъём 40–60 минут. С вершины — панорама залива Находка, порта и бескрайнего Японского моря. Купание после.",
        "price": 3000,
        "img_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-11,2026-06-18,2026-06-25,2026-07-02,2026-07-09,2026-07-16",
    },
    {
        "id": "putyatin",
        "tag": "Остров",
        "name": "Красоты острова Путятин",
        "description": "Скалистые бухты и дикие побережья острова с борта катера. Купание в чистейших водах Японского моря.",
        "price": 6200,
        "img_url": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-12,2026-06-19,2026-06-26,2026-07-03,2026-07-10,2026-07-17",
    },
    {
        "id": "lotus",
        "tag": "Август",
        "name": "Путятин + цветение лотосов",
        "description": "Морское путешествие вокруг острова Путятин. Озеро, покрытое розовыми лотосами — незабываемое зрелище!",
        "price": 8000,
        "img_url": "https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=500&q=80",
        "booked_dates": None,
    },
    {
        "id": "vladivostok1",
        "tag": "Владивосток",
        "name": "Владивосток: Нагорный парк, маяк Токаревский",
        "description": "Нагорный парк с видом на город и залив, смотровая Бурачка, исторический Токаревский маяк — символ Владивостока.",
        "price": 4000,
        "img_url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-08,2026-06-15,2026-06-22,2026-06-29",
    },
    {
        "id": "botsad",
        "tag": "Владивосток",
        "name": "Ботсад + зоопарк Садгород + б.Стеклянная",
        "description": "Три в одном: тенистые аллеи ботсада, уютный зоопарк с любовью к животным и уникальный пляж бухты Стеклянной.",
        "price": 5500,
        "img_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-10,2026-06-17,2026-06-24",
    },
    {
        "id": "vladivostok2",
        "tag": "Владивосток",
        "name": "Музей ДВ + пешеходная экскурсия",
        "description": "Музей Арсеньева и пешеходная экскурсия по центру: Светланская, набережная Амурского залива, Корабельная набережная.",
        "price": 6500,
        "img_url": "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=500&q=80",
        "booked_dates": "2026-06-11,2026-06-18,2026-06-25",
    },
    {
        "id": "waterfall",
        "tag": "По запросу",
        "name": "Водопад Стеклянуха",
        "description": "Водопад высотой 12 метров, окружённый вулканическими восьмиугольными столбами. Громкий, красивый, завораживающий.",
        "price": 5000,
        "img_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=500&q=80",
        "booked_dates": None,
    },
    {
        "id": "individual",
        "tag": "Индивидуально",
        "name": "Индивидуальная экскурсия по Находке",
        "description": "Городская часть + природная локация на выбор: мыс Пассека, маяк Лихачёва, тропа Осьминога, японский сад Эниси, Ливадия.",
        "price": 12000,
        "img_url": "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=500&q=80",
        "booked_dates": None,
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
    {
        "icon": "🐆",
        "title": "След леопарда",
        "description": "Побывал в национальном парке «Земля леопарда».",
    },
    {
        "icon": "🌉",
        "title": "Стальная нить",
        "description": "Пересёк Русский мост на остров Русский.",
    },
    {
        "icon": "🦀",
        "title": "Краболов",
        "description": "Попробовал свежего камчатского краба в туре.",
    },
    {
        "icon": "⚓",
        "title": "Морской волк",
        "description": "Прошёл три морских тура.",
    },
    {
        "icon": "🐋",
        "title": "Встреча с гигантом",
        "description": "Увидел кита или косатку в заливе Петра Великого.",
    },
    {
        "icon": "🏰",
        "title": "Хранитель крепости",
        "description": "Посетил форты Владивостокской крепости.",
    },
    {
        "icon": "❄️",
        "title": "Зимний странник",
        "description": "Отправился в тур в зимний сезон.",
    },
    {
        "icon": "🎣",
        "title": "Удачный клёв",
        "description": "Принял участие в рыболовном туре.",
    },
    {
        "icon": "🛶",
        "title": "Покоритель волн",
        "description": "Прошёл маршрут на каяке или сапборде.",
    },
    {
        "icon": "🦇",
        "title": "Спелеолог",
        "description": "Спустился в пещеры Екатериновского массива.",
    },
    {
        "icon": "⛺",
        "title": "Под звёздами",
        "description": "Провёл ночь в палаточном лагере.",
    },
    {
        "icon": "🚂",
        "title": "Конечная станция",
        "description": "Побывал на вокзале Владивостока — финише Транссиба.",
    },
    {
        "icon": "🦭",
        "title": "Друг нерпы",
        "description": "Увидел нерп на лежбище во время сафари-тура.",
    },
]


async def seed_initial_data(session: AsyncSession) -> None:
    existing_ids_result = await session.execute(select(Tour.id))
    existing_ids = {row[0] for row in existing_ids_result.all()}
    for data in TOURS_SEED:
        if data["id"] not in existing_ids:
            session.add(Tour(**data))


    existing_titles_result = await session.execute(select(Achievement.title))
    existing_titles = {row[0] for row in existing_titles_result.all()}
    for data in ACHIEVEMENTS_SEED:
        if data["title"] not in existing_titles:
            session.add(Achievement(**data))

    await session.commit()
