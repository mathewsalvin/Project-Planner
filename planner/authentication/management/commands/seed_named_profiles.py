import secrets
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from authentication.models import RoleChoices, TechChoices


NAMED_PROFILES = {
    'coordinator01': ('maya.patel', 'Maya', 'Patel', RoleChoices.COORDINATOR, None),
    'coordinator02': ('noah.williams', 'Noah', 'Williams', RoleChoices.COORDINATOR, None),
    'coordinator03': ('aisha.khan', 'Aisha', 'Khan', RoleChoices.COORDINATOR, None),
    'backend01': ('arjun.mehta', 'Arjun', 'Mehta', RoleChoices.DEVELOPER, TechChoices.BACKEND),
    'backend02': ('priya.nair', 'Priya', 'Nair', RoleChoices.DEVELOPER, TechChoices.BACKEND),
    'backend03': ('ethan.chen', 'Ethan', 'Chen', RoleChoices.DEVELOPER, TechChoices.BACKEND),
    'frontend01': ('sofia.garcia', 'Sofia', 'Garcia', RoleChoices.DEVELOPER, TechChoices.FRONTEND),
    'frontend02': ('liam.johnson', 'Liam', 'Johnson', RoleChoices.DEVELOPER, TechChoices.FRONTEND),
    'frontend03': ('ananya.rao', 'Ananya', 'Rao', RoleChoices.DEVELOPER, TechChoices.FRONTEND),
    'fullstack01': ('daniel.kim', 'Daniel', 'Kim', RoleChoices.DEVELOPER, TechChoices.FULLSTACK),
    'fullstack02': ('zara.ahmed', 'Zara', 'Ahmed', RoleChoices.DEVELOPER, TechChoices.FULLSTACK),
    'fullstack03': ('oliver.brown', 'Oliver', 'Brown', RoleChoices.DEVELOPER, TechChoices.FULLSTACK),
    'uiux01': ('isabella.martin', 'Isabella', 'Martin', RoleChoices.DEVELOPER, TechChoices.UI_UX),
    'uiux02': ('kavya.iyer', 'Kavya', 'Iyer', RoleChoices.DEVELOPER, TechChoices.UI_UX),
    'uiux03': ('mateo.silva', 'Mateo', 'Silva', RoleChoices.DEVELOPER, TechChoices.UI_UX),
}

TESTER_PROFILES = (
    ('fatima.ali', 'Fatima', 'Ali'),
    ('ryan.cooper', 'Ryan', 'Cooper'),
    ('meera.shah', 'Meera', 'Shah'),
)


class Command(BaseCommand):
    help = 'Rename demo profiles, create tester profiles, and update local credentials.'

    def handle(self, *args, **options):
        user_model = get_user_model()
        credentials_path = Path(__file__).resolve().parents[2] / 'credentials.txt'

        if not credentials_path.exists():
            raise CommandError(f'Credentials file not found: {credentials_path}')

        records = {}
        for block in credentials_path.read_text(encoding='utf-8').strip().split('\n\n'):
            record = {}
            for line in block.splitlines():
                key, separator, value = line.partition(': ')
                if not separator:
                    raise CommandError('Credentials file contains a malformed record.')
                record[key] = value
            username = record.get('Username')
            if not username or not record.get('Password'):
                raise CommandError('Credentials file must include each username and password.')
            records[username] = record

        missing_records = set(NAMED_PROFILES) - records.keys()
        if missing_records:
            raise CommandError(
                'Missing credential records for: ' + ', '.join(sorted(missing_records))
            )

        existing_profiles = {
            profile.username: profile
            for profile in user_model.objects.filter(
                username__in=NAMED_PROFILES,
                is_superuser=False,
            )
        }
        missing_profiles = set(NAMED_PROFILES) - existing_profiles.keys()
        if missing_profiles:
            raise CommandError(
                'Missing non-admin profiles for: ' + ', '.join(sorted(missing_profiles))
            )

        target_usernames = {
            details[0] for details in NAMED_PROFILES.values()
        } | {username for username, _, _ in TESTER_PROFILES}
        current_ids = {profile.pk for profile in existing_profiles.values()}
        conflicts = user_model.objects.filter(username__in=target_usernames).exclude(
            pk__in=current_ids
        )
        if conflicts.exists():
            raise CommandError(
                'A target username is already in use: '
                + ', '.join(conflicts.values_list('username', flat=True))
            )

        credential_records = []
        with transaction.atomic():
            for old_username, (username, first_name, last_name, role, tech) in NAMED_PROFILES.items():
                profile = existing_profiles[old_username]
                profile.username = username
                profile.first_name = first_name
                profile.last_name = last_name
                profile.role = role
                profile.tech = tech
                profile.save(update_fields=['username', 'first_name', 'last_name', 'role', 'tech'])

                record = records.pop(old_username)
                record.update({
                    'Username': username,
                    'Name': f'{first_name} {last_name}',
                    'Role': role,
                    'Tech': tech or 'N/A',
                })
                credential_records.append(record)

            for username, first_name, last_name in TESTER_PROFILES:
                password = secrets.token_urlsafe(24)
                user_model.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    role=RoleChoices.DEVELOPER,
                    tech=TechChoices.TESTER,
                )
                credential_records.append({
                    'Username': username,
                    'Name': f'{first_name} {last_name}',
                    'Role': RoleChoices.DEVELOPER,
                    'Tech': TechChoices.TESTER,
                    'Password': password,
                })

            output = '\n\n'.join(
                '\n'.join(f'{key}: {value}' for key, value in record.items())
                for record in credential_records
            ) + '\n'
            credentials_path.write_text(output, encoding='utf-8')

        self.stdout.write(
            self.style.SUCCESS(
                'Updated 15 profiles and created 3 software tester profiles. '
                f'Credentials saved to {credentials_path}.'
            )
        )
