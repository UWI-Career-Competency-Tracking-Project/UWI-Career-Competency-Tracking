import os, tempfile, pytest, logging, unittest
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from App.main import create_app
from App.database import db, create_db
from App.models import User
from App.controllers import (
    create_user,
    get_all_users_json,
    login,
    get_user,
    get_user_by_username,
    update_user
)


LOGGER = logging.getLogger(__name__)

'''
   Unit Tests
'''
class UserUnitTests(unittest.TestCase):

    def test_new_user(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user = User(username=f"bob_{timestamp}", email=f"bob_{timestamp}@example.com", password="bobpass")
        assert user.username == f"bob_{timestamp}"

    # pure function no side effects or integrations called
    def test_get_json(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user = User(username=f"bob_{timestamp}", email=f"bob_{timestamp}@example.com", password="bobpass")
        user_json = user.get_json()
        assert user_json["username"] == f"bob_{timestamp}"
        assert user_json["email"] == f"bob_{timestamp}@example.com"
        assert "password" not in user_json
    
    def test_hashed_password(self):
        password = "mypass"
        hashed = generate_password_hash(password, method='sha256')
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user = User(username=f"bob_{timestamp}", email=f"bob_{timestamp}@example.com", password=password)
        assert user.password_hash != password

    def test_check_password(self):
        password = "mypass"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user = User(username=f"bob_{timestamp}", email=f"bob_{timestamp}@example.com", password=password)
        assert user.check_password(password)

'''
    Integration Tests
'''

# This fixture creates an empty database for the test and deletes it after the test
# scope="class" would execute the fixture once and resued for all methods in the class
@pytest.fixture(autouse=True, scope="module")
def empty_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Push application context to allow controller functions to work
        ctx = app.app_context()
        ctx.push()
        
        # Return test client
        yield app.test_client()
        
        # Clean up
        ctx.pop()
        db.session.remove()
        db.drop_all()

def test_authenticate():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    username = f"bob_{timestamp}"
    email = f"bob_{timestamp}@example.com"
    user = create_user(username, "bobpass", email)
    assert login(username, "bobpass") != None

class UsersIntegrationTests(unittest.TestCase):

    def test_create_user(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"rick_{timestamp}"
        email = f"rick_{timestamp}@example.com"
        user = create_user(username, "bobpass", email)
        assert user.username == username

    def test_get_all_users_json(self):
        users_json = get_all_users_json()
        # Just check that we get a list of users
        assert isinstance(users_json, list)
        # Create a user first to ensure we have at least one
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"json_test_{timestamp}"
        email = f"json_{timestamp}@example.com"
        create_user(username, "testpass", email)
        
        # Get users again and check
        users_json = get_all_users_json()
        assert len(users_json) > 0
        # Check that each user has the correct properties
        for user in users_json:
            assert "username" in user
            assert "email" in user
            assert "id" in user

    # Tests data changes in the database
    def test_update_user(self):
        # First create a user to update
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        username = f"update_test_{timestamp}"
        new_username = f"updated_{timestamp}"
        email = f"update_{timestamp}@example.com"
        user = create_user(username, "testpass", email)
        
        # Update the user
        update_user(user.id, new_username)
        updated_user = get_user(user.id)
        assert updated_user.username == new_username
        

