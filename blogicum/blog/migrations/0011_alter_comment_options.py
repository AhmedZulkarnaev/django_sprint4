# Generated by Django 3.2.16 on 2023-11-02 19:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_post_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('created_at',), 'verbose_name': 'Комментарий', 'verbose_name_plural': 'Комментарии'},
        ),
    ]
