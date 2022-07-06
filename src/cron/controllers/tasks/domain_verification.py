from core.settings import CORE_CONFIG
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from cystack_models.models.domains.domains import Domain


def domain_verification():
    team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()

    # Find the domains aren't verified
    unverified_domains = Domain.objects.filter(verification=True)
    for unverified_domain in unverified_domains:
        is_verify = unverified_domain.check_verification()
        # If this domain is verified => Send notification
        if is_verify is True:
            owner_user_id = team_repository.get_primary_member(team=unverified_domain.team).user_id
            LockerBackgroundFactory.get_background(
                bg_name=BG_NOTIFY, background=False
            ).run(func_name="domain_verified", **{
                "owner_user_id": owner_user_id,
                "domain": unverified_domain.domain,
                "organization_name": unverified_domain.team.name,
            })
