from django.conf import settings
from django.core.mail import send_mail


def send_confirmation_email(email, confirmation_code):
    """Отправляет email с кодом подтверждения пользователю."""
    subject = 'Ваш код подтверждения для Foodgram'
    message = (
        f'Спасибо за регистрацию! Ваш код подтверждения: {confirmation_code}'
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])