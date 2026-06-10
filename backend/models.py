from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    ref_code = db.Column(db.String(32), unique=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    bookings = db.relationship('Booking', backref='user', lazy=True)
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    referrals_sent = db.relationship('Referral', foreign_keys='Referral.referrer_id', backref='referrer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Tour(db.Model):
    __tablename__ = 'tours'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    start_date = db.Column(db.Date)
    duration = db.Column(db.String(100))
    bookings_count = db.Column(db.Integer, default=0)
    is_archived = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='active')

    bookings = db.relationship('Booking', backref='tour', lazy=True)


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tour_id = db.Column(db.Integer, db.ForeignKey('tours.id'), nullable=False)
    status = db.Column(db.String(20), default='booked')
    created_at = db.Column(db.DateTime, default=db.func.now())

    achievements = db.relationship('UserAchievement', backref='booking', lazy=True)


class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(10), nullable=False)
    unlock_condition = db.Column(db.String(200), nullable=False)

    user_achievements = db.relationship('UserAchievement', backref='achievement', lazy=True)


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    tour_booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    unlocked_at = db.Column(db.DateTime, default=db.func.now())

    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id'),)


class Referral(db.Model):
    __tablename__ = 'referrals'
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ref_code = db.Column(db.String(32), unique=True, nullable=False)
    discount_percent = db.Column(db.Integer, default=10)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    used_at = db.Column(db.DateTime)

    referee = db.relationship('User', foreign_keys=[referee_id], backref='referral_used')
