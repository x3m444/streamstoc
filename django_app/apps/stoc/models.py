from django.db import models
from django.contrib.auth.models import AbstractUser


class StocUser(AbstractUser):
    is_readonly = models.BooleanField(default=False, verbose_name='Read-only')

    class Meta:
        db_table = 'stoc_users'
        verbose_name = 'Utilizator'
        verbose_name_plural = 'Utilizatori'

    def __str__(self):
        return self.username


class UserPreferences(models.Model):
    """Per-user preferences — persistent across sessions."""
    user = models.OneToOneField(StocUser, on_delete=models.CASCADE, related_name='preferences')
    default_nava = models.IntegerField(default=978, verbose_name='Navă implicită')
    default_tragator = models.CharField(max_length=100, default='COSTEL', verbose_name='Tractator implicit')
    default_data = models.DateField(auto_now=True, verbose_name='Data actualizată')
    
    class Meta:
        db_table = 'stoc_user_preferences'
        verbose_name = 'Preferințe utilizator'
        verbose_name_plural = 'Preferințe utilizatori'
    
    def __str__(self):
        return f"Preferințe {self.user.username}"


class Cable(models.Model):
    id = models.AutoField(primary_key=True, db_column='ID')
    nr_lista = models.TextField(null=True, blank=True, db_column='Nr Lista')
    id_lista = models.TextField(null=True, blank=True, db_column='ID Lista')
    locatie = models.TextField(null=True, blank=True, db_column='Locatie')
    lungime = models.FloatField(null=True, blank=True, db_column='Lungime')
    nr_cabluri = models.IntegerField(null=True, blank=True, db_column='Nr Cabluri')
    nava = models.IntegerField(null=True, blank=True, db_column='Nava')
    tragator = models.TextField(null=True, blank=True, db_column='Tragator')
    data = models.DateField(null=True, blank=True, db_column='Data')
    trimis = models.BooleanField(null=True, blank=True, default=False, db_column='Trimis')
    data_trimisa = models.DateField(null=True, blank=True, db_column='Data trimisa')
    dosar = models.TextField(null=True, blank=True, db_column='Dosar')
    rework = models.BooleanField(null=True, blank=True, default=False, db_column='Rework')
    data_rework = models.DateField(null=True, blank=True, db_column='Data Rework')
    ore_rework = models.FloatField(null=True, blank=True, db_column='Ore Rework')

    class Meta:
        managed = False
        db_table = 'list963'
