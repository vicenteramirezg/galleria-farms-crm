# Generated by Django 5.1.6 on 2025-03-10 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0011_alter_contact_relationship_score_alter_profile_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
