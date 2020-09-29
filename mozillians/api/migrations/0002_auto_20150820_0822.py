# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='apiv2app',
            name='owner',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='apps', to='users.UserProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='apiapp',
            name='owner',
            field=models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
