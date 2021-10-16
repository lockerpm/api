
# ------------------------------ General code ----------------------------------- #
APP_CODE = [
    {
        "code": "0000",
        "message": "The authentication token is invalid",
        "vi_message": "Token đăng nhập không hợp lệ, gộp chung các trường hợp như token hết hạn, không decode được...v"
    },
    {
        "code": "0002",
        "message": "The account does not have enough permission to execute this operation",
        "vi_message": "Không đủ quyền để thực hiện chức năng này"
    },
    {
        "code": "0004",
        "message": "Invalid data",
        "vi_message": "Dữ liệu không hợp lệ"
    },
    {
        "code": "0005",
        "message": "Method Not Allowed",
        "vi_message": "Phương thức truy cập không hợp lệ"
    },
    {
        "code": "0008",
        "message": "Unknown Error",
        "vi_message": "Khong biet loi"
    }
]


# ------------------------------ User error code ----------------------------------- #
APP_CODE += [
    {
        "code": "1001",
        "message": "The email address or password is not valid",
        "description": "Đăng nhập thất bại"
    },
    {
        "code": "1003",
        "message": "The account is not activated yet",
        "description": "Tài khoản chưa được kích hoạt"
    },
    {
        "code": "1004",
        "message": "There’s no account associated with this email or username. Try another or create a new account",
        "description": "Tài khoản không tồn tại"
    },
    {
        "code": "1005",
        "message": "This user is not a admin account",
        "description": "Tài khoản này không phải là admin"
    },
    {
        "code": "1006",
        "message": "This group is a base group. So, you can not delete it",
        "description": "Group này là một base group nên bạn không thể xóa"
    },
    {
        "code": "1007",
        "message": "Cannot delete this user because it is the sole owner of at least one organization. "
                   "Please delete these organizations",
        "description": "Không thể xóa account này thì account là owner của ít nhất một chương trình. "
                       "Hãy xóa các chương trình mà bạn đã tạo."
    }
]


# ----------------------------- Team error code ----------------------------------#
APP_CODE += [
    {
        "code": "3000",
        "message": "You have reached the limit for the number of teams you can create at this time",
        "vi_message": "Bạn đã tạo tối đa số lượng team ở thời điểm này"
    },
    {
        "code": "3001",
        "message": "Can not create a team at this time. Something went wrong, try again later.",
        "vi_message": "Không thể tạo team tại thời điểm hiện tại. Vui lòng thử lại sau"
    },
    {
        "code": "3002",
        "message": "The maximum number of members is reached. Please upgrade your plan",
        "vi_message": "Số lượng thành viên vượt quá giới hạn cho phép. Vui lòng nâng cấp gói của bạn"
    },
    {
        "code": "3003",
        "message": "This team was locked. Please upgrade your plan",
        "vi_message": "Team này đã bị khóa. Vui lòng nâng cấp gói của bạn để tiếp tục sử dụng"
    },
    {
        "code": "3004",
        "message": "The invitation is expired. Please contact admin to re-invite",
        "vi_message": "Lời mời đã hết hạn. Vui lòng liên hệ admin để được mời lại"
    },

]


# ----------------------------- PM Folder error code ----------------------------------#
APP_CODE += [
    {
        "code": "4000",
        "message": "You can not delete the default team",
        "vi_message": "Bạn không thể xóa thư mực mặc định của teams"
    },
]


# ---------------------------- Cipher ------------------------------------------- #
APP_CODE += [
    {
        "code": "5000",
        "message": "This cipher already belongs to an organization",
        "vi_message": "Bản ghi đã thuộc về một team"
    }
]


# ------------------------------ TRANSACTION --------------------------------#
APP_CODE += [
    {
        "code": "7003",
        "message": "You don't need pay to execute this operator",
        "description": "Bạn không cần trả tiền để thực hiện hành động này"
    },
    {
        "code": "7004",
        "message": "You can not cancel the default plan",
        "description": "Bạn không thể hủy gói mặc định"
    },
    {
        "code": "7005",
        "message": "An unexpected error has occurred when connecting to Stripe",
        "description": "Kết nối tới Stripe đã xảy ra lỗi"
    },
    {
        "code": "7006",
        "message": "This card was existed",
        "description": "Thẻ đã tồn tại"
    },
    {
        "code": "7007",
        "message": "This user doesn't have any card",
        "description": "User chưa có thẻ nào"
    },
    {
        "code": "7008",
        "message": "This user doesn't have any subscription",
        "description": "User chưa đăng ký gói nào"
    },
    {
        "code": "7009",
        "message": "Your card was declined (insufficient funds, etc...) or your balance is not enough",
    },
    {
        "code": "7010",
        "message": "Your current plan is a subscription plan and not support this operator"
    }
]


def get_app_code_content(code):
    try:
        return [content for content in APP_CODE if content["code"] == code][0]['message']
    except (IndexError, KeyError):
        raise Exception("Does not have this app_code")
