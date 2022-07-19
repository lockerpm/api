from django.db import models
from django.core.cache import cache

from shared.permissions.app import CACHE_ROLE_ENTERPRISE_PERMISSION_PREFIX


class EnterpriseMemberRole(models.Model):
    name = models.CharField(primary_key=True, max_length=45)

    class Meta:
        db_table = 'e_member_roles'

    def get_permissions(self):
        cache_key = "{}{}".format(CACHE_ROLE_ENTERPRISE_PERMISSION_PREFIX, self.name).lower()
        if cache_key not in cache:
            perms = self.get_role_permissions().values_list('permission__scope', 'permission__codename').order_by()
            cache.set(cache_key, ["{}.{}".format(scope, codename) for scope, codename in perms], 4 * 60 * 60)
        return cache.get(cache_key)

    def get_role_permissions(self):
        return self.enterprise_role_permissions.all()

    def add_role_perm(self, perm_obj):
        if self.enterprise_role_permissions.filter(permission=perm_obj).exists() is False:
            self.enterprise_role_permissions.model.create(self, perm_obj)

    def remove_role_perm(self, perm_obj):
        self.enterprise_role_permissions.filter(permission=perm_obj).delete()
