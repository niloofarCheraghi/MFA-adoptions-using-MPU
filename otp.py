import pyotp
import json


# get the secret key from the json file
with open('secret.json', 'r') as f:
    data = json.load(f)
    SECRET_KEY = data.get('SECRET_KEY')



# check if the otp is valid
def get_otp():
    if SECRET_KEY is None:
        print('Secret key not found')
        return
    try:
        totp = pyotp.TOTP(SECRET_KEY, interval=300)
        current_totp = totp.now()
        return current_totp
    except Exception as e:
        print("Error generating OTP")

# store the secret key in json file
def store_secret_key(secret_key):
    try:
        with open('secret.json', 'w') as f:
            json.dump({'SECRET_KEY': secret_key}, f)
        print('Secret key stored successfully')
    except Exception as e:
        print('Error storing secret key')
    

if __name__ == '__main__':
    otp = get_otp()
    print(otp)
    