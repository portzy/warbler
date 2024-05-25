"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

app.config['WTF_CSRF_ENABLED'] = False


class WarbleViewTestCase(TestCase):
    """Test views for warbles."""

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

            self.u1 = User.signup("test1", "test1@test.com", "password", None)
            self.u1_id = 778
            self.u1.id = self.u1_id
            self.u2 = User.signup("test2", "test2@test.com", "password", None)
            self.u2_id = 884
            self.u2.id = self.u2_id
            self.u3 = User.signup("test3", "test3@test.com", "password", None)
            self.u4 = User.signup("test4", "test4@test.com", "password", None)

            db.session.commit()

    def tearDown(self):
        with app.app_context():
            resp = super().tearDown()
            db.session.rollback()
            return resp

    def test_users_index(self):
        with self.client as c:
            resp = c.get('/users')

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
            self.assertIn("@test3", str(resp.data))
            self.assertIn("@test4", str(resp.data))

    def test_users_index(self):
        with self.client as c:
            resp = c.get('/users')

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
            self.assertIn("@test3", str(resp.data))
            self.assertIn("@test4", str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser", str(resp.data))

    def test_show_followers_logged_in(self):
        """Test accessing followers page while logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get(f"/users/{self.testuser.id}/followers")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Followers", str(resp.data))

    def test_show_followers_logged_out(self):
        """Test accessing followers page while logged out."""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            


    

    




    

    
