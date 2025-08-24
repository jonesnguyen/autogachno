import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EditProfile } from "@/components/EditProfile";
import { ArrowLeft, User, Shield, Calendar, CheckCircle, Clock, XCircle } from "lucide-react";

export default function Profile() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const [, navigate] = useLocation();
  const { toast } = useToast();
  const [showEditForm, setShowEditForm] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      toast({
        title: "Unauthorized",
        description: "Bạn cần đăng nhập để tiếp tục",
        variant: "destructive",
      });
      setTimeout(() => {
        navigate("/login");
      }, 500);
      return;
    }
  }, [isAuthenticated, isLoading, toast, navigate]);

  const handleProfileUpdate = (updatedUser: any) => {
    toast({
      title: "Thành công",
      description: "Thông tin tài khoản đã được cập nhật",
    });
    setShowEditForm(false);
  };

  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'active':
        return { icon: CheckCircle, color: 'bg-green-100 text-green-800', text: 'Đã kích hoạt' };
      case 'pending':
        return { icon: Clock, color: 'bg-yellow-100 text-yellow-800', text: 'Chờ xét duyệt' };
      case 'suspended':
        return { icon: XCircle, color: 'bg-red-100 text-red-800', text: 'Đã tạm khóa' };
      default:
        return { icon: Clock, color: 'bg-gray-100 text-gray-800', text: status };
    }
  };

  const getRoleInfo = (role: string) => {
    switch (role) {
      case 'admin':
        return { color: 'bg-red-100 text-red-800', text: 'Quản trị viên' };
      case 'manager':
        return { color: 'bg-blue-100 text-blue-800', text: 'Quản lý' };
      case 'user':
        return { color: 'bg-green-100 text-green-800', text: 'Người dùng' };
      default:
        return { color: 'bg-gray-100 text-gray-800', text: role };
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-2 text-gray-600">Đang tải...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const StatusIcon = getStatusInfo(user.status).icon;

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/dashboard")}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Quay lại Dashboard
          </Button>
          <h1 className="text-2xl font-bold text-gray-900">Thông tin tài khoản</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Info */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <User className="h-6 w-6 text-blue-600" />
                    <div>
                      <CardTitle>Thông tin cá nhân</CardTitle>
                      <CardDescription>
                        Xem và cập nhật thông tin tài khoản của bạn
                      </CardDescription>
                    </div>
                  </div>
                  <Button
                    onClick={() => setShowEditForm(true)}
                    size="sm"
                  >
                    Chỉnh sửa
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Tên</Label>
                    <p className="text-lg font-medium">{user.firstName || 'Chưa cập nhật'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Họ</Label>
                    <p className="text-lg font-medium">{user.lastName || 'Chưa cập nhật'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Tên đăng nhập</Label>
                    <p className="text-lg font-medium font-mono">{user.user || 'Chưa cập nhật'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">ID</Label>
                    <p className="text-sm font-mono text-gray-600">{user.id}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Account Status */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-lg">Trạng thái tài khoản</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm font-medium text-gray-500">Trạng thái</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <StatusIcon className="h-4 w-4" />
                    <Badge className={getStatusInfo(user.status).color}>
                      {getStatusInfo(user.status).text}
                    </Badge>
                  </div>
                </div>
                
                <div>
                  <Label className="text-sm font-medium text-gray-500">Vai trò</Label>
                  <Badge className={`mt-1 ${getRoleInfo(user.role).color}`}>
                    {getRoleInfo(user.role).text}
                  </Badge>
                </div>

                {user.expiresAt && (
                  <div>
                    <Label className="text-sm font-medium text-gray-500">Thời hạn sử dụng</Label>
                    <div className="flex items-center gap-2 mt-1">
                      <Calendar className="h-4 w-4 text-gray-500" />
                      <p className="text-sm">
                        {new Date(user.expiresAt).toLocaleDateString('vi-VN')}
                      </p>
                    </div>
                  </div>
                )}

                <div>
                  <Label className="text-sm font-medium text-gray-500">Ngày tạo</Label>
                  <p className="text-sm text-gray-600">
                    {user.createdAt ? new Date(user.createdAt).toLocaleDateString('vi-VN') : 'N/A'}
                  </p>
                </div>

                <div>
                  <Label className="text-sm font-medium text-gray-500">Cập nhật lần cuối</Label>
                  <p className="text-sm text-gray-600">
                    {user.updatedAt ? new Date(user.updatedAt).toLocaleDateString('vi-VN') : 'N/A'}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Thao tác nhanh</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  onClick={() => setShowEditForm(true)}
                  className="w-full"
                  variant="outline"
                >
                  <User className="mr-2 h-4 w-4" />
                  Chỉnh sửa thông tin
                </Button>
                
                <Button
                  onClick={() => navigate("/dashboard")}
                  className="w-full"
                  variant="outline"
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Về Dashboard
                </Button>
              </CardContent>
                         </Card>
           </div>
         </div>
         
         
       </div>

      {/* Edit Profile Modal */}
      {showEditForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <EditProfile
            user={user}
            onClose={() => setShowEditForm(false)}
            onUpdate={handleProfileUpdate}
          />
        </div>
      )}
    </div>
  );
}
