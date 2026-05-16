import random
import time

otp_store = {}

def generate_otp():
    otp = random.randint(100000, 999999)
    otp_store["otp"] = otp
    otp_store["time"] = time.time()
    return otp

def verify_otp(user_otp):
    if "otp" not in otp_store:
        return False

    # OTP expires in 5 minutes
    if time.time() - otp_store["time"] > 300:
        return False

    return int(user_otp) == otp_store["otp"]
