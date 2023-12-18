DEFAULT_TEAM_NAME = "My Team"


MEMBER_ROLE_OWNER = "owner"
MEMBER_ROLE_ADMIN = "admin"
MEMBER_ROLE_MANAGER = "manager"
MEMBER_ROLE_MEMBER = "member"

TEAM_LIST_ROLE = [MEMBER_ROLE_OWNER, MEMBER_ROLE_MEMBER, MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER]


MEMBER_SHARE_TYPE_EDIT = "Edit"
MEMBER_SHARE_TYPE_VIEW = "View"
MEMBER_SHARE_TYPE_ONLY_FILL = "Only fill"


PM_MEMBER_STATUS_INVITED = "invited"
PM_MEMBER_STATUS_ACCEPTED = "accepted"
PM_MEMBER_STATUS_CONFIRMED = "confirmed"

MAP_MEMBER_STATUS = {
    0: PM_MEMBER_STATUS_INVITED,
    1: PM_MEMBER_STATUS_ACCEPTED,
    2: PM_MEMBER_STATUS_CONFIRMED
}

MAP_MEMBER_STATUS_TO_INT = {
    PM_MEMBER_STATUS_INVITED: 0,
    PM_MEMBER_STATUS_ACCEPTED: 1,
    PM_MEMBER_STATUS_CONFIRMED: 2
}

MAP_MEMBER_TYPE_BW = {
    MEMBER_ROLE_MANAGER: 3,
    MEMBER_ROLE_MEMBER: 2,
    MEMBER_ROLE_ADMIN: 1,
    MEMBER_ROLE_OWNER: 0
}

MAP_MEMBER_TYPE_FROM_BW = {
    3: MEMBER_ROLE_MANAGER,
    2: MEMBER_ROLE_MEMBER,
    1: MEMBER_ROLE_ADMIN,
    0: MEMBER_ROLE_OWNER
}