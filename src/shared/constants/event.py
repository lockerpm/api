EVENT_USER_LOGIN = 1000
EVENT_USER_CHANGE_PASSWORD = 1001
# EVENT_USER_ENABLED_2FA = 1002
# EVENT_USER_DISABLED_2FA = 1003
EVENT_USER_LOGIN_FAILED = 1005
# EVENT_USER_LOGIN_2FA_FAILED = 1006
# EVENT_USER_EXPORT_VAULT = 1007
EVENT_USER_BLOCK_LOGIN = 1008

EVENT_ITEM_SHARE_CREATED = 1100
EVENT_ITEM_QUICK_SHARE_CREATED = 1101


# ---------------- New events code ids of the Enterprise ----------------- #
EVENT_ENTERPRISE_CREATED = 1800
EVENT_ENTERPRISE_UPDATED = 1801

EVENT_E_MEMBER_INVITED = 1900
EVENT_E_MEMBER_CONFIRMED = 1901
EVENT_E_MEMBER_UPDATED_ROLE = 1902
EVENT_E_MEMBER_REMOVED = 1903
EVENT_E_MEMBER_UPDATED_GROUP = 1904
EVENT_E_MEMBER_ENABLED = 1905
EVENT_E_MEMBER_DISABLED = 1906

EVENT_E_GROUP_CREATED = 2000
EVENT_E_GROUP_UPDATED = 2001
EVENT_E_GROUP_DELETED = 2002

EVENT_E_DOMAIN_CREATED = 2100
EVENT_E_DOMAIN_VERIFIED = 2101
EVENT_E_DOMAIN_DELETED = 2102


