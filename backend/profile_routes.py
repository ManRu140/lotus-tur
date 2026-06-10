import secrets
import string
from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request, session
from models import db, User, Achievement, UserAchievement, Referral, Booking, Tour

profile_bp = Blueprint('profile', __name__)


ACHIEVEMENT_TOUR_MAP = {
    'tour_sea_cruise':       'Морская прогулка на катере',
    'tour_island':           ['Остров Аскольд', 'остров Путятин'],
    'tour_mountain':         'Сопка Сестра',
    'tour_safari':           'Сафари Парк',
    'tour_aquarium':         'Приморский ОКЕАНАРИУМ',
    'tour_vladivostok_walk': 'Знакомство с Владивостоком',
    'tour_lotus':            'ЦВЕТЕНИЕ ЛОТОСОВ',
    'tour_waterfall':        'Водопад Стеклянуха',
    'tour_botanical':        'Бот.сад',
    'tour_lighthouse':       ['Токаревский маяк', 'Маяк Лихачёва'],
    'tour_livadia':          'Рифовая',
}


def generate_ref_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(12))
        if not Referral.query.filter_by(ref_code=code).first():
            return code


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def check_and_unlock_achievements(user_id, booking_id=None):
    user = User.query.get(user_id)
    if not user:
        return []

    all_achievements = Achievement.query.all()
    unlocked_codes = {ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=user_id).all()}
    completed_bookings = Booking.query.filter_by(user_id=user_id, status='completed').all()
    all_bookings = Booking.query.filter_by(user_id=user_id).all()
    newly_unlocked = []

    def unlock(ach):
        if ach.id not in unlocked_codes:
            ua = UserAchievement(
                user_id=user_id,
                achievement_id=ach.id,
                tour_booking_id=booking_id
            )
            db.session.add(ua)
            unlocked_codes.add(ach.id)
            newly_unlocked.append(ach.code)

    for ach in all_achievements:
        cond = ach.unlock_condition

        if cond == 'first_booking' and len(all_bookings) >= 1:
            unlock(ach)

        elif cond == 'five_tours' and len(completed_bookings) >= 5:
            unlock(ach)

        elif cond == 'ten_tours' and len(completed_bookings) >= 10:
            unlock(ach)

        elif cond == 'three_beaches':
            beach_keywords = ['Триозерье', 'Окуневая', 'Рифовая', 'Стеклянная', 'Лашкевича']
            visited = set()
            for b in completed_bookings:
                for kw in beach_keywords:
                    if b.tour and kw.lower() in b.tour.name.lower():
                        visited.add(kw)
            if len(visited) >= 3:
                unlock(ach)

        elif cond == 'sea_and_land':
            has_sea = any(b.tour and 'катер' in b.tour.name.lower() for b in completed_bookings)
            has_land = any(b.tour and ('пешеходная' in b.tour.name.lower() or 'сопка' in b.tour.name.lower()) for b in completed_bookings)
            if has_sea and has_land:
                unlock(ach)

        elif cond == 'referral_used':
            ref = Referral.query.filter_by(referrer_id=user_id, used=True).first()
            if ref:
                unlock(ach)

        elif cond == 'early_booking' and booking_id:
            b = Booking.query.get(booking_id)
            if b and b.tour and b.created_at:
                delta = (b.tour.start_date - b.created_at.date()).days
                if delta >= 7:
                    unlock(ach)

        elif cond in ACHIEVEMENT_TOUR_MAP:
            keywords = ACHIEVEMENT_TOUR_MAP[cond]
            if isinstance(keywords, str):
                keywords = [keywords]
            for b in completed_bookings:
                if b.tour and any(kw.lower() in b.tour.name.lower() for kw in keywords):
                    unlock(ach)
                    break

    db.session.commit()
    return newly_unlocked


