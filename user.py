from werkzeug.security import check_password_hash

class User:
    
    def __init__(self, username, email, password, room, is_agent):
        self.username = username
        self.email = email
        self.password = password
        self.room = room
        self.is_agent = is_agent

    @staticmethod
    def is_authenticated(self):
        return True
    
    @staticmethod
    def is_active(self):
        return True

    @staticmethod
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    def check_password(self, password_input):
        return check_password_hash(self.password, password_input)



