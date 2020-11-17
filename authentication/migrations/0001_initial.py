# Generated by Django 3.1.2 on 2020-11-04 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserAuthentication',
            fields=[
                ('auth_id', models.CharField(editable=False,
                                             max_length=300, primary_key=True, serialize=False)),
                ('auth_token', models.CharField(blank=True, max_length=300, null=True)),
                ('refresh_token', models.CharField(blank=True, max_length=300, null=True)),
                ('curate_nd_token', models.CharField(blank=True, max_length=300, null=True)),
                ('figshare_token', models.CharField(blank=True, max_length=300, null=True)),
                ('github_token', models.CharField(blank=True, max_length=300, null=True)),
                ('gitlab_token', models.CharField(blank=True, max_length=300, null=True)),
                ('osf_token', models.CharField(blank=True, max_length=300, null=True)),
                ('zenodo_token', models.CharField(blank=True, max_length=300, null=True)),
            ],
            options={
                'verbose_name_plural': 'UserAuthentication',
                'db_table': 'user_authentication',
            },
        ),
    ]
