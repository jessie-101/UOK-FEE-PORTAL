from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fees', '0004_student_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='student',
            old_name='class_name',
            new_name='course',
        ),
    ]