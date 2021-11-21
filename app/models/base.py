from contextlib import contextmanager
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
import threading

import settings


logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine(f'sqlite:///{settings.db_name}?check_same_thread=False')
Session = scoped_session(sessionmaker(bind=engine))
lock = threading.Lock()

# ref: https://docs.sqlalchemy.org/en/13/orm/session_basics.html#what-does-the-session-do
@contextmanager
def session_scope():
    session = Session()
    session.expire_on_commit = False
    try:
        lock.acquire()
        yield session
        session.commit()
    except Exception as e:
        logger.error({'action': 'session_scope', 'error': e})
        session.rollback()
        raise
    finally:
        session.expire_on_commit = True
        lock.release()

def init_db():
    import app.models.issues
    import app.models.accout
    Base.metadata.create_all(bind=engine)


