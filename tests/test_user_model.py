import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows
from app import app

os.environ['DATABASE_URL'] = "postgresql:///messager-test"

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            u1 = User.signup("test1", "email1@email.com", "password", None)
            uid1 = 1111
            u1.id = uid1

            u2 = User.signup("test2", "email2@email.com", "password", None)
            uid2 = 2222
            u2.id = uid2

            db.session.commit()

            self.u1 = User.query.get(uid1)
            self.uid1 = uid1

            self.u2 = User.query.get(uid2)
            self.uid2 = uid2

            self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""
        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )
            db.session.add(u)
            db.session.commit()

            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)

    def test_user_repr(self):
        """Test the __repr__ method returns the expected string."""
        with app.app_context():
            u = User(username="testrepr", email="test@repr.com", password="password")
            db.session.add(u)
            db.session.commit()
            repr_str = f"<User #{u.id}: testrepr, test@repr.com>"
            self.assertEqual(repr(u), repr_str)

    
    def test_user_follows(self):
        """Tests if user1 is correctly identified as following user2."""
        with app.app_context():
            u1 = User.query.get(self.uid1)
            u2 = User.query.get(self.uid2)
            u1.following.append(u2)
            db.session.commit()

            self.assertEqual(len(u2.following), 0)
            self.assertEqual(len(u2.followers), 1)
            self.assertEqual(len(u1.followers), 0)
            self.assertEqual(len(u1.following), 1)

            self.assertEqual(u2.followers[0].id, u1.id)
            self.assertEqual(u1.following[0].id, u2.id)

    def test_is_following(self):
        with app.app_context():
            u1 = User.query.get(self.uid1)
            u2 = User.query.get(self.uid2)
            u1.following.append(u2)
            db.session.commit()

            self.assertTrue(u1.is_following(u2))
            self.assertFalse(u2.is_following(u1))

    def test_is_followed_by(self):
        """Tests if user1 is correctly identified as being followed by user2."""
        with app.app_context():
            u1 = User.query.get(self.uid1)
            u2 = User.query.get(self.uid2)
            u1.following.append(u2)
            db.session.commit()

            self.assertTrue(u2.is_followed_by(u1))
            self.assertFalse(u1.is_followed_by(u2))

    def test_valid_signup(self):
        """Tests if a new user can be created with valid credentials."""
        with app.app_context():
            u_test = User.signup("testtesttest", "testtest@test.com", "password", None)
            uid = 99999
            u_test.id = uid
            db.session.commit()

            u_test = User.query.get(uid)
            self.assertIsNotNone(u_test)
            self.assertEqual(u_test.username, "testtesttest")
            self.assertEqual(u_test.email, "testtest@test.com")
            self.assertNotEqual(u_test.password, "password")
            # Bcrypt strings should start with $2b$
            self.assertTrue(u_test.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        with app.app_context():
            invalid = User.signup(None, "test@test.com", "password", None)
            uid = 123456789
            invalid.id = uid
            with self.assertRaises(exc.IntegrityError):
                db.session.commit()

    def test_invalid_email_signup(self):
        with app.app_context():
            invalid = User.signup("testtest", None, "password", None)
            uid = 123789
            invalid.id = uid
            with self.assertRaises(exc.IntegrityError):
                db.session.commit()

    def test_invalid_password_signup(self):
        with app.app_context():
            with self.assertRaises(ValueError):
                User.signup("testtest", "email@email.com", "", None)

            with self.assertRaises(ValueError):
                User.signup("testtest", "email@email.com", None, None)


    def test_valid_authentication(self):
        with app.app_context():
            u1 = User.query.get(self.uid1)
            u = User.authenticate(u1.username, "password")
            self.assertIsNotNone(u)
            self.assertEqual(u.id, self.uid1)

    def test_invalid_username(self):
        with app.app_context():
            self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        with app.app_context():
            u1 = User.query.get(self.uid1)
            self.assertFalse(User.authenticate(u1.username, "badpassword"))
