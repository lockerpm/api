TRIAL_PERSONAL_PLAN = 30 * 86400        # 30 days
TRIAL_TEAM_PLAN = 10 * 86400            # 10 days
TRIAL_TEAM_MEMBERS = 2

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


FAMILY_MAX_MEMBER = 6


# ------------- Banking code ----------------------------- #
BANKING_ID_PWD_MANAGER = "LK"
BANKING_ID_WEB_SECURITY = "CW"
