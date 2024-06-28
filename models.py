from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped
from typing import List
from datetime import datetime

db = SQLAlchemy()


# Why the usage of `id` is allowable: https://stackoverflow.com/a/76108267
class User(db.Model, UserMixin):
    id: Mapped[int] = db.mapped_column(primary_key=True)
    username: Mapped[str] = db.mapped_column(unique=True)
    password: Mapped[str]

    solve: Mapped[List["Solve"]] = db.relationship(back_populates="user")

    def is_active(self):
        return True

    def __repr__(self):
        return f"<User '{self.id}', '{self.username}'>"

    def get_id(self):
        return self.id


class Solve(db.Model):
    id: Mapped[int] = db.mapped_column(primary_key=True)
    user_id: Mapped[int] = db.mapped_column(db.ForeignKey("user.id"))
    challenge_id: Mapped[str]
    time: Mapped[datetime] = db.mapped_column(
        default=datetime.now
    )  # Who cares about UTC, this isn't a global CTF

    user: Mapped["User"] = db.relationship(back_populates="solve")

    def __repr__(self):
        return f"<Solve user={self.user.username} challenge_id={self.challenge_id} time={self.time}>"
