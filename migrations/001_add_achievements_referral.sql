ALTER TABLE tours ADD COLUMN IF NOT EXISTS bookings_count INTEGER DEFAULT 0;
ALTER TABLE tours ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;
ALTER TABLE tours ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';

CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(10) NOT NULL,
    unlock_condition VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id INTEGER NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    tour_booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_id)
);

CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referee_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ref_code VARCHAR(32) UNIQUE NOT NULL,
    discount_percent INTEGER DEFAULT 10,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS ref_code VARCHAR(32) UNIQUE;

ALTER TABLE bookings ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'booked';

UPDATE bookings SET status = 'booked' WHERE status IS NULL;

INSERT INTO achievements (code, name, description, icon, unlock_condition) VALUES
('FIRST_TRIP',      'Первый шаг',          'Совершил первое путешествие',              '🌱', 'first_booking'),
('SEA_LOVER',       'Морская душа',         'Побывал на морской прогулке на катере',    '⛵', 'tour_sea_cruise'),
('ISLAND_EXPLORER', 'Исследователь островов','Посетил остров Аскольд или Путятин',     '🏝️', 'tour_island'),
('SUMMIT_SEEKER',   'Покоритель вершин',    'Поднялся на сопку Сестра',                '⛰️', 'tour_mountain'),
('WILDLIFE_FRIEND', 'Друг природы',         'Побывал в Сафари Парке',                  '🐅', 'tour_safari'),
('OCEAN_DIVER',     'Житель глубин',        'Посетил Приморский океанариум',            '🐬', 'tour_aquarium'),
('VLADIVOSTOK_VIP', 'Знаток Владивостока',  'Прошёл пешеходную экскурсию по Владивостоку','🏙️', 'tour_vladivostok_walk'),
('LOTUS_WATCHER',   'Хранитель лотоса',     'Увидел цветение лотосов на острове Путятин','🌸', 'tour_lotus'),
('WATERFALL_CHASER','Охотник за водопадами','Посетил водопад Стеклянуха',               '💧', 'tour_waterfall'),
('EARLY_BIRD',      'Ранняя пташка',        'Забронировал тур за 7+ дней',             '🌅', 'early_booking'),
('SOCIAL_STAR',     'Социальная звезда',    'Привёл друга по реферальной ссылке',      '🌟', 'referral_used'),
('BEACH_ADDICT',    'Пляжный маньяк',       'Посетил 3 разных пляжа/бухты',            '🏖️', 'three_beaches'),
('PHOTOGRAPHER',    'Фотоохотник',          'Побывал на 5 различных турах',            '📸', 'five_tours'),
('NAVIGATOR',       'Штурман',              'Побывал на морской и наземной экскурсии', '🧭', 'sea_and_land'),
('BOTANIST',        'Ботаник',              'Посетил ботанический сад во Владивостоке','🌿', 'tour_botanical'),
('LIGHTHOUSE',      'Маяк',                 'Увидел маяк Токаревский или Лихачёва',    '🔦', 'tour_lighthouse'),
('DIEHARD_FAN',     'Преданный путешественник','Совершил 10 путешествий с Лотос-тур',  '🏆', 'ten_tours'),
('LIVADIA_PEARL',   'Жемчужина Ливадии',    'Побывал в бухте Рифовая',                 '💎', 'tour_livadia')
ON CONFLICT (code) DO NOTHING;
