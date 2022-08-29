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
    remind_entries = []
    for item in session.query(Reminders).filter(Reminders.remind_datetime == remind_datetime_now):
        remind_entries.append(item.remind_id)
        remind_entries.append(item.user_id)
        remind_entries.append(item.remind)
        remind_entries.append(item.remind_datetime)
        remind_entries.append(item.remind_count)
        remind_entries.append(item.remind_delay)
    return remind_entries


def get_entries_by_user_id(user_id):
    remind_entries = []
    user_reminders = []
    entry_number = 0
    for entry in session.query(Reminders).filter(Reminders.user_id == user_id):
        user_reminders.append(entry)
    for item in user_reminders:
        remind_entries.append(list())
        remind_entries[entry_number].append(entry_number+1)
        remind_entries[entry_number].append(item.remind_id)
        remind_entries[entry_number].append(item.user_id)
        remind_entries[entry_number].append(item.remind)
        remind_entries[entry_number].append(item.remind_datetime)
        remind_entries[entry_number].append(item.remind_count)
        remind_entries[entry_number].append(item.remind_delay)
        entry_number += 1
    return remind_entries


def get_numbered_remind_id_by_user_id(user_id):
    dict_number_id_reminder_id = {}
    number_id = '1'
    for entry in session.query(Reminders).filter(Reminders.user_id == user_id):
        dict_number_id_reminder_id[number_id] = entry.remind_id
        number_id = str(int(number_id) + 1)
    return dict_number_id_reminder_id


def get_reminder_entry_by_remind_id(remind_id):
    reminder_entry = session.query(Reminders).filter(Reminders.remind_id == remind_id)
    reminder_list = []
    for item in reminder_entry:
        reminder_list.append(item.remind_id)
        reminder_list.append(item.user_id)
        reminder_list.append(item.remind)
        reminder_list.append(item.remind_datetime)
        reminder_list.append(item.remind_count)
        reminder_list.append(item.remind_delay)
    return reminder_list


def update_remind_datetime_and_count_in_db(reminder):
    session.query(Reminders)\
        .filter(Reminders.remind_id == reminder.remind_id)\
        .update({'remind_datetime': reminder.remind_datetime, 'remind_count': reminder.remind_count})
    session.commit()


def update_remind_text(reminder):
    session.query(Reminders) \
        .filter(Reminders.remind_id == reminder.remind_id) \
        .update({'remind': reminder.remind})
    session.commit()


def update_remind_datetime(reminder):
    session.query(Reminders) \
        .filter(Reminders.remind_id == reminder.remind_id) \
        .update({'remind_datetime': reminder.remind_datetime})
    session.commit()


def update_remind_count(reminder):
    session.query(Reminders) \
        .filter(Reminders.remind_id == reminder.remind_id) \
        .update({'remind_count': reminder.remind_count})
    session.commit()


def update_remind_delay(reminder):
    session.query(Reminders) \
        .filter(Reminders.remind_id == reminder.remind_id) \
        .update({'remind_delay': reminder.remind_delay})
    session.commit()


def delete_remind(reminder_id):
    session.query(Reminders).filter_by(remind_id=reminder_id).delete()
    session.commit()
