# Generated by Django 3.2.20 on 2023-08-10 10:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0073_notifications_queued"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationrecipient",
            name="email_scheduled",
            field=models.BooleanField(
                default=False,
                help_text="If True, then the notification has been scheduled to be sent by email to the recipient email.",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="email_notification_frequency",
            field=models.TextField(
                choices=[
                    ("instant", "instant"),
                    ("daily", "daily"),
                    ("weekly", "weekly"),
                    ("never", "never"),
                ],
                default="instant",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="last_notifications_email_sent_at",
            field=models.DateTimeField(
                default=None,
                help_text="The last time an email notification was sent to the user.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="timezone",
            field=models.CharField(
                help_text="The user timezone to use for dates and times.",
                max_length=255,
                null=True,
            ),
        ),
    ]