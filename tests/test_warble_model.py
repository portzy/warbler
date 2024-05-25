import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Likes
from app import app

os.environ['DATABASE_URL'] = "postgresql:///messager-test"

class MessageModelTestCase(TestCase):
    """Test Warble model."""

    def setUp(self):
        """Create test client and add sample data."""
        with app.app_context():
            db.drop_all()
            db.engine.execute("DROP TABLE IF EXISTS messages CASCADE")
            db.engine.execute("DROP TABLE IF EXISTS users CASCADE")
            db.create_all()

            self.uid = 94566
            self.user = User.signup("testing", "testing@test.com", "password", None)
            self.user.id = self.uid

            db.session.commit()
            self.client = app.test_client()


    def tearDown(self):
        with app.app_context():
            db.session.rollback()

    def test_message_model(self):
        """Test if the basic model functionality works."""
        with app.app_context():
            user = User.query.get(self.uid)
            m = Message(text='hello world!', user_id=self.uid)
            db.session.add(m)
            db.session.commit()
            self.assertEqual(len(user.messages), 1)
            self.assertEqual(user.messages[0].text, 'hello world!')

    def test_message_repr(self):
        """Test the __repr__ method of the Warble model."""
        with app.app_context():
            m = Message(text='hello world!', user_id=self.uid)
            db.session.add(m)
            db.session.commit()
            repr_str = f"<Warble #{m.id}: hello world!>"
            self.assertEqual(repr(m), repr_str)

    def test_message_likes(self):
        """Test the message likes relationship."""
        with app.app_context():
            m1 = Message(text='hey', user_id=self.uid)
            m2 = Message(text='bye', user_id=self.uid)
            user2 = User.signup("testuser", "test@email.com", "password", None)
            uid2 = 123
            user2.id = uid2
            db.session.add_all([m1, m2, user2])
            db.session.commit()

            user2.likes.append(m1)
            db.session.commit()

            l = Likes.query.filter(Likes.user_id == uid2).all()
            self.assertEqual(len(l), 1)
            self.assertEqual(l[0].message_id, m1.id)

    def test_message_creation(self):
        """Test creating a message with valid data."""
        with app.app_context():
            user = User.query.get(self.uid)
            m = Message(text="Hello, Warbler!", user_id=user.id)
            db.session.add(m)
            db.session.commit()

            self.assertEqual(len(user.messages), 1)
            self.assertEqual(user.messages[0].text, "Hello, Warbler!")

    def test_invalid_message_creation(self):
        """Test creating a message with missing required fields."""
        with app.app_context():
            m = Message(text=None, user_id=self.uid) 
            db.session.add(m)
            with self.assertRaises(exc.IntegrityError):
                db.session.commit()
