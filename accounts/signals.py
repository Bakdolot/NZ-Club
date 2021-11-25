from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from .utils import telegram_bot_sendtext


@receiver(post_save, sender=Notification)
def create_profile(sender, instance, created, **kwargs):
    if instance.type == '1':
        telegram_bot_sendtext(f'Пользователь {instance.user} вывел счет')
    elif instance.type == '2':
        telegram_bot_sendtext(f'Пользователь {instance.user} пополнил счет')