@profile_bp.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if not user.ref_code:
        user.ref_code = generate_ref_code()
        ref = Referral(referrer_id=user_id, ref_code=user.ref_code)
        db.session.add(ref)
        db.session.commit()

    all_achievements = Achievement.query.order_by(Achievement.id).all()
    user_ach_map = {
        ua.achievement_id: ua
        for ua in UserAchievement.query.filter_by(user_id=user_id).all()
    }

    achievements_data = []
    for ach in all_achievements:
        ua = user_ach_map.get(ach.id)
        achievements_data.append({
            'id': ach.id,
            'code': ach.code,
            'name': ach.name,
            'description': ach.description,
            'icon': ach.icon,
            'unlocked': ua is not None,
            'unlocked_at': ua.unlocked_at.isoformat() if ua else None,
            'tour_booking_id': ua.tour_booking_id if ua else None,
        })

    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()

    def booking_achievements(booking_id):
        uas = UserAchievement.query.filter_by(user_id=user_id, tour_booking_id=booking_id).all()
        result = []
        for ua in uas:
            ach = Achievement.query.get(ua.achievement_id)
            if ach:
                result.append({'icon': ach.icon, 'name': ach.name, 'code': ach.code})
        return result

    booked = []
    in_progress = []
    completed = []

    for b in bookings:
        item = {
            'id': b.id,
            'tour_id': b.tour_id,
            'tour_name': b.tour.name if b.tour else '',
            'tour_date': b.tour.start_date.isoformat() if b.tour and b.tour.start_date else None,
            'price': b.tour.price if b.tour else None,
            'status': b.status,
            'achievements': booking_achievements(b.id),
        }
        if b.status == 'booked':
            booked.append(item)
        elif b.status == 'in_progress':
            in_progress.append(item)
        elif b.status == 'completed':
            completed.append(item)

    referral_link = f"{request.host_url}?ref={user.ref_code}"

    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'ref_code': user.ref_code,
        'referral_link': referral_link,
        'achievements': achievements_data,
        'bookings': {
            'booked': booked,
            'in_progress': in_progress,
            'completed': completed,
        }
    })


@profile_bp.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'success': True})


@profile_bp.route('/api/tours', methods=['GET'])
def get_tours():
    archived = request.args.get('archived', 'false').lower() == 'true'
    tours = Tour.query.filter_by(is_archived=archived).order_by(Tour.bookings_count.desc()).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'description': t.description,
        'price': t.price,
        'start_date': t.start_date.isoformat() if t.start_date else None,
        'bookings_count': t.bookings_count,
        'is_archived': t.is_archived,
        'status': t.status,
    } for t in tours])


@profile_bp.route('/api/tours/popular', methods=['GET'])
def get_popular_tours():
    limit = int(request.args.get('limit', 6))
    tours = (
        Tour.query
        .filter_by(is_archived=False)
        .order_by(Tour.bookings_count.desc())
        .limit(limit)
        .all()
    )
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'description': t.description,
        'price': t.price,
        'start_date': t.start_date.isoformat() if t.start_date else None,
        'bookings_count': t.bookings_count,
    } for t in tours])


@profile_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    ref_code = data.get('ref')
    user = User(
        name=data.get('name', '').strip(),
        email=data.get('email', '').strip().lower(),
    )
    user.set_password(data.get('password', ''))
    db.session.add(user)
    db.session.flush()

    user.ref_code = generate_ref_code()
    new_ref = Referral(referrer_id=user.id, ref_code=user.ref_code)
    db.session.add(new_ref)

    discount = 0
    if ref_code:
        existing_ref = Referral.query.filter_by(ref_code=ref_code, used=False).first()
        if existing_ref and existing_ref.referrer_id != user.id:
            existing_ref.used = True
            existing_ref.referee_id = user.id
            existing_ref.used_at = datetime.utcnow()
            discount = existing_ref.discount_percent
            db.session.flush()
            referrer = User.query.get(existing_ref.referrer_id)
            if referrer:
                check_and_unlock_achievements(referrer.id)

    db.session.commit()
    return jsonify({'success': True, 'discount': discount})


@profile_bp.route('/api/bookings/<int:booking_id>/complete', methods=['POST'])
@login_required
def complete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    booking.status = 'completed'
    if booking.tour:
        booking.tour.bookings_count = (booking.tour.bookings_count or 0) + 1
    db.session.commit()
    newly = check_and_unlock_achievements(session['user_id'], booking_id)
    return jsonify({'success': True, 'new_achievements': newly})
