import datetime
import sqlalchemy

from .db_session import SqlAlchemyBase


class Friendship(SqlAlchemyBase):
    __tablename__ = 'friendships'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    friend_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    __table_args__ = (
        sqlalchemy.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),
    )
