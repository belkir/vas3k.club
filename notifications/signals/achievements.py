from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import loader
from django_q.tasks import async_task

from bot.common import send_telegram_message, Chat, render_html_message
from notifications.email.sender import send_club_email
from users.models.achievements import UserAchievement


@receiver(post_save, sender=UserAchievement)
def create_or_update_achievement(sender, instance, created, **kwargs):
    if not created:
        return  # skip updates

    async_task(async_create_or_update_achievement, instance)


def async_create_or_update_achievement(user_achievement: UserAchievement):
    user = user_achievement.user
    achievement = user_achievement.achievement

    # telegram
    if user.is_club_member and user.telegram_id:
        send_telegram_message(
            chat=Chat(id=user.telegram_id),
            text=render_html_message("achievement.html", user=user, achievement=achievement),
        )

    # emails
    if not user.is_email_unsubscribed:
        email_template = loader.get_template("emails/achievement.html")
        send_club_email(
            recipient=user.email,
            subject=f"🎖 Вас наградили бейджиком «{achievement.name}»",
            html=email_template.render({"user": user, "achievement": achievement}),
            tags=["achievement"]
        )
