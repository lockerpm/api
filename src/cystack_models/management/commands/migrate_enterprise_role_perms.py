from django.core.management import BaseCommand


from shared.constants.enterprise_members import *
from cystack_models.models import *


class Command(BaseCommand):

    def handle(self, *args, **options):
        primary_admin_role = EnterpriseMemberRole.objects.get(name=E_MEMBER_ROLE_PRIMARY_ADMIN)
        admin_role = EnterpriseMemberRole.objects.get(name=E_MEMBER_ROLE_ADMIN)
        member_role = EnterpriseMemberRole.objects.get(name=E_MEMBER_ROLE_MEMBER)

        # Create permissions HERE
        perms_list = [
            # Enterprise perms
            {
                "scope": "enterprise", "codename": "list", "description": "Can get list enterprises",
                "roles": ["primary_admin", "admin", "member"]
            },
            {
                "scope": "enterprise", "codename": "retrieve", "description": "Can view enterprise",
                "roles": ["primary_admin", "admin", "member"]
            },
            {
                "scope": "enterprise", "codename": "create", "description": "Can create enterprise",
                "roles": ["primary_admin", "admin", "member"]
            },
            {
                "scope": "enterprise", "codename": "update", "description": "Can update enterprise",
                "roles": ["primary_admin", "admin"]
            },
            {
                "scope": "enterprise", "codename": "destroy", "description": "Can delete enterprise",
                "roles": ["primary_admin"]
            },

            # Domain perms
            {
                "scope": "domain", "codename": "list", "description": "Can get list domains",
                "roles": ["primary_admin", "admin", "member"]
            },
            {
                "scope": "domain", "codename": "create", "description": "Can create domain",
                "roles": ["primary_admin", "admin"]
            },
            {
                "scope": "domain", "codename": "verification", "description": "Can verify domain",
                "roles": ["primary_admin", "admin"]
            },
            {
                "scope": "domain", "codename": "destroy", "description": "Can delete domain",
                "roles": ["primary_admin"]
            },

        ]
        for perm in perms_list:
            if Permission.objects.filter(scope=perm.get("scope"), codename=perm.get("codename")).exists() is False:
                perm_obj = Permission.create(
                    scope=perm["scope"], codename=perm["codename"], description=perm["description"]
                )
            else:
                perm_obj = Permission.objects.get(scope=perm["scope"], codename=perm["codename"])

            if "member" in perm["roles"]:
                member_role.add_role_perm(perm_obj)
            else:
                member_role.remove_role_perm(perm_obj)
            if "primary_admin" in perm["roles"]:
                primary_admin_role.add_role_perm(perm_obj)
            else:
                primary_admin_role.remove_role_perm(perm_obj)
            if "admin" in perm["roles"]:
                admin_role.add_role_perm(perm_obj)
            else:
                admin_role.remove_role_perm(perm_obj)
