# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_userprofile_is_spam'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbuseReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'', max_length=30, choices=[(b'spam', b'Spam profile'), (b'inappropriate', b'Inappropriate content')])),
                ('is_akismet', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('profile', models.ForeignKey(on_delete=models.CASCADE, related_name='abuses', to='users.UserProfile')),
                ('reporter', models.ForeignKey(on_delete=models.CASCADE, related_name='abuses_reported', to='users.UserProfile', null=True)),
            ],
        ),
    ]
