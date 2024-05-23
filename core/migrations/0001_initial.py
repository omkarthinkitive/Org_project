# Generated by Django 5.0.6 on 2024-05-22 09:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizations', '0006_alter_organization_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='NestedOrganization',
            fields=[
                ('organization_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='organizations.organization')),
                ('parent_organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_organizations', to='core.nestedorganization')),
            ],
            options={
                'verbose_name': 'organization',
                'verbose_name_plural': 'organizations',
                'ordering': ['name'],
                'abstract': False,
            },
            bases=('organizations.organization',),
        ),
    ]