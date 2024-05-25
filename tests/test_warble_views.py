import os
from unittest import TestCase
from models import db, User, Message
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            self.client = app.test_client()

            self.testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="testuser",
                                        image_url=None)
            self.testuser_id = 8989
            self.testuser.id = self.testuser_id
            db.session.commit()

            self.testuser = User.query.get(self.testuser_id)  # Ensure user is bound to session

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_add_message(self):
        """Can user add a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)

            with app.app_context():
                message = Message.query.one()
                self.assertEqual(message.text, "Hello")

    def test_add_no_session(self):
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello world"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_message_show(self):
        with app.app_context():
            m = Message(id=1234, text='test message', user_id=self.testuser_id)
            db.session.add(m)
            db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/messages/{m.id}')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))

    def test_invalid_message_show(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/messages/123456789123456789')
            self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):
        with app.app_context():
            m = Message(id=1234, text='test message', user_id=self.testuser_id)
            db.session.add(m)
            db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            with app.app_context():
                m = Message.query.get(1234)
                self.assertIsNone(m)

    def test_unauth_message_delete(self):
        with app.app_context():
            u = User.signup(username="bad-guy", email="testing@gmail.com", password="password", image_url=None)
            u.id = 76543

            m = Message(id=1234, text='hello', user_id=self.testuser_id)
            db.session.add_all([u, m])
            db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 76543

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            with app.app_context():
                m = Message.query.get(1234)
                self.assertIsNotNone(m)

if __name__ == "__main__":
    import unittest
    unittest.main()
