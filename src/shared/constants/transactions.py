TRIAL_PERSONAL_PLAN = 14 * 86400        # 14 days
TRIAL_PERSONAL_DURATION_TEXT = "14 days"
TRIAL_PROMOTION = 6 * 30 * 86400        # 6 months
TRIAL_PROMOTION_DURATION_TEXT = "6 months"

TRIAL_BETA_EXPIRED = 1654016400         # 1/6/2022 00:00:00
TRIAL_TEAM_PLAN = 14 * 86400            # 14 days
TRIAL_TEAM_MEMBERS = 10

REFERRAL_EXTRA_TIME = 86400 * 30        # 30 days
REFERRAL_LIMIT = 3


# -------------------- UTM Source Promotion ------------------------ #
UTM_SOURCE_PROMOTIONS = "plans-promotion"
LIST_UTM_SOURCE_PROMOTIONS = [UTM_SOURCE_PROMOTIONS]


# ------------------- Currency ------------------------------------- #
CURRENCY_VND = "VND"
CURRENCY_USD = "USD"
CURRENCY_WHC = "WHC"

LIST_CURRENCY = [CURRENCY_VND, CURRENCY_USD]

# ------------------- Transaction type ------------------------------ #
TRANSACTION_TYPE_PAYMENT = "Payment"
TRANSACTION_TYPE_REFUND: str = "Refund"


# ------------------- Payment method -------------------------------- #
PAYMENT_METHOD_CARD = "card"
PAYMENT_METHOD_BANKING = "banking"
PAYMENT_METHOD_WALLET = "wallet"
PAYMENT_METHOD_MOBILE = "mobile"

LIST_PAYMENT_METHOD = [PAYMENT_METHOD_CARD, PAYMENT_METHOD_WALLET, PAYMENT_METHOD_BANKING]


# ------------------- Payment status -------------------------------- #
PAYMENT_STATUS_FAILED = "failed"            # Failed
PAYMENT_STATUS_PAID = "paid"                # Successful
PAYMENT_STATUS_PENDING = "pending"          # Contact pending
PAYMENT_STATUS_PROCESSING = "processing"    # CyStack banking processing
PAYMENT_STATUS_PAST_DUE = "past_due"        # Subscription failed


# ------------------- Duration types -------------------------------- #
DURATION_MONTHLY = "monthly"
DURATION_HALF_YEARLY = "half_yearly"
DURATION_YEARLY = "yearly"

LIST_DURATION = [DURATION_MONTHLY, DURATION_HALF_YEARLY, DURATION_YEARLY]


# ------------------- Promo code types ------------------------------ #
PROMO_AMOUNT = "amount_off"
PROMO_PERCENTAGE = "percentage_off"


# ------------------- Plan type constants --------------------------- #
PLAN_TYPE_PM_FREE = "pm_free"
PLAN_TYPE_PM_PREMIUM = "pm_premium"
PLAN_TYPE_PM_FAMILY = "pm_family"

PLAN_TYPE_PM_ENTERPRISE = "pm_enterprise"

FAMILY_MAX_MEMBER = 6


# ------------- Banking code ----------------------------- #
BANKING_ID_PWD_MANAGER = "LK"
BANKING_ID_WEB_SECURITY = "CW"
