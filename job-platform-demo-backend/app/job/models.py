from django.db import models
from django.contrib.postgres.fields import ArrayField


class Job(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('scheduled', 'Scheduled'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    salary_range = models.JSONField(default=dict)
    company_name = models.CharField(max_length=200)
    posting_date = models.DateField()
    expiration_date = models.DateField()
    required_skills = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-posting_date']
