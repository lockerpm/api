from django.db import models


class AbstractMemberRoleORM(models.Model):
    name = models.CharField(primary_key=True, max_length=45)

    class Meta:
        abstract = True

    # def get_permissions(self):
    #     """
    #     Get list permissions of the role. Result is a list what each element contains `scope.codename`
    #     :return:
    #     """
    #     cache_key = "{}{}".format(CACHE_ROLE_PERMISSION_PREFIX, self.name).lower()
    #     if cache_key not in cache:
    #         perms = self.get_role_permissions().values_list('permission__scope', 'permission__codename').order_by()
    #         cache.set(cache_key, ["{}.{}".format(scope, codename) for scope, codename in perms], 4 * 60 * 60)
    #     return cache.get(cache_key)
    #
    # def get_role_permissions(self):
    #     return self.role_permissions.all()
    #
    # def add_role_perm(self, perm_obj):
    #     if self.role_permissions.filter(permission=perm_obj).exists() is False:
    #         self.role_permissions.model.create(self, perm_obj)
    #
    # def remove_role_perm(self, perm_obj):
    #     self.role_permissions.filter(permission=perm_obj).delete()