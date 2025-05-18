from django.db import models
from django.contrib.postgres.fields import ArrayField
from user.models import User

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
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='jobs_created', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='jobs_last_updated', null=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-posting_date']
        indexes = [
            # Indexes for search functionality
            models.Index(fields=['title']),
            models.Index(fields=['company_name']),

            # Index for status filtering
            models.Index(fields=['status']),

            # Indexes for date sorting and filtering
            models.Index(fields=['posting_date']),
            models.Index(fields=['expiration_date']),

            # Index for location filtering
            models.Index(fields=['location']),

            # Composite indexes: status + dates, for common filter+sort combinations
            models.Index(fields=['status', 'posting_date']),
            models.Index(fields=['status', 'expiration_date']),

            # Full-text search index
            models.Index(fields=['description'], name='description_idx'),
        ]
