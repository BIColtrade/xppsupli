from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


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
    ('ceo', 'Presidencia'),
    ('direccion_comercial', 'Direccion Comercial'),
    ('tecnologia', 'Tech'),
    ('accounting', 'Accounting'),
    ('finanzas', 'Finance'),
    ('sales', 'Sales'),
    ('operations', 'Operations (Ops)'),
    ('procurement', 'Procurement'),
    ('trade', 'Trade Marketing'),
    ('brands', 'Brands'),
    ('bi', 'Business Intelligence'),
    ('sales_corporativo', 'Sales Corporativo'),
    ('sales_retail', 'Sales Retail'),
    ('people', 'People'),
    ('quality', 'Quality'),
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
    cargo = models.CharField(max_length=150, null=True, blank=True)
    jefe_directo = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reportes_directos",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        full_name = f"{self.nombre} {self.apellido}".strip()
        return full_name or self.email


class PasswordResetCode(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="reset_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "password_reset_codes"
        indexes = [
            models.Index(fields=["user", "code"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_expired(self):
        return self.expires_at <= timezone.now()
