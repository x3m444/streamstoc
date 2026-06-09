# Migration file — copy-paste in apps/stoc/migrations/

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stoc', '0001_initial'),  # Adjust if different
    ]

    operations = [
        migrations.CreateModel(
            name='UserPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_nava', models.IntegerField(default=978, verbose_name='Navă implicită')),
                ('default_tragator', models.CharField(default='COSTEL', max_length=100, verbose_name='Tractator implicit')),
                ('default_data', models.DateField(auto_now=True, verbose_name='Data actualizată')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='stoc.stocuser')),
            ],
            options={
                'verbose_name': 'Preferințe utilizator',
                'verbose_name_plural': 'Preferințe utilizatori',
                'db_table': 'stoc_user_preferences',
            },
        ),
    ]