LOG_TYPES = {
    # User Events
    EVENT_USER_LOGIN: {
        "vi": "Đăng nhập",
        "en": "Logged in"
    },
    EVENT_USER_CHANGE_PASSWORD: {
        "vi": "Đã thay đổi mật khẩu chính của tài khoản",
        "en": "Changed account password"
    },
    EVENT_USER_LOGIN_FAILED: {
        "vi": "Cố gắng đăng nhập với mật khẩu không chính xác",
        "en": "Login attempted failed with incorrect password"
    },
    EVENT_USER_BLOCK_LOGIN: {
        "vi": "User <b>{user_email}</b> đã bị khóa đăng nhập bởi chính sách của doanh nghiệp",
        "vi_non_html": "User {user_email} đã bị khóa đăng nhập bởi chính sách của doanh nghiệp",
        "en": "User <b>{user_email}</b> is blocked login by the enterprise policy",
        "en_non_html": "User {user_email} is blocked login by the enterprise policy",
    },

    # Item events
    EVENT_ITEM_SHARE_CREATED: {
        "vi": "Đã chia sẻ một {item_type} với người dùng khác",
        "vi_non_html": "Đã chia sẻ một {item_type} với người dùng khác",
        "en": "shared a(n) {item_type} item with users",
        "en_non_html": "shared a(n) {item_type} item with users"
    },
    EVENT_ITEM_QUICK_SHARE_CREATED: {
        "vi": "Đã chia sẻ một <b>{item_type}</b> thông qua Quick Share",
        "vi_non_html": "Đã chia sẻ một {item_type} thông qua Quick Share",
        "en": "shared a(n) <b>{item_type}</b> item via Quick Share",
        "en_non_html": "shared a(n) {item_type} item via Quick Share"
    },

    # Enterprise events
    EVENT_ENTERPRISE_CREATED: {
        "vi": "Doanh nghiệp đã được tạo",
        "en": "The enterprise is created"
    },
    EVENT_ENTERPRISE_UPDATED: {
        "vi": "Thông tin của doanh nghiệp đã được cập nhật",
        "en": "The enterprise's information is updated"
    },

    # Enterprise member events
    EVENT_E_MEMBER_INVITED: {
        "vi": "User <b>{user_email}</b> đã được mời vào doanh nghiệp",
        "vi_non_html": "User {user_email} đã được mời vào doanh nghiệp",
        "en": "User <b>{user_email}</b> has been invited to your enterprise",
        "en_non_html": "User {user_email} has been invited to your enterprise"
    },
    EVENT_E_MEMBER_CONFIRMED: {
        "vi": "User <b>{user_email}</b> đã tham gia vào doanh nghiệp",
        "vi_non_html": "User {user_email} đã tham gia vào doanh nghiệp",
        "en": "User <b>{user_email}</b> has joined your enterprise",
        "en_non_html": "User {user_email} has joined your enterprise"
    },
    EVENT_E_MEMBER_UPDATED_ROLE: {
        "vi": "User <b>{user_email}</b> vừa chuyển từ {old_role} sang {new_role}",
        "vi_non_html": "User {user_email} vừa chuyển từ {old_role} sang {new_role}",
        "en": "User <b>{user_email}</b> has been changed from {old_role} to {new_role}",
        "en_non_html": "User {user_email} has been changed from {old_role} to {new_role}"
    },
    EVENT_E_MEMBER_REMOVED: {
        "vi": "User <b>{user_email}</b> đã rời khỏi doanh nghiệp",
        "vi_non_html": "User {user_email} đã rời khỏi doanh nghiệp",
        "en": "User <b>{user_email}</b> has left your enterprise",
        "en_non_html": "User {user_email} has left your enterprise"
    },
    EVENT_E_MEMBER_UPDATED_GROUP: {
        "vi": "Nhóm của user <b>{user_email}</b> vừa được cập nhật",
        "vi_non_html": "Nhóm của user {user_email} vừa được cập nhật",
        "en": "The groups of user <b>{user_email}</b> has been updated",
        "en_non_html": "The groups of user {user_email} has been updated"
    },
    EVENT_E_MEMBER_ENABLED: {
        "vi": "User <b>{user_email}</b> đã được kích hoạt",
        "vi_non_html": "User {user_email} đã được kích hoạt",
        "en": "User <b>{user_email}</b> has been enabled",
        "en_non_html": "User {user_email} has been enabled"
    },
    EVENT_E_MEMBER_DISABLED: {
        "vi": "User <b>{user_email}</b> đã bị vô hiệu hóa",
        "vi_non_html": "User {user_email} đã bị vô hiệu hóa",
        "en": "User <b>{user_email}</b> has been disabled",
        "en_non_html": "User {user_email} has been disabled"
    },

    # Enterprise group events
    EVENT_E_GROUP_CREATED: {
        "vi": "Nhóm {group_name} đã được tạo",
        "en": "A group {group_name} has been created"
    },
    EVENT_E_GROUP_UPDATED: {
        "vi": "Tên nhóm đã được chuyển từ {old_name} sang {new_name}",
        "en": "The group's name has been changed from {old_name} to {new_name}"
    },
    EVENT_E_GROUP_DELETED: {
        "vi": "Nhóm {group_name} đã bị xóa",
        "en": "The group {group_name} is deleted"
    },

    # Enterprise domain events
    EVENT_E_DOMAIN_CREATED: {
        "vi": "Tên miền <b>{domain_address}</b> đã được tạo",
        "vi_non_html": "Tên miền {domain_address} đã được tạo",
        "en": "The domain <b>{domain_address}</b> has been created",
        "en_non_html": "The domain {domain_address} has been created",
    },
    EVENT_E_DOMAIN_VERIFIED: {
        "vi": "Tên miền <b>{domain_address}</b> đã được xác thực",
        "vi_non_html": "Tên miền {domain_address} đã được xác thực",
        "en": "The domain <b>{domain_address}</b> has been verified",
        "en_non_html": "The domain {domain_address} has been verified"
    },
    EVENT_E_DOMAIN_DELETED: {
        "vi": "Tên miền <b>{domain_address}</b> đã bị xóa",
        "vi_non_html": "Tên miền {domain_address} đã bị xóa",
        "en": "The domain <b>{domain_address}</b> is deleted",
        "en_non_html": "The domain {domain_address} is deleted"
    },
}