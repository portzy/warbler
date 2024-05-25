"""Seed database with sample data from CSV Files."""

from csv import DictReader
from app import app, db
from models import User, Message, Follows

with app.app_context():
    db.drop_all()  
    db.create_all()

    # Open and load users from CSV file
    with open('generator/users.csv', 'r') as users:
        user_data = DictReader(users)
        db.session.bulk_insert_mappings(User, user_data)

    # Open and load messages from CSV file
    with open('generator/messages.csv', 'r') as messages:
        message_data = DictReader(messages)
        db.session.bulk_insert_mappings(Warble, message_data)

    # Open and load follows from CSV file
    with open('generator/follows.csv', 'r') as follows:
        follows_data = DictReader(follows)
        db.session.bulk_insert_mappings(Follows, follows_data)

    db.session.commit()
