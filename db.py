import sqlalchemy
from token_and_db_pass import db_pass
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_pass}@localhost:5432/telegram-bot-reminders')

connection = engine.connect()

Base = declarative_base()

Base.metadata.create_all(engine)


class Reminders(Base):
    __tablename__ = 'reminders'

    remind_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    remind = Column(String(1024))
    remind_datetime = Column(DateTime)
    remind_count = Column(Integer)
    remind_delay = Column(String(16))


Session = sessionmaker(bind=engine)

session = Session()


def add_new_remind_in_db(new_remind):
    new_remind = Reminders(user_id=new_remind.user_id, remind=new_remind.remind,
                           remind_datetime=new_remind.remind_datetime, remind_count=new_remind.remind_count,
                           remind_delay=new_remind.remind_delay)
    session.add(new_remind)
    session.commit()


def get_reminders_datetime():
    reminders_datetime_list = []
    for item in session.query(Reminders):
        reminders_datetime_list.append(item.remind_datetime)
    return reminders_datetime_list


def get_entries_by_datetime(remind_datetime_now):
    remind_entry = []
    for item in session.query(Reminders).filter(Reminders.remind_datetime == remind_datetime_now):
        remind_entry.append(item.remind_id)
        remind_entry.append(item.user_id)
        remind_entry.append(item.remind)
        remind_entry.append(item.remind_datetime)
    return remind_entry


def delete_remind(reminder_id):
    session.query(Reminders).filter_by(remind_id=reminder_id).delete()
    session.commit()


delete_remind(2)
