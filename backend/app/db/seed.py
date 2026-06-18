from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.tour import Tour
from app.models.achievement import Achievement
from app.models.review import Review
from app.models.user import User

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
        "schedule": "Ежедневно",
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
        "schedule": "Ежедневно",
        "booked_dates": None,
    },
    {
        "id": "safari",
        "tag": "Дикая природа",
        "name": "Сафари Парк (три парка)",
        "description": "Тигры, леопарды, медведи и олени в естественной среде обитания. Без клеток и ограждений.",
        "price": 5100,
        "img_url": "img/tours/safari_1.jpg",
        "schedule": "Среда",
        "booked_dates": "2026-06-08,2026-06-15,2026-06-22,2026-06-29,2026-07-06,2026-07-13,2026-07-20,2026-07-27",
    },
    {
        "id": "ocean",
        "tag": "Экскурсия",
        "name": "Приморский Океанариум",
        "description": "Один из крупнейших океанариумов мира на острове Русский. Обитатели всех океанов и климатических зон Земли.",
        "price": 3500,
        "img_url": "img/tours/oreonarium_2.JPG",
        "schedule": "Пятница",
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
        "schedule": "Четверг",
        "booked_dates": "2026-06-10,2026-06-17,2026-06-24",
    },
    {
        "id": "vladivostok2",
        "tag": "Владивосток",
        "name": "Музей ДВ + пешеходная экскурсия",
        "description": "Музей Арсеньева и пешеходная экскурсия по центру: Светланская, набережная Амурского залива, Корабельная набережная.",
        "price": 6500,
        "img_url": "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=500&q=80",
        "schedule": "Вторник",
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
    {
        "id": "yacht",
        "tag": "Море",
        "name": "Морская прогулка на яхте",
        "description": "Морская прогулка на яхте по заливу Восток. Уединение и свобода — только море, небо, ветер в парусах и ваша компания. Погружение в гармонию моря и момент истинной свободы.",
        "price": 3700,
        "img_url": "https://images.unsplash.com/photo-1500627964684-141351970a7c?auto=format&fit=crop&w=500&q=80",
        "schedule": "Ежедневно",
        "booked_dates": None,
    },
    {
        "id": "kravtsovsky",
        "tag": "Водопады",
        "name": "Кравцовские водопады + парк «Белый лев» и ферма альпак",
        "description": "Эко-тропа сквозь тайгу к каскаду из пяти водопадов, затем парк «Белый лев» со львами и львятами в просторных вольерах, и ферма альпак — самых дружелюбных обитателей Приморья.",
        "price": 4500,
        "img_url": "https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?auto=format&fit=crop&w=500&q=80",
        # Originally ran every other Monday ("через неделю") — the current
        # schedule model only supports a single fixed weekday, not a
        # biweekly cadence, so this is set to the closest single value.
        # Adjust via Admin → Расписание if a different default reads better.
        "schedule": "Понедельник",
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

# Migrated from the static marquee that used to be hardcoded directly
# into frontend/index.html — now real rows so the reviews section is
# 100% dynamic (fetched from GET /api/reviews) from day one instead of
# showing an empty list until someone adds the first real review.
# tour_id left as None where the original copy didn't clearly match a
# tour still in the current catalog, rather than guessing wrong.
REVIEWS_SEED = [
    {
        "author_name": "Игорь К.",
        "rating": 5,
        "text": "Тур на остров Аскольд — лучшее, что я делал в жизни. Гиды профессиональные, атмосфера потрясающая.",
        "tour_id": "askold",
    },
    {
        "author_name": "Анна П.",
        "rating": 5,
        "text": "Бухта Триозерье — сказка! Вода чистейшая, инструкторы заботливые. Обязательно вернёмся снова.",
        "tour_id": "triozerye",
    },
    {
        "author_name": "Сергей М.",
        "rating": 5,
        "text": "Морской сафари-тур — адреналин, нерпы и брызги океана. Никаких слов, только эмоции!",
        "tour_id": None,
    },
    {
        "author_name": "Ольга Н.",
        "rating": 5,
        "text": "Остров Петрова — мистика и тишина. Тисовая роща, древние тайны. Настоящее путешествие во времени.",
        "tour_id": None,
    },
    {
        "author_name": "Дмитрий С.",
        "rating": 5,
        "text": "Пик Сестра буквально открыл мне глаза на красоту Приморья. Закат оттуда — это что-то нереальное.",
        "tour_id": "sestra",
    },
    {
        "author_name": "Елена В.",
        "rating": 5,
        "text": "Сафари-парк превзошел все ожидания. Видели тигра в 10 метрах от нас — незабываемо!",
        "tour_id": "safari",
    },
]

# Real testimonials migrated from the old site (2011–2016) — trimmed and
# lightly cleaned up (stray reply fragments removed, one very long
# article-style review condensed to an excerpt) but otherwise the
# author's own words. tour_id matched only where the original clearly
# names a tour still in the current catalog; left None elsewhere rather
# than guessing. created_at is set to the original posting date so
# these read as the real history they are, not as if written today.
HISTORICAL_REVIEWS_SEED = [
    {
        "author_name": "Rishka",
        "rating": 5,
        "text": "Хотим выразить большую благодарность замечательной компании Лотос-тур, с которой мы уже путешествуем много лет, а также экскурсоводу Кабелеву С.В. за потрясающую экскурсию на остров Лисий. Спасибо вам большое за то, что вы нам открыли и показали этот необыкновенный остров.",
        "tour_id": None,
        "created_at": datetime(2016, 8, 19, 12, 0, tzinfo=timezone.utc),
    },
    {
        "author_name": "Галина Дьяконова",
        "rating": 5,
        "text": "Большое спасибо за проведённую экскурсию на остров Путятин — лотосы и танцующие страусы! Нам всё очень понравилось, было очень здорово. Мы рады сотрудничать с компанией Лотос-тур. Как же здорово, что в нашем городе есть такие компании!",
        "tour_id": "lotus",
        "created_at": datetime(2015, 8, 16, 12, 0, tzinfo=timezone.utc),
    },
    {
        "author_name": "Галина Дьяконова",
        "rating": 5,
        "text": "Нам очень понравилась экскурсия на водопад «Стеклянуха», было очень интересно и вкусно, попалась очень хорошая компания. Всё было здорово, благодарим за организацию экскурсии. Теперь будем путешествовать только с компанией Лотос-тур!",
        "tour_id": "waterfall",
        "created_at": datetime(2015, 6, 7, 12, 0, tzinfo=timezone.utc),
    },
    {
        "author_name": "anastasiya",
        "rating": 5,
        "text": "Большое спасибо за проведённую обзорную экскурсию по городу Находка с детьми 1 «А» класса. Всё было изложено доступным для детей языком, познавательно, интересно и содержательно. Отдельное спасибо за экскурсию по храму — у детей вызвала большой интерес и обсуждение.",
        "tour_id": None,
        "created_at": datetime(2014, 3, 24, 12, 0, tzinfo=timezone.utc),
    },
    {
        "author_name": "Девчина",
        "rating": 5,
        "text": "Спасибо компании за бережное, внимательное и заботливое отношение к туристам! Отдельное спасибо инструкторам, которые на протяжении всего восхождения на гору Ольховую вели группу — впечатлил профессионализм и неиссякаемые физические возможности этих людей. Осталось море положительных воспоминаний и впечатлений!",
        "tour_id": None,
        "created_at": datetime(2011, 10, 3, 12, 0, tzinfo=timezone.utc),
    },
    {
        "author_name": "Марина Маркова",
        "rating": 5,
        "text": "Экскурсия на остров Петрова — сказка наяву! Лазурная вода такая прозрачная, что видна каждая складочка на белоснежном песчаном дне, а внизу лениво плавают непуганые рыбы. От красоты буквально сносит крышу. Спасибо сотрудникам компании, которые открыли для моей семьи отдых на родных берегах, не уступающий по красоте тропическим широтам!",
        "tour_id": None,
        "created_at": datetime(2011, 9, 14, 12, 0, tzinfo=timezone.utc),
    },
    {
        "author_name": "Евгений Шестаков",
        "rating": 5,
        "text": "Вы самая лучшая компания на всей планете! Спасибо что Вы есть!!!",
        "tour_id": None,
        "created_at": datetime(2011, 1, 3, 12, 0, tzinfo=timezone.utc),
    },
]


async def seed_initial_data(session: AsyncSession) -> None:
    # ── Bootstrap admin user ───────────────────────────────────────────
    # Runs only when ADMIN_PASSWORD is set (non-empty) in the environment.
    # On Railway: set ADMIN_USERNAME + ADMIN_PASSWORD as env vars before
    # first deploy. The account is created once and never overwritten, so
    # changing the env vars later has no effect — use Admin → Users to
    # reset the password after the initial login.
    if settings.ADMIN_PASSWORD:
        existing_admin = (
            await session.execute(
                select(User).where(User.username == settings.ADMIN_USERNAME)
            )
        ).scalar_one_or_none()
        if not existing_admin:
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                email=f"{settings.ADMIN_USERNAME}@lotos-tour.local",
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                full_name="Администратор",
                is_active=True,
                is_admin=True,
                role="admin",
            )
            session.add(admin_user)
            await session.flush()  # give the user an id before continuing

    existing_ids_result = await session.execute(select(Tour.id))
    existing_ids = {row[0] for row in existing_ids_result.all()}
    for data in TOURS_SEED:
        if data["id"] not in existing_ids:
            session.add(Tour(**data))

    # One-time correction of weekly schedule days for tours that already
    # existed before the `schedule` column did (it defaulted every tour
    # to "По запросу"). Only touches rows still sitting at that default,
    # so it can never overwrite a value an admin deliberately set via
    # Admin → Расписание.
    SCHEDULE_CORRECTIONS = {
        "triozerye": "Ежедневно",
        "sea-cruise": "Ежедневно",
        "vladivostok2": "Вторник",
        "safari": "Среда",
        "botsad": "Четверг",
        "ocean": "Пятница",
    }
    for tour_id, correct_schedule in SCHEDULE_CORRECTIONS.items():
        tour = await session.get(Tour, tour_id)
        if tour and tour.schedule == "По запросу":
            tour.schedule = correct_schedule

    existing_titles_result = await session.execute(select(Achievement.title))
    existing_titles = {row[0] for row in existing_titles_result.all()}
    for data in ACHIEVEMENTS_SEED:
        if data["title"] not in existing_titles:
            session.add(Achievement(**data))

    # Reviews: dedup by (author_name, text) rather than "table empty" —
    # this lets REVIEWS_SEED/HISTORICAL_REVIEWS_SEED grow over time
    # (e.g. another batch of migrated testimonials later) without the
    # whole table needing to still be empty for the new ones to land,
    # while still never re-adding something an admin deleted on purpose
    # under the exact same name+text.
    existing_reviews_result = await session.execute(select(Review.author_name, Review.text))
    existing_review_keys = {(name, text) for name, text in existing_reviews_result.all()}
    for data in REVIEWS_SEED + HISTORICAL_REVIEWS_SEED:
        key = (data["author_name"], data["text"])
        if key in existing_review_keys:
            continue
        review_fields = {k: v for k, v in data.items() if k != "created_at"}
        review = Review(source="site", is_published=True, **review_fields)
        if "created_at" in data:
            review.created_at = data["created_at"]
        session.add(review)
        existing_review_keys.add(key)

    await session.commit()
