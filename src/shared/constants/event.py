EVENT_USER_LOGIN = 1000
EVENT_USER_CHANGE_PASSWORD = 1001
EVENT_USER_ENABLED_2FA = 1002
EVENT_USER_DISABLED_2FA = 1003
EVENT_USER_LOGIN_FAILED = 1005
EVENT_USER_LOGIN_2FA_FAILED = 1006
EVENT_USER_EXPORT_VAULT = 1007
EVENT_USER_BLOCK_LOGIN = 1008

EVENT_CIPHER_CREATED = 1100
EVENT_CIPHER_UPDATED = 1101
EVENT_CIPHER_DELETED = 1102
EVENT_CIPHER_ATTACHMENT_CREATED = 1103
EVENT_CIPHER_ATTACHMENT_DELETED = 1104
EVENT_CIPHER_SHARED = 1105
EVENT_CIPHER_UPDATE_COLLECTION = 1106
EVENT_CIPHER_VIEWED = 1107
EVENT_CIPHER_SOFT_DELETED = 1115
EVENT_CIPHER_RESTORE = 1116

EVENT_COLLECTION_CREATED = 1300
EVENT_COLLECTION_UPDATED = 1301
EVENT_COLLECTION_DELETED = 1202

EVENT_GROUP_CREATED = 1400
EVENT_GROUP_UPDATED = 1401
EVENT_GROUP_DELETED = 1402

EVENT_MEMBER_INVITED = 1500
EVENT_MEMBER_CONFIRMED = 1501
EVENT_MEMBER_UPDATED = 1502
EVENT_MEMBER_REMOVED = 1503
EVENT_MEMBER_UPDATED_GROUP = 1504

EVENT_TEAM_UPDATED = 1600
EVENT_TEAM_PURGED_DATA = 1601

