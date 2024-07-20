from config import config


def otp_template(otp: str):
    template = f"""
    Your OTP for password reset is {otp} and it's valid for {config['otp_time']} minutes.
    """
    return template


def email_verification_template(url: str):
    template = f"""
    Please verify your account. Click <a href="{url}" target="_blank">here</>.
    """
    return template
