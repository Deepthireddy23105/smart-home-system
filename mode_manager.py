class ModeManager:
    def __init__(self, db):
        self.mode = 'Home'

    def get_current_mode(self):
        return self.mode

    def set_mode(self, mode):
        self.mode = mode

    def should_provide_voice_feedback(self):
        return True

    def is_guest_allowed(self):
        return True