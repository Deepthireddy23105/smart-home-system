import threading
import time

class GuestModeManager:
    def __init__(self):
        self.guest_mode_active = False
        self.guest_mode_duration = 0

    def is_guest_mode_active(self):
        return self.guest_mode_active

    def enable_guest_mode(self, duration_minutes):
        self.guest_mode_duration = duration_minutes * 60
        self.guest_mode_active = True
        threading.Thread(target=self.disable_guest_mode_after_duration).start()

    def disable_guest_mode_after_duration(self):
        time.sleep(self.guest_mode_duration)
        self.guest_mode_active = False

    def generate_otp(self):
        # Simple OTP generation for existing guest mode
        import random
        return str(random.randint(1000, 9999))

# Global instance
guest_manager = GuestModeManager()

# Flask app for web interface
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/guest_mode', methods=['GET', 'POST'])
def guest_mode():
    if request.method == 'POST':
        duration = request.form['duration']
        if duration == '30 minutes':
            duration_minutes = 30
        elif duration == '2 hours':
            duration_minutes = 120
        elif duration == '1 day':
            duration_minutes = 1440
        guest_manager.enable_guest_mode(duration_minutes)
        return redirect(url_for('success'))
    return render_template('guest_mode.html')

@app.route('/enable_guest')
def enable_guest():
    duration = request.args.get('duration')
    if duration:
        duration_minutes = int(duration)
        guest_manager.enable_guest_mode(duration_minutes)
        return f'Guest mode enabled for {duration_minutes} minutes!'
    return 'Invalid request'

if __name__ == '__main__':
    app.run(debug=True)