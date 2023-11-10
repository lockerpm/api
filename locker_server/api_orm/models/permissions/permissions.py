from django.db import models


class PermissionORM(models.Model):
    id = models.AutoField(primary_key=True)
    scope = models.CharField(max_length=128)
    codename = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = 'cs_permissions'
        unique_together = ('scope', 'codename')

    @classmethod
    def create(cls, scope: str, codename: str, description: str = ""):
        new_permission = cls(
            scope=scope, codename=codename, description=description
        )
        new_permission.save()
        return new_permission

    @classmethod
    def create_multiple(cls, *permissions_data):
        permissions = []
        for data in permissions_data:
            permissions.append(cls(
                scope=data.get("scope"), codename=data.get("codename"), description=data.get("description", "")
            ))
        cls.objects.bulk_create(permissions)
