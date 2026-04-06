from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError('El usuario debe tener un correo electronico')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(email, username, password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


TIPO_USUARIO_CHOICES = [
    ('colaborador', 'Colaborador'),
    ('lider', 'Lider'),
    ('admin', 'Admin'),
]

AREA_CHOICES = [
    ('trade', 'Trade Marketing'),
    ('supli', 'Supply Chain'),
    ('people', 'People & Cultura'),
    ('comercial', 'Comercial'),
    ('logistica', 'Logistica'),
    ('tecnologia', 'Tecnologia'),
    ('finanzas', 'Finanzas'),
    ('administracion', 'Administracion'),
    ('otra', 'Otra'),
]


class Usuario(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150, null=True, blank=True)
    edad = models.PositiveIntegerField(null=True, blank=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, null=True, blank=True)
    area = models.CharField(max_length=30, choices=AREA_CHOICES, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        full_name = f"{self.nombre} {self.apellido}".strip()
        return full_name or self.email
