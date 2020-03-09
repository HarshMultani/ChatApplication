from datetime import datetime
from db import get_user, save_user, save_room,  get_room, is_room_member, \
    get_room_members, is_room_admin, update_room, remove_room_member, get_rooms_for_user, save_message, get_messages, add_room_member, get_room_by_roomname, get_all_rooms, get_all_users, save_agent
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "my secret key"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def home():
    rooms = []
    if current_user.is_authenticated:
        rooms = get_rooms_for_user(current_user.username)
    return render_template("index.html", rooms=rooms)


@app.route('/login', methods=['GET', 'POST'])
def login():

    available_rooms = []
    message = ''
    if current_user.is_authenticated:
        user = get_user(current_user.username)
        if user.is_agent:
            message=current_user.username
            return redirect(url_for('create_room', message=message))
        else:
            rooms = get_all_rooms()
            for room in rooms:
                if room['member'] == 1:
                    available_rooms.append(room['name'])
            return redirect(url_for('joining_room', available_rooms=available_rooms))

    message = 'Guest'
    if request.method=="POST":
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)
        if user and user.check_password(password_input):
            login_user(user)
            if user.is_agent:
                message=username
                return redirect(url_for('create_room', message=message))
            else:
                rooms = get_all_rooms()
                for room in rooms:
                    if room['member'] == 1:
                        available_rooms.append(room['name'])
                return redirect(url_for('joining_room', available_rooms=available_rooms))
        else:
            message = 'Failed to login'
            return render_template('login.html', message=message)

    return render_template('login.html', message=message)

#@app.route('/signup', methods=['GET', 'POST'])
#def signup():
#    if current_user.is_authenticated:
#        return redirect(url_for('home'))
#
#    message = ''
#    if request.method == 'POST':
#        username = request.form.get('username')
#        email = request.form.get('email')
#        password = request.form.get('password')
#        try:
#            save_user(username, email, password)
#            message = username
#            return redirect(url_for('login', message=message))
#        except :
#            message = "User already exists!"
#    return render_template('signup.html', message=message)

@app.route('/agent-signup', methods=['GET', 'POST'])
def agent_signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            save_agent(username, email, password)
            message = username
            return redirect(url_for('login', message=message))
        except :
            message = "User already exists!"
    return render_template('agent_signup.html', message=message)

@app.route('/user-signup', methods=['GET', 'POST'])
def user_signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            save_user(username, email, password)
            message = username
            return redirect(url_for('login', message=message))
        except :
            message = "User already exists!"
    return render_template('user_signup.html', message=message)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/create-room/', methods=['GET', 'POST'])
@login_required
def create_room():
    message = ''
    if request.method == 'POST':
        room_name = request.form.get('room_name')

        if len(room_name):# and len(usernames):
            room_id = save_room(room_name, current_user.username)
            return redirect(url_for('view_room', room_id=room_id))
        else:
            message = "Failed to create room"
    return render_template('create_room.html', message=message)

@app.route('/join-room', methods=['GET', 'POST'])
@login_required
def joining_room():
    available_rooms = []
    rooms = get_all_rooms()
    for room in rooms:
        if room['member'] == 1:
            available_rooms.append(room['name'])
    message = current_user.username
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        username = current_user.username

        if len(room_name) and len(username):
            try:

                room = get_room_by_roomname(room_name)
                room_id = room['_id']
                room_name = room['name']
                room_members = get_room_members(room_id)
                if len(room_members) == 1:
                    add_room_member(room_id, room_name, current_user.username, current_user.username, False)
                    return redirect(url_for('view_room', room_id=room_id))
                else:
                    message = "Failed to join room"

            except:
                message = "Failed to join room"

    return render_template('join_room.html', message=message, available_rooms=available_rooms)

@app.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    available_users = []
    users = get_all_users()
    for user in users:
        if len(user['room']) == 0 and user['is_agent'] == False:
            available_users.append(user['_id']) 
    if room and is_room_admin(room_id, current_user.username):

        message = ''
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            room['name'] = room_name
            update_room(room_id, room_name)

            member_to_add = request.form.get('add_member').strip()
            member_to_remove = request.form.get('remove_member').strip()
            print(member_to_remove)


            if len(member_to_add):
                if room['member'] == 2:
                    message = "Room already has 2 members - cannot add more members"
                    return render_template('edit_room.html', room=room, message=message, available_users=available_users)
                else:
                    add_room_member(room_id, room_name, member_to_add, current_user.username, False)
            if len(member_to_remove):
                print(member_to_remove)
                remove_room_member(room_id, member_to_remove)
            message = 'Room edited successfully'
        return render_template('edit_room.html', room=room, message=message, available_users=available_users)
    else:
        return "Room not found", 404


@app.route('/rooms/<room_id>/')
@login_required
def view_room(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        messages = get_messages(room_id)
        return render_template('view_room.html', username=current_user.username, room=room, room_members=room_members, messages=messages)
    else:
        return "Room not found", 404


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    save_message(data['room'], data['message'], data['username'])
    socketio.emit('receive_message', data, room=data['room'])


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])

#@socketio.on('leave_room')
#def handle_leave_room_event(data):
    #app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    #leave_room(data['room'])
    #socketio.emit('leave_room_announcement', data, room=data['room'])

@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    socketio.run(app, debug=True)