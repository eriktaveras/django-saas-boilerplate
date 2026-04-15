# Generated to replace plaintext api_key with hashed storage.
#
# Existing plaintext keys are dropped (users must regenerate). This is
# intentional: those keys were stored unhashed and are considered exposed.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_alter_usersettings_api_key'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersettings',
            name='api_key',
        ),
        migrations.AddField(
            model_name='usersettings',
            name='api_key_hash',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='usersettings',
            name='api_key_prefix',
            field=models.CharField(blank=True, default='', max_length=12),
        ),
    ]
