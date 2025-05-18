from django.contrib.auth.models import BaseUserManager
from company.models import CompanyDomain


class UserManager(BaseUserManager):
    def create_user(self, email, password, is_superuser=False, **extra_fields):
        email = self.normalize_email(email)
        domain = email.split('@')[-1].lower()

        try:
            company_domain = CompanyDomain.objects.get(name=domain)
            extra_fields['company'] = company_domain.company
        except CompanyDomain.DoesNotExist:
            pass

        user = self.model(email=email, is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, is_superuser=True, **extra_fields):
        return self.create_user(email, password, is_superuser, **extra_fields)
