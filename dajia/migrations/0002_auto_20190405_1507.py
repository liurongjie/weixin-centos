# Generated by Django 2.0.9 on 2019-04-05 15:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dajia', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='production',
            old_name='introducitonpic',
            new_name='introductionpic',
        ),
        migrations.RemoveField(
            model_name='order',
            name='ordertime',
        ),
    ]
