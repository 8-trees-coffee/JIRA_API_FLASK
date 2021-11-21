from datetime import datetime
import logging
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.base import session_scope


logger = logging.getLogger(__name__)


class Account(Base):
    __tablename__ = 'ACCOUNTS'
    id = Column(String(16), primary_key=True, nullable=False)
    pw = Column(String(128))
    create_at = Column(DateTime, default=datetime.now)
    update_at = Column(DateTime, default=datetime.now)

    @classmethod
    def create(cls, id, pw):
        account = cls(id=id, pw=pw)
        try:
            with session_scope() as session:
                session.add(account)
            return account
        except IntegrityError:
            return False

    @classmethod
    def get(cls, id):
        with session_scope() as session:
            account = session.query(cls).filter(cls.id == id).first()
        if account is None:
            return None
        return account

    def save(self):
        with session_scope() as session:
            session.add(self)