from django.core.management import BaseCommand


from shared.constants.members import *
from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.permissions.permissions import Permission
from cystack_models.models.members.member_roles import MemberRole


class Command(BaseCommand):

    def handle(self, *args, **options):
        owner_role = MemberRole.objects.get(name=MEMBER_ROLE_OWNER)
        admin_role = MemberRole.objects.get(name=MEMBER_ROLE_ADMIN)
        manager_role = MemberRole.objects.get(name=MEMBER_ROLE_MANAGER)
        member_role = MemberRole.objects.get(name=MEMBER_ROLE_MEMBER)

        # Create permissions HERE
        perms_list = [
            # Team perms
            {"scope": "team", "codename": "list", "description": "Can get list team", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "team", "codename": "retrieve", "description": "Can view team", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "team", "codename": "create", "description": "Can create team", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "team", "codename": "update", "description": "Can update team", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "team", "codename": "destroy", "description": "Can delete team", "roles": ["owner"]},

            # Cipher perms
            {"scope": "cipher", "codename": "list", "description": "Can get list ciphers", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "cipher", "codename": "retrieve", "description": "Can retrieve a cipher", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "cipher", "codename": "create", "description": "Can create a cipher", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "cipher", "codename": "update", "description": "Can update a cipher",  "roles": ["owner", "admin", "manager"]},
            {"scope": "cipher", "codename": "destroy", "description": "Can delete ciphers", "roles": ["owner", "admin", "manager"]},

            # Collection perms
            {"scope": "collection", "codename": "list", "description": "Can get list collections", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "collection", "codename": "retrieve", "description": "Can retrieve a collection", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "collection", "codename": "create", "description": "Can create a collection", "roles": ["owner", "admin"]},
            {"scope": "collection", "codename": "update", "description": "Can update a collection", "roles": ["owner", "admin", "manager"]},
            {"scope": "collection", "codename": "destroy", "description": "Can delete collections",   "roles": ["owner", "admin"]},

            # Groups perms
            {"scope": "group", "codename": "list", "description": "Can get list group", "roles": ["owner", "admin", "manager"]},
            {"scope": "group", "codename": "retrieve", "description": "Can retrieve a group", "roles": ["owner", "admin", "manager"]},
            {"scope": "group", "codename": "create", "description": "Can create a group", "roles": ["owner", "admin"]},
            {"scope": "group", "codename": "update", "description": "Can update a group", "roles": ["owner", "admin"]},
            {"scope": "group", "codename": "destroy", "description": "Can delete groups", "roles": ["owner", "admin"]},

            # Groups perms
            {"scope": "event", "codename": "list", "description": "Can get list event", "roles": ["owner", "admin", "manager"]},
            {"scope": "event", "codename": "retrieve", "description": "Can retrieve an event", "roles": ["owner", "admin", "manager"]},
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
            if "owner" in perm["roles"]:
                owner_role.add_role_perm(perm_obj)
            if "admin" in perm["roles"]:
                admin_role.add_role_perm(perm_obj)
            if "manager" in perm["roles"]:
                manager_role.add_role_perm(perm_obj)
