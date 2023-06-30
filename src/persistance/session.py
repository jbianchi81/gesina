from contextlib import contextmanager

from sqlalchemy import (
    create_engine,
    MetaData,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from src import config

Base = declarative_base(metadata=MetaData(schema="gesina"))

engine = create_engine(
    f"postgresql://{config.database_user}:{config.database_password}@{config.database_host}/{config.database_name}"
)

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

@contextmanager
def get_session():
    session = Session(expire_on_commit=False, bind=engine)
    try:
        yield session
        session.commit()
        session.expunge_all()
    except Exception as e:
        session.expunge_all()
        session.rollback()
        raise e
    finally:
        session.close()


def persist(object_to_persist):
    with get_session() as session:
        session.add(object_to_persist)
