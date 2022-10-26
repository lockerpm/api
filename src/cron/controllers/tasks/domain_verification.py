from shared.background import LockerBackgroundFactory, BG_DOMAIN
from cystack_models.models.enterprises.domains.domains import Domain
from shared.constants.enterprise_members import E_MEMBER_ROLE_ADMIN
from shared.utils.app import now


def domain_verification():
    current_time = now()
    # Find the domains aren't verified
    unverified_domains = Domain.objects.filter(verification=False)
    for unverified_domain in unverified_domains:
        is_verify = unverified_domain.check_verification()
        # If this domain is verified => Send notification
        if is_verify is True:
            owner_user_id = unverified_domain.enterprise.enterprise_members.get(is_primary=True).user_id
            LockerBackgroundFactory.get_background(bg_name=BG_DOMAIN, background=False).run(
                func_name="domain_verified", **{
                    "owner_user_id": owner_user_id,
                    "domain": unverified_domain,
                    "verification": True
                }
            )
        else:
            # Check the domain is added more than one day?
            if current_time >= unverified_domain.created_time + 86400 and unverified_domain.is_notify_failed is False:
                owner_user_id = unverified_domain.enterprise.enterprise_members.get(is_primary=True).user_id
                LockerBackgroundFactory.get_background(bg_name=BG_DOMAIN, background=False).run(
                    func_name="domain_unverified", **{
                        "owner_user_id": owner_user_id,
                        "domain": unverified_domain
                    }
                )
                unverified_domain.is_notify_failed = True
                unverified_domain.save()
