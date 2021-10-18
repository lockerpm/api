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

OrganizationUser_Invited = 1500,
OrganizationUser_Confirmed = 1501,
OrganizationUser_Updated = 1502,
OrganizationUser_Removed = 1503,
OrganizationUser_UpdatedGroups = 1504,
OrganizationUser_UnlinkedSso = 1505,
OrganizationUser_ResetPassword_Enroll = 1506,
OrganizationUser_ResetPassword_Withdraw = 1507,
OrganizationUser_AdminResetPassword = 1508,
OrganizationUser_ResetSsoLink = 1509,

Organization_Updated = 1600,
Organization_PurgedVault = 1601,


LOG_TYPES = {
    # User Events
    EVENT_USER_LOGIN: {
        "vi": "Đăng nhập",
        "en": "Logged in"
    },
    EVENT_USER_CHANGE_PASSWORD: {
        "vi": "",
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
        "vi": "",
        "en": "Login attempted failed with incorrect password"
    },
    1006: {
        "vi": "",
        "en": "Login attempt failed with incorrect two-step login"
    },
    EVENT_USER_EXPORT_VAULT: {
        "vi": "",
        "en": "Exported Vault"
    },

    # Item Events
    EVENT_CIPHER_CREATED: {
        "vi": "",
        "en": "Created item {}"
    },
    EVENT_CIPHER_UPDATED: {
        "vi": "",
        "en": "Edited item {}"
    },
    EVENT_CIPHER_DELETED: {
        "vi": "",
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
        "vi": "",
        "en": "Shared item {}"
    },
    EVENT_CIPHER_UPDATE_COLLECTION: {
        "vi": "",
        "en": "Edited collections for item {}"
    },
    EVENT_CIPHER_VIEWED: {
        "vi": "",
        "en": "Viewed item {}"
    },
    1108: {
        "vi": "",
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
        "vi": "",
        "en": "Sent item {} to trash"
    },
    EVENT_CIPHER_RESTORE: {
        "vi": "",
        "en": "Restored item {}"
    },

    # Collections event
    EVENT_COLLECTION_CREATED: {
        "vi": "",
        "en": "Created collection {}"
    },
    EVENT_COLLECTION_UPDATED: {
        "vi": "",
        "en": "Edited collection {}"
    },
    EVENT_COLLECTION_DELETED: {
        "vi": "",
        "en": "Deleted collection {}"
    },

    # Groups Event
    EVENT_GROUP_CREATED: {
        "vi": "",
        "en": "Created group {}"
    },
    EVENT_GROUP_UPDATED: {
        "vi": "",
        "en": "Edited group {}"
    },
    EVENT_GROUP_DELETED: {
        "vi": "",
        "en": "Deleted group {}"
    },

    # Organziation events
    1500: {
        "vi": "",
        "en": "Invited user {}"
    },
    1501: {
        "vi": "",
        "en": "Confirmed user {}"
    },
    1502: {
        "vi": "",
        "en": "Edited user {}"
    },
    1503: {
        "vi": "",
        "en": "Removed user {}"
    },
    1504: {
        "vi": "",
        "en": "Edited groups for user {}"
    },
    1505: {
        "vi": "",
        "en": "Unlinked SSO"
    },
    1600: {
        "vi": "",
        "en": "Edited organization settings"
    },
    1601: {
        "vi": "",
        "en": "Purged organization vault"
    },
    1700: {
        "vi": "",
        "en": "Updated a Policy"
    }
}
