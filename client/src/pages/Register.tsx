import { useState } from "react";
import { useLocation } from "wouter";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { UserPlus, ArrowLeft } from "lucide-react";

export default function Register() {
  const [, navigate] = useLocation();
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    user: "",
    firstName: "",
    lastName: "",
    phone: "",
    organization: "",
    requestReason: "",
    password: "",
    confirmPassword: "",
    expiresAt: "" // Thêm trường thời hạn sử dụng
  });

  const registerMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await apiRequest("/api/register", "POST", data);
      return response.json();
    },
    onSuccess: (response) => {
      // Kiểm tra status từ response để hiển thị thông báo phù hợp
      const status = response?.status || 'pending';
      const message = response?.message || "Đăng ký thành công!";
      
      toast({
        title: "Đăng ký thành công",
        description: message,
      });
      
      // Nếu user ở trạng thái pending, hiển thị thông báo rõ ràng hơn
      if (status === 'pending') {
        toast({
          title: "Tài khoản đang chờ xét duyệt",
          description: "Quản trị viên sẽ xem xét và phê duyệt tài khoản của bạn trong thời gian sớm nhất.",
        });
      }
      
      navigate("/");
    },
    onError: (error) => {
      toast({
        title: "Lỗi đăng ký",
        description: error.message || "Có lỗi xảy ra khi đăng ký",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.user || !formData.firstName || !formData.lastName || !formData.password || !formData.confirmPassword) {
      toast({
        title: "Thiếu thông tin",
        description: "Vui lòng điền đầy đủ các trường bắt buộc",
        variant: "destructive",
      });
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast({
        title: "Mật khẩu không khớp",
        description: "Mật khẩu và xác nhận mật khẩu phải giống nhau",
        variant: "destructive",
      });
      return;
    }

    if (formData.password.length < 6) {
      toast({
        title: "Mật khẩu quá ngắn",
        description: "Mật khẩu phải có ít nhất 6 ký tự",
        variant: "destructive",
      });
      return;
    }
    
    registerMutation.mutate(formData);
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center gap-2">
            <UserPlus className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            <CardTitle className="text-2xl">Đăng ký tài khoản</CardTitle>
          </div>
          <CardDescription>
            Điền thông tin để đăng ký sử dụng hệ thống ViettelPay. Tài khoản sẽ được xét duyệt bởi quản trị viên trước khi có thể sử dụng.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <div className="text-blue-600 mt-0.5">ℹ️</div>
              <div className="text-sm text-blue-800">
                <p className="font-medium">Quy trình đăng ký:</p>
                <ol className="list-decimal list-inside mt-1 space-y-1">
                  <li>Điền thông tin và gửi đăng ký</li>
                  <li>Quản trị viên xem xét và phê duyệt</li>
                  <li>Nhận email thông báo kết quả</li>
                  <li>Đăng nhập và sử dụng hệ thống</li>
                </ol>
              </div>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="user">User *</Label>
              <Input
                id="user"
                type="text"
                value={formData.user}
                onChange={(e) => handleInputChange("user", e.target.value)}
                placeholder="Tên đăng nhập"
                required
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">Tên *</Label>
                <Input
                  id="firstName"
                  value={formData.firstName}
                  onChange={(e) => handleInputChange("firstName", e.target.value)}
                  placeholder="Nguyễn"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastName">Họ *</Label>
                <Input
                  id="lastName"
                  value={formData.lastName}
                  onChange={(e) => handleInputChange("lastName", e.target.value)}
                  placeholder="Văn A"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Số điện thoại</Label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) => handleInputChange("phone", e.target.value)}
                placeholder="0987654321"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="organization">Tổ chức</Label>
              <Input
                id="organization"
                value={formData.organization}
                onChange={(e) => handleInputChange("organization", e.target.value)}
                placeholder="Công ty ABC"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="requestReason">Lý do sử dụng</Label>
              <Textarea
                id="requestReason"
                value={formData.requestReason}
                onChange={(e) => handleInputChange("requestReason", e.target.value)}
                placeholder="Mô tả ngắn gọn lý do cần sử dụng hệ thống..."
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="expiresAt">Thời hạn sử dụng (tùy chọn)</Label>
              <Input
                id="expiresAt"
                type="date"
                value={formData.expiresAt}
                onChange={(e) => handleInputChange("expiresAt", e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                placeholder="Chọn ngày hết hạn"
              />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Để trống nếu không có thời hạn cụ thể
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu *</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => handleInputChange("password", e.target.value)}
                placeholder="Nhập mật khẩu (tối thiểu 6 ký tự)"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Xác nhận mật khẩu *</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                placeholder="Nhập lại mật khẩu"
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={registerMutation.isPending}
            >
              {registerMutation.isPending ? "Đang gửi..." : "Đăng ký"}
            </Button>

            <div className="text-center text-sm text-gray-600 dark:text-gray-400 space-y-2">
              <p>⚠️ Lưu ý: Tài khoản của bạn sẽ được xét duyệt trong vòng 24-48 giờ</p>
              <p>Bạn sẽ nhận được email thông báo khi tài khoản được phê duyệt</p>
            </div>

            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={() => navigate("/")}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Quay lại trang chủ
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}