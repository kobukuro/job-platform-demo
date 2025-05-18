from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CompanyDomain(models.Model):
    name = models.CharField(max_length=200, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='domains')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
