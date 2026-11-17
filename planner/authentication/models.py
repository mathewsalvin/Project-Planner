from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser

class RoleChoices(models.TextChoices):
    ADMIN = 'Admin', 'Admin'

    COORDINATOR = 'Project Coordinator', 'Project Coordinator'

    DEVELOPER = 'Developer','Developer'

class TechChoices(models.TextChoices):

    BACKEND='Backend Developer','Backend Developer'

    FRONTEND='Frontend Developer','Frontend Developer'

    FULLSTACK='Fullstack Developer','Fullstack Developer'

    UI_UX= 'UI/UX Designer','UI/UX Designer'

    TESTER='Software Tester','Software Tester'

class Profile(AbstractUser):

    role = models.CharField(max_length=20,choices=RoleChoices.choices)

    tech = models.CharField(max_length=30,choices=TechChoices.choices,null=True,blank=True)



    class Meta:

        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        name = self.get_full_name() or self.username
        return f'{name} - {self.tech}' if self.tech else name