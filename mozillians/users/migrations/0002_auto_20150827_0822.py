# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vouch',
            name='date',
            field=models.DateTimeField(default=None),
            preserve_default=False,
        ),
    ]
