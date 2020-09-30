# Generated by Django 2.2.16 on 2020-09-30 10:55

from django.db import migrations


def remove_non_email_external_accounts(apps, schema_editor):
    ExternalAccount = apps.get_model("users", "ExternalAccount")
    ExternalAccount.objects.exclude(type="EMAIL").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0050_auto_20200929_0509'),
    ]

    operations = [
        migrations.RunPython(remove_non_email_external_accounts)
    ]
