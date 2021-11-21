from datetime import datetime
import logging
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.base import session_scope


logger = logging.getLogger(__name__)


class JiraIssue(Base):
    __tablename__ = 'JIRA_ISSUES'
    key = Column(String(32), primary_key=True, nullable=False)
    prev_progress = Column(Float, nullable=True)
    create_at = Column(DateTime, default=datetime.now)
    update_at = Column(DateTime, default=datetime.now)

    @classmethod
    def create(cls, key, prev_progress):
        base_issue = cls(key=key, prev_progress=prev_progress)
        try:
            with session_scope() as session:
                session.add(base_issue)
            return base_issue
        except IntegrityError:
            return False

    @classmethod
    def get_all(cls):
        with session_scope() as session:
            base_issues = session.query(cls).all()
        if base_issues is None:
            return None
        return base_issues

    @classmethod
    def delete_all(cls):
        with session_scope() as session:
            session.query(cls).delete()
        logger.info({'action': 'delete_all', 'status': 'delete'})

    @property
    def value(self):
        return {
            'key': self.key,
            'prev_progress': self.prev_progress,
            'prev_updated': self.update_at.strftime('%m/%d'),
        }