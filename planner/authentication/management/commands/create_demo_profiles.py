import secrets
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from authentication.models import RoleChoices, TechChoices


class Command(BaseCommand):
    help = 'Create demo coordinator and developer profiles and save new credentials locally.'

    def handle(self, *args, **options):
        user_model = get_user_model()
        profiles = [
            (f'coordinator{i:02}', RoleChoices.COORDINATOR, None)
            for i in range(1, 4)
        ]
        profiles.extend(
            (f'{username_prefix}{i:02}', RoleChoices.DEVELOPER, tech)
            for username_prefix, tech in (
                ('backend', TechChoices.BACKEND),
                ('frontend', TechChoices.FRONTEND),
                ('fullstack', TechChoices.FULLSTACK),
                ('uiux', TechChoices.UI_UX),
            )
            for i in range(1, 4)
        )

        credentials = []
        skipped = []
        with transaction.atomic():
            for username, role, tech in profiles:
                if user_model.objects.filter(username=username).exists():
                    skipped.append(username)
                    continue

                password = secrets.token_urlsafe(24)
                user_model.objects.create_user(
                    username=username,
                    password=password,
                    role=role,
                    tech=tech,
                )
                credentials.append(
                    f'Username: {username}\n'
                    f'Role: {role}\n'
                    f'Tech: {tech or "N/A"}\n'
                    f'Password: {password}\n'
                )

        if credentials:
            credentials_path = Path(__file__).resolve().parents[2] / 'credentials.txt'
            with credentials_path.open('a', encoding='utf-8') as credentials_file:
                if credentials_path.stat().st_size:
                    credentials_file.write('\n')
                credentials_file.write('\n'.join(credentials))
                credentials_file.write('\n')
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {len(credentials)} profile(s). Credentials saved to '
                    f'{credentials_path}.'
                )
            )
        else:
            self.stdout.write('No new profiles created.')

        if skipped:
            self.stdout.write(f'Skipped existing usernames: {", ".join(skipped)}')
