# Tính năng Chỉnh sửa thông tin tài khoản

## Tổng quan
Đã bổ sung tính năng cho phép người dùng chỉnh sửa thông tin tài khoản của mình bao gồm:
- Tên và họ
- Tên đăng nhập (username)
- Mật khẩu (tùy chọn)

## Các thành phần đã thêm

### 1. API Routes (server/routes.ts)
- **PATCH /api/auth/user**: Cập nhật thông tin tài khoản hiện tại
  - Yêu cầu xác thực
  - Kiểm tra username không trùng lặp
  - Validate mật khẩu (nếu có)
  - Cập nhật thông tin vào database

### 2. Storage Method (server/storage.ts)
- **updateUser()**: Method mới để cập nhật thông tin user
  - Hỗ trợ cập nhật từng phần thông tin
  - Tự động cập nhật `updatedAt`
  - Logging chi tiết cho debugging

### 3. Components
- **EditProfile.tsx**: Modal form để chỉnh sửa thông tin
  - Form validation
  - Xử lý mật khẩu tùy chọn
  - Hiển thị loading state
  - Toast notifications

- **Profile.tsx**: Trang hiển thị thông tin tài khoản
  - Hiển thị đầy đủ thông tin user
  - Trạng thái tài khoản với badges
  - Nút chỉnh sửa thông tin
  - Thao tác nhanh

### 4. Cập nhật Header
- Thêm menu "Thông tin tài khoản" trong dropdown user
- Link đến trang Profile
- Nút chỉnh sửa thông tin nhanh

### 5. Routing
- **/profile**: Trang thông tin tài khoản
- Tích hợp với hệ thống routing hiện tại

## Cách sử dụng

### 1. Truy cập trang Profile
- Click vào avatar user ở góc phải header
- Chọn "Thông tin tài khoản"
- Hoặc truy cập trực tiếp `/profile`

### 2. Chỉnh sửa thông tin
- Click nút "Chỉnh sửa" trên trang Profile
- Hoặc chọn "Chỉnh sửa thông tin" từ dropdown menu
- Điền thông tin mới
- Click "Cập nhật"

### 3. Thay đổi mật khẩu
- Điền mật khẩu mới (tối thiểu 6 ký tự)
- Xác nhận mật khẩu mới
- Để trống nếu không muốn thay đổi

## Tính năng bảo mật

### 1. Validation
- Kiểm tra username không trùng lặp
- Validate mật khẩu tối thiểu 6 ký tự
- Xác nhận mật khẩu phải khớp

### 2. Quyền truy cập
- Chỉ user đã đăng nhập mới có thể chỉnh sửa
- Chỉ có thể chỉnh sửa thông tin của chính mình
- Admin có thể chỉnh sửa thông tin user khác

### 3. Audit Log
- Log tất cả thay đổi thông tin
- Ghi lại thời gian cập nhật
- Tracking IP và User-Agent

## Cấu trúc dữ liệu

### User Schema
```typescript
interface User {
  id: string;
  user: string;           // Username
  firstName: string;      // Tên
  lastName: string;       // Họ
  password?: string;      // Mật khẩu (optional)
  role: string;           // Vai trò
  status: string;         // Trạng thái
  expiresAt?: Date;       // Thời hạn sử dụng
  createdAt: Date;        // Ngày tạo
  updatedAt: Date;        // Ngày cập nhật
}
```

### Update Request
```typescript
interface UpdateProfileRequest {
  firstName: string;      // Bắt buộc
  lastName: string;       // Bắt buộc
  user: string;           // Bắt buộc
  password?: string;      // Tùy chọn
  confirmPassword?: string; // Bắt buộc nếu có password
}
```

## Xử lý lỗi

### 1. Validation Errors
- **400**: Thiếu thông tin bắt buộc
- **400**: Username đã tồn tại
- **400**: Mật khẩu quá ngắn
- **400**: Mật khẩu không khớp

### 2. Server Errors
- **500**: Lỗi database
- **500**: Lỗi server

### 3. Authentication Errors
- **401**: Chưa đăng nhập
- **403**: Không có quyền truy cập

## Testing

### 1. Test Cases
- [ ] Đăng nhập và truy cập trang Profile
- [ ] Chỉnh sửa tên và họ
- [ ] Thay đổi username (không trùng lặp)
- [ ] Thay đổi mật khẩu
- [ ] Validation mật khẩu
- [ ] Kiểm tra username trùng lặp
- [ ] Test với user chưa có thông tin

### 2. Test Scenarios
- User thường chỉnh sửa thông tin
- Admin chỉnh sửa thông tin user khác
- Validation các trường bắt buộc
- Xử lý lỗi network
- Refresh page sau khi cập nhật

## Deployment

### 1. Backend
- Cập nhật `server/routes.ts`
- Cập nhật `server/storage.ts`
- Restart server

### 2. Frontend
- Build project: `npm run build`
- Deploy các file mới
- Clear cache nếu cần

## Troubleshooting

### 1. Lỗi thường gặp
- **Type mismatch**: Kiểm tra interface UserProfile
- **Route not found**: Kiểm tra App.tsx routing
- **Permission denied**: Kiểm tra authentication middleware

### 2. Debug
- Kiểm tra console logs
- Kiểm tra network requests
- Kiểm tra database queries
- Kiểm tra user permissions

## Tương lai

### 1. Tính năng có thể mở rộng
- Upload avatar
- Thay đổi email
- Two-factor authentication
- Activity log chi tiết
- Export thông tin cá nhân

### 2. Cải tiến
- Real-time validation
- Auto-save
- Version history
- Backup/restore settings