EVENT_TEAM_POLICY_UPDATED = 1700


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
    EVENT_USER_ENABLED_2FA: {
        "vi": "Đã bật/Cập nhật xác thực 2 bước",
        "en": "Enabled/updated two-step login"
    },
    EVENT_USER_DISABLED_2FA: {
        "vi": "Đã tắt xác thực 2 bước",
        "en": "Disabled two-step login"
    },
    EVENT_USER_LOGIN_FAILED: {
        "vi": "Cố gắng đăng nhập với mật khẩu không chính xác",
        "en": "Login attempted failed with incorrect password"
    },
    EVENT_USER_LOGIN_2FA_FAILED: {
        "vi": "Đăng nhập thất bại với 2FA không chính xác",
        "en": "Login attempt failed with incorrect two-step login"
    },
    EVENT_USER_EXPORT_VAULT: {
        "vi": "Xuất kho dữ liệu",
        "en": "Exported Vault"
    },
    EVENT_USER_BLOCK_LOGIN: {
        "vi": "is blocked login by the enterprise policy",
        "en": "đã bị khóa đăng nhập bởi chính sách của doanh nghiệp"
    },

    # Item Events
    EVENT_CIPHER_CREATED: {
        "vi": "Tạo bản ghi mã hóa {}",
        "en": "Created item {}"
    },
    EVENT_CIPHER_UPDATED: {
        "vi": "Chỉnh sửa bản ghi {}",
        "en": "Edited item {}"
    },
    EVENT_CIPHER_DELETED: {
        "vi": "Xóa vĩnh viễn bản ghi {}",
        "en": "Permanently Deleted item {}"
    },
    EVENT_CIPHER_ATTACHMENT_CREATED: {
        "vi": "",
        "en": "Created attachment for item {}"
    },
    EVENT_CIPHER_ATTACHMENT_DELETED: {
        "vi": "",
        "en": "Deleted attachment for item {}"
    },
    EVENT_CIPHER_SHARED: {
        "vi": "Chia sẻ bản ghi {}",
        "en": "Shared item {}"
    },
    EVENT_CIPHER_UPDATE_COLLECTION: {
        "vi": "Chỉnh sửa collections của bản ghi {}",
        "en": "Edited collections for item {}"
    },
    EVENT_CIPHER_VIEWED: {
        "vi": "Hiển thị bản ghi {}",
        "en": "Viewed item {}"
    },
    EVENT_CIPHER_SOFT_DELETED: {
        "vi": "Đưa bản ghi {} vào thùng rác",
        "en": "Sent item {} to trash"
    },
    EVENT_CIPHER_RESTORE: {
        "vi": "Khôi phục bản ghi {}",
        "en": "Restored item {}"
    },

    # Collections event
    EVENT_COLLECTION_CREATED: {
        "vi": "Tạo collection {}",
        "en": "Created collection {}"
    },
    EVENT_COLLECTION_UPDATED: {
        "vi": "Cập nhật collection {}",
        "en": "Edited collection {}"
    },
    EVENT_COLLECTION_DELETED: {
        "vi": "Xóa collection {}",
        "en": "Deleted collection {}"
    },

    # Groups Event
    EVENT_GROUP_CREATED: {
        "vi": "Tạo nhóm {}",
        "en": "Created group {}"
    },
    EVENT_GROUP_UPDATED: {
        "vi": "Chỉnh sửa nhóm {}",
        "en": "Edited group {}"
    },
    EVENT_GROUP_DELETED: {
        "vi": "Xóa nhóm {}",
        "en": "Deleted group {}"
    },

    # Member events
    EVENT_MEMBER_INVITED: {
        "vi": "Mời thành viên {}",
        "en": "Invited user {}"
    },
    EVENT_MEMBER_CONFIRMED: {
        "vi": "Xác nhận thành viên {}",
        "en": "Confirmed user {}"
    },
    EVENT_MEMBER_UPDATED: {
        "vi": "Cập nhật thành viên {}",
        "en": "Edited user {}"
    },
    EVENT_MEMBER_REMOVED: {
        "vi": "Xóa thành viên {}",
        "en": "Removed user {}"
    },
    EVENT_MEMBER_UPDATED_GROUP: {
        "vi": "Cập nhật nhóm của thành viên {}",
        "en": "Edited groups for user {}"
    },

    # Team events
    EVENT_TEAM_UPDATED: {
        "vi": "Cập nhật cài đặt của tổ chức",
        "en": "Edited organization settings"
    },
    EVENT_TEAM_PURGED_DATA: {
        "vi": "Xóa dữ liệu tổ chức",
        "en": "Purged organization vault"
    },

    # Team policy events
    EVENT_TEAM_POLICY_UPDATED: {
        "vi": "Cập nhật policy của tổ chức",
        "en": "Updated the team policy"
    },

    # Enterprise events
    EVENT_ENTERPRISE_CREATED: {
        "vi": "Đã tạo doanh nghiệp",
        "en": "Created the enterprise"
    },
    EVENT_ENTERPRISE_UPDATED: {
        "vi": "Đã cập nhật thông tin doanh nghiệp",
        "en": "Update the enterprise's information"
    },

    # Enterprise member events
    EVENT_E_MEMBER_INVITED: {
        "vi": "User đã được mời vào doanh nghiệp",
        "en": "A user has been invited to your enterprise"
    },
    EVENT_E_MEMBER_CONFIRMED: {
        "vi": "User đã tham gia vào doanh nghiệp",
        "en": "A user has joined your enterprise"
    },
    EVENT_E_MEMBER_UPDATED_ROLE: {
        "vi": "Quyền của user vừa chuyển từ {old_role} sang {new_role}",
        "en": "A user's role has been changed from {old_role} to {new_role}"
    },
    EVENT_E_MEMBER_REMOVED: {
        "vi": "User đã rời khỏi doanh nghiệp",
        "en": "A user has been left your enterprise"
    },
    EVENT_E_MEMBER_UPDATED_GROUP: {
        "vi": "Nhóm của user vừa được cập nhật",
        "en": "A user's group has been updated"
    },
    EVENT_E_MEMBER_ENABLED: {
        "vi": "User đã được kích hoạt",
        "en": "A user has been enabled"
    },
    EVENT_E_MEMBER_DISABLED: {
        "vi": "User đã bị vô hiệu hóa",
        "en": "A user has been disabled"
    }
}
