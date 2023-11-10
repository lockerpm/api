from django.conf import settings
from django.db import models

from locker_server.api_orm.abstracts.enterprises.enterprises import AbstractEnterpriseORM
from locker_server.shared.utils.app import now, random_n_digit


def image_upload_path(instance, filename):
    return settings.MEDIA_ROOT + '/avatars/{0}/{1}'.format(instance.id, filename)


class EnterpriseORM(AbstractEnterpriseORM):
    avatar = models.CharField(null=True, default=None, max_length=255)

    class Meta(AbstractEnterpriseORM.Meta):
        swappable = 'LS_ENTERPRISE_MODEL'
        db_table = 'e_enterprises'

    @classmethod
    def create(cls, **data):
        name = data.get("name")
        description = data.get("description", "")
        creation_date = data.get("creation_date", now())
        enterprise_id = data.get("id")
        if not enterprise_id:
            # Create new team id
            while True:
                enterprise_id = random_n_digit(n=6)
                if cls.objects.filter(id=enterprise_id).exists() is False:
                    break
        new_enterprise_orm = cls(
            id=enterprise_id, name=name, description=description, creation_date=creation_date,
            enterprise_name=name,
            enterprise_address1=data.get("enterprise_address1") or "",
            enterprise_address2=data.get("enterprise_address2") or "",
            enterprise_phone=data.get("enterprise_phone") or "",
            enterprise_country=data.get("enterprise_country") or "",
            enterprise_postal_code=data.get("enterprise_postal_code") or ""
        )
        new_enterprise_orm.save()

        # Create team members
        members = data.get("members", [])
        new_enterprise_orm.enterprise_members.model.create_multiple(new_enterprise_orm, *members)

        return new_enterprise_orm
