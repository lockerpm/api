from shared.background import LockerBackgroundFactory, BG_NOTIFY
from cystack_models.models.enterprises.domains.domains import Domain


def domain_verification():
    # Find the domains aren't verified
    unverified_domains = Domain.objects.filter(verification=False)
    for unverified_domain in unverified_domains:
        is_verify = unverified_domain.check_verification()
        # If this domain is verified => Send notification
        if is_verify is True:
            owner_user_id = unverified_domain.enterprise.enterprise_members.get(is_primary=True).user_id
            LockerBackgroundFactory.get_background(
                bg_name=BG_NOTIFY, background=False
            ).run(func_name="domain_verified", **{
                "owner_user_id": owner_user_id,
                "domain": unverified_domain.domain,
                "organization_name": unverified_domain.enterprise.name,
            })
