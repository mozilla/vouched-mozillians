# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20160516_0814'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_spam',
            field=models.NullBooleanField(default=None, help_text='Possible spam'),
        ),
    ]
