from django.db import models

class Target(models.Model):
    name = models.CharField(max_length=255)
    platform = models.CharField(max_length=100)
    program_handle = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Asset(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE)
    domain_or_url = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    in_scope = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.domain_or_url


class Task(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=100)
    deadline = models.DateTimeField()
    date_completed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title