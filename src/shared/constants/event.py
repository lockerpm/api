EVENT_USER_LOGIN = 1000
EVENT_USER_CHANGE_PASSWORD = 1001
EVENT_USER_LOGIN_FAILED = 1005
EVENT_USER_EXPORT_VAULT = 1007

EVENT_CIPHER_CREATED = 1100
EVENT_CIPHER_UPDATED = 1101
EVENT_CIPHER_DELETED = 1102
EVENT_CIPHER_SHARED = 1105
EVENT_CIPHER_UPDATE_COLLECTION = 1106
EVENT_CIPHER_VIEWED = 1107
EVENT_CIPHER_COPIED_PASSWORD = 1111
EVENT_CIPHER_COPIED_CARD_CODE = 1113
EVENT_CIPHER_AUTOFILLED = 1114
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
    1002: {
        "vi": "",
        "en": "Enabled/updated two-step login"
    },
    1003: {
        "vi": "",
        "en": "Disabled two-step login"
    },
    1004: {
        "vi": "",
        "en": "Recovered account from two-step login"
    },
    EVENT_USER_LOGIN_FAILED: {
        "vi": "Cố gắng đăng nhập với mật khẩu không chính xác",
        "en": "Login attempted failed with incorrect password"
    },
    1006: {
        "vi": "Đăng nhập thất bại với 2FA không chính xác",
        "en": "Login attempt failed with incorrect two-step login"
    },
    EVENT_USER_EXPORT_VAULT: {
        "vi": "Xuất kho dữ liệu",
        "en": "Exported Vault"
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
    1103: {
        "vi": "",
        "en": "Created attachment for item {}"
    },
    1104: {
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
    1108: {
        "vi": "Hiển thị mật khẩu của item {}",
        "en": "Viewed password for item {}"
    },
    1109: {
        "vi": "",
        "en": "Viewed hidden field for item {}"
    },
    1110: {
        "vi": "",
        "en": "Viewed security code for item {}"
    },
    EVENT_CIPHER_COPIED_PASSWORD: {
        "vi": "",
        "en": "Copied password for item {}"
    },
    1112: {
        "vi": "",
        "en": "Copied hidden field for item {}"
    },
    EVENT_CIPHER_COPIED_CARD_CODE: {
        "vi": "",
        "en": "Copied security code for item {}"
    },
    EVENT_CIPHER_AUTOFILLED: {
        "vi": "",
        "en": "Auto-filled item {}"
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
    1505: {
        "vi": "",
        "en": "Unlinked SSO"
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
}
