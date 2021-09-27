TRIAL_ASSET_NUMBER = 1
TRIAL_TEAM_NUMBER = 2

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

LIST_PAYMENT_METHOD = [PAYMENT_METHOD_CARD, PAYMENT_METHOD_WALLET, PAYMENT_METHOD_BANKING]


# ------------------- Payment status -------------------------------- #
PAYMENT_STATUS_FAILED = "failed"        # Failed
PAYMENT_STATUS_PAID = "paid"            # Successful
PAYMENT_STATUS_PENDING = "pending"      # Contact pending
PAYMENT_STATUS_PAST_DUE = "past_due"    # Subscription failed


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
PLAN_TYPE_PM_PERSONAL_PREMIUM = "pm_personal_premium"
PLAN_TYPE_PM_FAMILY_DISCOUNT = "pm_family_discount"
PLAN_TYPE_PM_ENTERPRISE = "pm_business_premium"


FAMILY_MAX_MEMBER = 5
