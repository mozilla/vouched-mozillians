# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmembership',
            name='userprofile',
            field=models.ForeignKey(on_delete=models.CASCADE, to='users.UserProfile'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='groupmembership',
            unique_together=set([('userprofile', 'group')]),
        ),
        migrations.AddField(
            model_name='groupalias',
            name='alias',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='aliases', to='groups.Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='group',
            name='curator',
            field=models.ForeignKey(on_delete=models.SET_NULL, related_name='groups_curated', blank=True, to='users.UserProfile', null=True),
            preserve_default=True,
        ),
    ]
