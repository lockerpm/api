# Member Notes

## Thêm member

Có các cách mời member sau:

### Mời thông qua email

Có thể thông qua nhập tay email, hoặc upload file lên, hoặc GSuite

- Member được mời có trạng thái là `invited`
- Gửi mail thông báo cho email được mời: báo là tài khoản của bạn được add vào Enterprise
- Khi user đăng nhập vào, sẽ có pop-up (có thể là chỗ banner màn Vault) hiển thị lời mời để đồng ý hoặc từ chối
- Khi user đồng ý, chuyển status thành `confirmed` và có thể sử dụng các tính năng Premium
- User từ chối thì xóa (remove) member này.

### Mời thông qua Domain

Owner thêm một domain và xác thực domain => Domain này thuộc doanh nghiệp

- Ngay khi verify domain xong => Tìm các email tương ứng domain này. 
- Gửi mail thông báo cho các email tương ứng domain rằng tài khoản đã thuộc Enterprise
- Tự động add các user này vào làm member

Có 2 options chọn: Bật/Tắt tự động phê duyệt

- Khi bật tự động phê duyệt => User đăng ký mới với domain tương ứng => Thông báo thuộc Enterprise 
=> Add user vào enterprise
- Khi tắt tự dộng phê duyệt => User đăng ký mới thì tài khoản ko vào được vault ngay mà bị chặn, 
thông báo tài khoản thuộc doanh nghiệp, request để tham gia => Admin confirm => Tài khoản được dùng


## Update role

Primary Admin hoặc Admin có thể update role của member

## Xóa member

- Không được xóa member có mail là domain đã được xác thực
- Với các domain còn lại, xóa khỏi enterprise, đồng thời hạ về bậc Free


## Deactivate member

- Lock member lại, không cho sử dụng nữa
- Member bị locker có thể ko bị tính tiền, cũng như ko dùng được các tính năng
