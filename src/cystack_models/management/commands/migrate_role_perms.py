from django.core.management import BaseCommand


from shared.constants.members import *
from endpoint_models.models.members.team_members import TeamMember
from endpoint_models.models.permissions.permissions import Permission
from endpoint_models.models.members.member_roles import MemberRole


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
            {"scope": "team", "codename": "retrieve_secret", "description": "Can retrieve team secret key", "roles": ["owner", "admin", "manager", "member"]},
            {"scope": "team", "codename": "create_secret", "description": "Can re-create team secret key", "roles": ["owner"]},

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
