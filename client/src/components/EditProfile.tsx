import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { User, Edit3, Save, X } from "lucide-react";

interface UserProfile {
  id: string;
  user: string | null;
  firstName: string | null;
  lastName: string | null;
  password?: string | null;
  role: string;
  status: string;
  expiresAt?: string | Date | null;
}

interface EditProfileProps {
  user: UserProfile;
  onClose: () => void;
  onUpdate: (updatedUser: UserProfile) => void;
}

export function EditProfile({ user, onClose, onUpdate }: EditProfileProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    firstName: user.firstName || "",
    lastName: user.lastName || "",
    user: user.user || "",
    password: "",
    confirmPassword: ""
  });

  const updateProfileMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      console.log('🔄 Sending profile update request:', data);
      
      try {
        const response = await apiRequest("/api/auth/user", "PATCH", data);
        console.log('📡 Response status:', response.status);
        console.log('📡 Response headers:', response.headers);
        
        const responseData = await response.json();
        console.log('✅ Response data:', responseData);
        return responseData;
      } catch (error) {
        console.error('❌ Error in profile update:', error);
        if (error instanceof Error) {
          throw error;
        }
        throw new Error('Unknown error occurred');
      }
    },
    onSuccess: (response) => {
      console.log('🎉 Profile update successful:', response);
      toast({
        title: "Thành công",
        description: response.message || "Cập nhật thông tin thành công",
      });
      
      // Update local user data
      const updatedUser = {
        ...user,
        firstName: formData.firstName,
        lastName: formData.lastName,
        user: formData.user
      };
      
      onUpdate(updatedUser);
      onClose();
      
      // Invalidate and refetch user data
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
    onError: (error: any) => {
      console.error('💥 Profile update error:', error);
      toast({
        title: "Lỗi cập nhật",
        description: error.message || "Có lỗi xảy ra khi cập nhật thông tin",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.firstName || !formData.lastName || !formData.user) {
      toast({
        title: "Thiếu thông tin",
        description: "Vui lòng điền đầy đủ các trường bắt buộc",
        variant: "destructive",
      });
      return;
    }

    if (formData.password && formData.password.length < 6) {
      toast({
        title: "Mật khẩu quá ngắn",
        description: "Mật khẩu phải có ít nhất 6 ký tự",
        variant: "destructive",
      });
      return;
    }

    if (formData.password && formData.password !== formData.confirmPassword) {
      toast({
        title: "Mật khẩu không khớp",
        description: "Mật khẩu và xác nhận mật khẩu phải giống nhau",
        variant: "destructive",
      });
      return;
    }
    
    updateProfileMutation.mutate(formData);
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="space-y-1">
        <div className="flex items-center gap-2">
          <Edit3 className="h-6 w-6 text-blue-600" />
          <CardTitle className="text-xl">Chỉnh sửa thông tin</CardTitle>
        </div>
        <CardDescription>
          Cập nhật thông tin cá nhân và mật khẩu của bạn
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
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
            <Label htmlFor="user">Tên đăng nhập *</Label>
            <Input
              id="user"
              value={formData.user}
              onChange={(e) => handleInputChange("user", e.target.value)}
              placeholder="username"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Mật khẩu mới (tùy chọn)</Label>
            <Input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => handleInputChange("password", e.target.value)}
              placeholder="Để trống nếu không đổi mật khẩu"
            />
            <p className="text-sm text-gray-500">
              Chỉ điền nếu muốn thay đổi mật khẩu
            </p>
          </div>

          {formData.password && (
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Xác nhận mật khẩu mới</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                placeholder="Nhập lại mật khẩu mới"
              />
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button
              type="submit"
              className="flex-1"
              disabled={updateProfileMutation.isPending}
            >
              {updateProfileMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Đang cập nhật...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Cập nhật
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={updateProfileMutation.isPending}
            >
              <X className="mr-2 h-4 w-4" />
              Hủy
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
