# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funfacts', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='funfact',
            options={'ordering': ['-created']},
        ),
        migrations.AlterField(
            model_name='funfact',
            name='number',
            field=models.TextField(default=b'', max_length=1000, blank=True),
        ),
    ]
