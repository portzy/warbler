import os

from flask import Flask, render_template, request, flash, redirect, session, g, abort
# from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt
from forms import UserAddForm, LoginForm, MessageForm, EditProfileForm, DirectMessageForm
from models import db, connect_db, User, Message, Likes, BlockedUsers, DirectMessage

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
# toolbar = DebugToolbarExtension(app)

connect_db(app)

with app.app_context():
    db.create_all()


##############################################################################
# User signup/login/logout


@app.before_request 
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    do_logout() #removes user from session
    flash('You have successfully loggedout.', 'success')
    return redirect('/login')


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")

@app.route('/users/<int:user_id>/likes', methods=["GET"])
def show_likes(user_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect('/')
    user = User.query.get_or_404(user_id)
    return render_template('users/likes.html', user=user, likes=user.likes)


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    if not g.user: #checks if there is no user loaded in the global g object
        flash('Unauthorized access', 'danger')
        return redirect('/login')
    
    form = EditProfileForm(obj=g.user) #pre-fill the form with the current user's data

    if form.validate_on_submit():
        if User.authenticate(username=g.user.username, password=form.password.data):
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data or "/static/images/default-pic.png"
            g.user.header_image_url = form.header_image_url.data or "/static/images/warbler-hero.jpg"
            g.user.bio = form.bio.data
            g.user.location = form.location.data
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(f'/users/{g.user.id}')
        else:
            flash('Invalid password.', 'danger')
            return redirect('/')
    return render_template('users/edit.html', form=form)




@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")

#####################################################################
## Likes routes
@app.route('/messages/<int:message_id>/like', methods=['POST'])
def add_like(message_id):
    """Toggle a liked message for the currently-logged-in user."""
    print("Success!", message_id)

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    liked_message = Message.query.get_or_404(message_id)
    if liked_message.user_id == g.user.id:
        return abort(403)

    user_likes = g.user.likes

    if liked_message in user_likes:
        g.user.likes = [like for like in user_likes if like != liked_message]
    else:
        g.user.likes.append(liked_message)

    db.session.commit()

    return redirect("/")

########### BLOCK
@app.route('/users/block/<int:user_id>', methods=['POST'])
def block_user(user_id):
    """Block a user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    blocked_user = User.query.get_or_404(user_id)
    if blocked_user == g.user:
        flash("You cannot block yourself.", "danger")
        return redirect("/")

    block = BlockedUsers(user_id=g.user.id, blocked_user_id=user_id)
    db.session.add(block)
    db.session.commit()

    flash(f"{blocked_user.username} has been blocked.", "success")
    return redirect(f"/users/{user_id}")

@app.route('/users/unblock/<int:user_id>', methods=['POST'])
def unblock_user(user_id):
    """Unblock a user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    block = BlockedUsers.query.filter_by(user_id=g.user.id, blocked_user_id=user_id).first()
    if block:
        db.session.delete(block)
        db.session.commit()
        flash("User has been unblocked.", "success")
    return redirect(f"/users/{user_id}")

###### DIRECT MESSAGES
@app.route('/dm/send/<int:user_id>', methods=["GET", "POST"])
def send_message(user_id):
    """Send a direct message to another user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    recipient = User.query.get_or_404(user_id)
    if recipient == g.user:
        flash("You cannot send a message to yourself.", "danger")
        return redirect("/")

    form = DirectMessageForm()
    if form.validate_on_submit():
        message = DirectMessage(
            sender_id=g.user.id,
            recipient_id=user_id,
            text=form.text.data
        )
        db.session.add(message)
        db.session.commit()
        flash("Message sent!", "success")
        return redirect(f"/users/{user_id}")

    return render_template('dm/send.html', form=form, recipient=recipient)

@app.route('/dm/reply/<int:user_id>', methods=["GET", "POST"])
def reply_message(user_id):
    """Reply to a direct message."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    recipient = User.query.get_or_404(user_id)
    if recipient == g.user:
        flash("You cannot reply to yourself.", "danger")
        return redirect("/")

    form = DirectMessageForm()
    if form.validate_on_submit():
        message = DirectMessage(
            sender_id=g.user.id,
            recipient_id=user_id,
            text=form.text.data
        )
        db.session.add(message)
        db.session.commit()
        flash("Reply sent!", "success")
        return redirect("/dm/inbox")

    return render_template('dm/reply.html', form=form, recipient=recipient)


@app.route('/dm/inbox')
def inbox():
    """Show inbox with direct messages."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Create an instance of DirectMessageForm
    form = DirectMessageForm()

    messages = DirectMessage.query.filter_by(recipient_id=g.user.id).order_by(DirectMessage.timestamp.desc()).all()
    return render_template('dm/inbox.html', messages=messages, form=form)  # Pass form to the template

@app.route('/dm/sent')
def sent_messages():
    """Show sent messages."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    messages = DirectMessage.query.filter_by(sender_id=g.user.id).order_by(DirectMessage.timestamp.desc()).all()
    return render_template('dm/sent.html', messages=messages)



##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:
    - anon users: no messages
    - logged in: 100 most recent messages from users followed by the logged-in user
    """
    if g.user:
        followed_user_ids = [user.id for user in g.user.following] + [g.user.id]  # List of user IDs the logged-in user is following + their own ID
        messages = Message.query.filter(Message.user_id.in_(followed_user_ids)).order_by(Message.timestamp.desc()).limit(100).all()
        return render_template('home.html', messages=messages)
    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
