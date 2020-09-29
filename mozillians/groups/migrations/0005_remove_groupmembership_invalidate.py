# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0004_auto_20151028_0632'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupmembership',
            name='invalidate',
        ),
    ]
