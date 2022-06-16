from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.automap import automap_base
from configs import SQLALCHEMY_DATABASE_URI

db_engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"connect_timeout": 60})

Base = automap_base()
Base.prepare(db_engine, reflect=True)

UserProject = Base.classes.user_projects
Lesson = Base.classes.lessons

Session = sessionmaker(bind=db_engine)
db_session: Session = Session()
