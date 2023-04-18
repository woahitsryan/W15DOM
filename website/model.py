from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import func, desc, case
from enum import Enum

db = SQLAlchemy()

class userinfo(db.Model, UserMixin):
    __tablename__ = 'userinfo'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    platforms = db.relationship('Platform', backref='userinfo', lazy=True)
    user_games = db.relationship('UserGame', backref='user', lazy=True)
    
    def has_platform(self, platform_name):
        for platform in self.platforms:
            if platform.name == platform_name:
                return True
        return False


class Platform(db.Model):
    __tablename__ = 'platform'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('userinfo.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fetched = db.Column(db.Boolean, default=False)
    connected = db.Column(db.Boolean, default=False)
    key = db.Column(db.String(100), nullable=False)
  
class RatingEnum(Enum):
    LIKE = 'like'
    DISLIKE = 'dislike'
    UNRATED = 'unrated'
  
class UserGame(db.Model):
    __tablename__ = 'user_game'
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id'), nullable=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id', ondelete='CASCADE'), nullable=True)
    playtime = db.Column(db.Integer, nullable=True)
    owned = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('userinfo.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Enum(RatingEnum), default=RatingEnum.UNRATED, nullable=False)
    
    game = db.relationship('Game', backref='usergames')

    @staticmethod
    def top_5_games(user_id):
        games = (db.session.query(Game.name, func.sum(UserGame.playtime).label('total_playtime'), 
                 func.count(case((UserGame.rating == 'like', 1), else_=None)).label('total_likes'),
                 func.count(case((UserGame.rating == 'dislike', 1), else_=None)).label('total_dislikes'))
                 .join(UserGame)
                 .filter(UserGame.user_id == user_id)
                 .group_by(Game.id)
                 .order_by(desc('total_playtime'))
                 .limit(5)
                 .all())
        return games


class Game(db.Model):
    __tablename__ = 'game'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('userinfo.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False, unique=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id', ondelete='CASCADE'), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    console = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    external_id = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    
    platform = db.relationship('Platform', backref=db.backref('games', lazy=True))

    def __repr__(self):
        return f"Game('{self.name}', '{self.platform.name if self.platform else None}', '{self.console}', '{self.completed}')"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'platform': self.platform.name if self.platform else None,
            'genre': self.genre,
            'console': self.console,
            'completed': self.completed,
            'external_id': self.external_id,
            'image_url': self.image_url
        }

    
@staticmethod
def add_game(user_id, name, platform_id, genre, console, completed, external_id):
    existing_game = Game.query.filter_by(user_id=user_id, name=name).first()
    if existing_game:
        # game with same name already exists for this user
        return False

    new_game = Game(user_id=user_id, name=name, platform_id=platform_id, genre=genre,
                    console=console, completed=completed, external_id=external_id)
    db.session.add(new_game)
    db.session.commit()  # add this line to save the new game to the database

       
