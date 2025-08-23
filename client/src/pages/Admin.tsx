import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { 
  Users, 
  UserCheck, 
  Activity, 
  DollarSign, 
  AlertCircle,
  CheckCircle,
  XCircle,
  Search,
  Settings,
  Calendar,
  Clock
} from "lucide-react";

interface User {
  id: string;
  user: string;
  firstName: string;
  lastName: string;
  password?: string;
  role: string;
  status: string;
  expiresAt?: string | null;
  lastLoginAt: string;
  createdAt: string;
}

interface Registration {
  id: string;
  user: string;
  firstName: string;
  lastName: string;
  password?: string;
  phone?: string;
  organization?: string;
  requestReason?: string;
  status: string;
  createdAt: string;
}

interface AdminStats {
  totalUsers: number;
  activeUsers: number;
  totalOrders: number;
  totalRevenue: string;
  pendingRegistrations: number;
  recentActivity: any[];
}

interface UsersResponse {
  users: User[];
  total: number;
  page: number;
  limit: number;
}

export default function Admin() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [expirationDate, setExpirationDate] = useState("");
  const [showExpirationDialog, setShowExpirationDialog] = useState(false);

  // Fetch admin stats
  const { data: stats } = useQuery<AdminStats>({
    queryKey: ["/api/admin/stats"],
  });

  // Fetch users
  const { data: usersData, isLoading: usersLoading } = useQuery<UsersResponse>({
    queryKey: ["/api/admin/users", currentPage, searchTerm],
    queryFn: async () => {
      const response = await apiRequest(`/api/admin/users?page=${currentPage}&search=${searchTerm}`);
      return response.json();
    },
  });

  // Fetch registrations
  const { data: registrations, isLoading: registrationsLoading } = useQuery<Registration[]>({
    queryKey: ["/api/admin/registrations"],
  });

  // Update user role mutation
  const updateRoleMutation = useMutation({
    mutationFn: async ({ id, role }: { id: string; role: string }) => {
      return apiRequest(`/api/admin/users/${id}/role`, "PATCH", { role });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/admin/users"] });
      toast({ title: "Đã cập nhật vai trò người dùng" });
    },
    onError: (error) => {
      toast({
        title: "Lỗi cập nhật",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Update user status mutation
  const updateStatusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return apiRequest(`/api/admin/users/${id}/status`, "PATCH", { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/admin/users"] });
      toast({ title: "Đã cập nhật trạng thái người dùng" });
    },
    onError: (error) => {
      toast({
        title: "Lỗi cập nhật",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Update user expiration mutation
  const updateExpirationMutation = useMutation({
    mutationFn: async ({ id, expiresAt }: { id: string; expiresAt: string | null }) => {
      console.log('🔄 Frontend: Starting expiration update...', { id, expiresAt });
      
      try {
        const response = await apiRequest(`/api/admin/users/${id}/expiration`, "PATCH", { expiresAt });
        console.log('📡 Frontend: API response received:', response);
        
        // Kiểm tra response status
        if (!response.ok) {
          const errorText = await response.text();
          console.error('❌ Frontend: Response not OK:', response.status, errorText);
          throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 100)}`);
        }
        
        // Kiểm tra content-type
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
          const responseText = await response.text();
          console.error('❌ Frontend: Response is not JSON:', contentType, responseText.substring(0, 200));
          throw new Error(`Expected JSON but got ${contentType}`);
        }
        
        const responseData = await response.json();
        console.log('📄 Frontend: Response data:', responseData);
        
        return responseData;
      } catch (error) {
        console.error('❌ Frontend: Request failed:', error);
        throw error;
      }
    },
    onSuccess: (data) => {
      console.log('✅ Frontend: Update successful, invalidating queries...', data);
      queryClient.invalidateQueries({ queryKey: ["/api/admin/users"] });
      toast({ title: "Đã cập nhật thời hạn sử dụng" });
    },
    onError: (error: any) => {
      console.error('❌ Frontend: Update failed:', error);
      
      let errorMessage = 'Lỗi cập nhật';
      if (error.message.includes('Expected JSON but got')) {
        errorMessage = 'Server trả về dữ liệu không đúng định dạng. Vui lòng thử lại.';
      } else if (error.message.includes('HTTP 500')) {
        errorMessage = 'Lỗi server. Vui lòng kiểm tra console server.';
      } else if (error.message.includes('HTTP 404')) {
        errorMessage = 'API endpoint không tìm thấy. Vui lòng kiểm tra server.';
      } else if (error.message.includes('HTTP 403')) {
        errorMessage = 'Không có quyền truy cập. Vui lòng đăng nhập lại.';
      }
      
      toast({
        title: "Lỗi cập nhật",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });

  // Review registration mutation
  const reviewRegistrationMutation = useMutation({
    mutationFn: async ({ id, approved, notes }: { id: string; approved: boolean; notes?: string }) => {
      return apiRequest(`/api/admin/registrations/${id}/review`, "PATCH", { approved, notes });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/admin/registrations"] });
      queryClient.invalidateQueries({ queryKey: ["/api/admin/stats"] });
      toast({ title: "Đã xử lý yêu cầu đăng ký" });
    },
    onError: (error) => {
      toast({
        title: "Lỗi xử lý",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'manager': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default: return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'suspended': return 'bg-red-100 text-red-800 dark:bg-green-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const openExpirationDialog = (user: User) => {
    setEditingUser(user);
    setExpirationDate(user.expiresAt ? user.expiresAt.split('T')[0] : '');
    setShowExpirationDialog(true);
  };

  const closeExpirationDialog = () => {
    setShowExpirationDialog(false);
    setEditingUser(null);
    setExpirationDate('');
  };

  const handleUpdateExpiration = () => {
    if (!editingUser) return;
    
    const expiresAt = expirationDate ? new Date(expirationDate).toISOString() : null;
    updateExpirationMutation.mutate({ 
      id: editingUser.id, 
      expiresAt 
    });
    closeExpirationDialog();
  };

  const formatExpirationDate = (expiresAt: string | null | undefined) => {
    if (!expiresAt) return 'Không có thời hạn';
    const date = new Date(expiresAt);
    const now = new Date();
    
    if (date < now) {
      return <span className="text-red-600 font-medium">Đã hết hạn ({date.toLocaleDateString('vi-VN')})</span>;
    }
    
    return date.toLocaleDateString('vi-VN');
  };

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Quản trị hệ thống</h2>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tổng người dùng</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalUsers}</div>
              <p className="text-xs text-muted-foreground">
                {stats.activeUsers} đang hoạt động
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tổng đơn hàng</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalOrders}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tổng doanh thu</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalRevenue}đ</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Chờ phê duyệt</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.pendingRegistrations}</div>
              <p className="text-xs text-muted-foreground">
                yêu cầu đăng ký
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="users" className="space-y-4">
        <TabsList>
          <TabsTrigger value="users">Quản lý người dùng</TabsTrigger>
          <TabsTrigger value="registrations">Đăng ký chờ duyệt</TabsTrigger>
          <TabsTrigger value="settings">Cài đặt</TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Người dùng hệ thống</CardTitle>
              <CardDescription>
                Quản lý tài khoản, phân quyền và thời hạn sử dụng của người dùng
              </CardDescription>
              <div className="flex items-center space-x-2">
                <Search className="h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Tìm kiếm theo tên, username..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
              </div>
            </CardHeader>
            <CardContent>
              {usersLoading ? (
                <div>Đang tải...</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>STT</TableHead>
                      <TableHead>Tên</TableHead>
                      <TableHead>Mật khẩu</TableHead>
                      <TableHead>Vai trò</TableHead>
                      <TableHead>Trạng thái</TableHead>
                      <TableHead>Thời hạn sử dụng</TableHead>
                      <TableHead>Thao tác</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {usersData?.users?.map((user: User, index: number) => (
                      <TableRow key={user.id}>
                        <TableCell className="font-medium">{index + 1}</TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{user.firstName} {user.lastName}</div>
                            <div className="text-sm text-gray-500">@{user.user}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                              {user.password || '••••••'}
                            </span>
                            {/* <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                // Có thể thêm chức năng reset password ở đây
                                toast({
                                  title: "Chức năng đang phát triển",
                                  description: "Reset mật khẩu sẽ được thêm sau",
                                });
                              }}
                              className="h-6 px-2"
                            >
                              <Settings className="h-3 w-3" />
                            </Button> */}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getRoleBadgeColor(user.role)}>
                            {user.role === 'admin' ? 'Quản trị viên' : 
                             user.role === 'manager' ? 'Quản lý' : 'Người dùng'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusBadgeColor(user.status)}>
                            {user.status === 'active' ? 'Hoạt động' :
                             user.status === 'suspended' ? 'Tạm khóa' : 'Chờ duyệt'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <span>{formatExpirationDate(user.expiresAt)}</span>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openExpirationDialog(user)}
                              className="h-6 px-2"
                            >
                              <Settings className="h-3 w-3" />
                            </Button>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Select
                              value={user.role}
                              onValueChange={(role) => updateRoleMutation.mutate({ id: user.id, role })}
                            >
                              <SelectTrigger className="w-24">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="user">User</SelectItem>
                                <SelectItem value="manager">Manager</SelectItem>
                                <SelectItem value="admin">Admin</SelectItem>
                              </SelectContent>
                            </Select>
                            
                            <Select
                              value={user.status}
                              onValueChange={(status) => updateStatusMutation.mutate({ id: user.id, status })}
                            >
                              <SelectTrigger className="w-24">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="active">Active</SelectItem>
                                <SelectItem value="suspended">Suspended</SelectItem>
                                <SelectItem value="pending">Pending</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="registrations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Yêu cầu đăng ký</CardTitle>
              <CardDescription>
                Phê duyệt hoặc từ chối các yêu cầu đăng ký tài khoản mới
              </CardDescription>
            </CardHeader>
            <CardContent>
              {registrationsLoading ? (
                <div>Đang tải...</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>STT</TableHead>
                      <TableHead>Tên</TableHead>
                      <TableHead>Tổ chức</TableHead>
                      <TableHead>Lý do</TableHead>
                      <TableHead>Ngày đăng ký</TableHead>
                      <TableHead>Thao tác</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {registrations?.filter(r => r.status === 'pending').map((registration, index) => (
                      <TableRow key={registration.id}>
                        <TableCell className="font-medium">{index + 1}</TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{registration.firstName} {registration.lastName}</div>
                            <div className="text-sm text-gray-500">@{registration.user}</div>
                          </div>
                        </TableCell>
                        <TableCell>{registration.organization || '-'}</TableCell>
                        <TableCell className="max-w-xs truncate">
                          {registration.requestReason || '-'}
                        </TableCell>
                        <TableCell>
                          {new Date(registration.createdAt).toLocaleDateString('vi-VN')}
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => reviewRegistrationMutation.mutate({ 
                                id: registration.id, 
                                approved: true 
                              })}
                              disabled={reviewRegistrationMutation.isPending}
                            >
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => reviewRegistrationMutation.mutate({ 
                                id: registration.id, 
                                approved: false 
                              })}
                              disabled={reviewRegistrationMutation.isPending}
                            >
                              <XCircle className="h-4 w-4 text-red-600" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cài đặt hệ thống</CardTitle>
              <CardDescription>
                Cấu hình các thông số hệ thống
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center h-32 text-muted-foreground">
                <Settings className="h-8 w-8 mr-2" />
                Tính năng cài đặt đang được phát triển
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Expiration Edit Dialog */}
      {showExpirationDialog && editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Chỉnh sửa thời hạn sử dụng</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={closeExpirationDialog}
                className="h-8 w-8 p-0"
              >
                ×
              </Button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Người dùng
                </label>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                  <div className="font-medium">{editingUser.user}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {editingUser.firstName} {editingUser.lastName}
                  </div>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">
                  Thời hạn sử dụng
                </label>
                <div className="flex items-center space-x-2">
                  <Input
                    type="date"
                    value={expirationDate}
                    onChange={(e) => setExpirationDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExpirationDate('')}
                    className="px-3"
                  >
                    <Clock className="h-4 w-4 mr-1" />
                    Không hạn
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Để trống hoặc chọn "Không hạn" để user không bao giờ hết hạn
                </p>
              </div>
              
              <div className="flex space-x-2 pt-4">
                <Button
                  onClick={handleUpdateExpiration}
                  disabled={updateExpirationMutation.isPending}
                  className="flex-1"
                >
                  {updateExpirationMutation.isPending ? "Đang cập nhật..." : "Cập nhật"}
                </Button>
                <Button
                  variant="outline"
                  onClick={closeExpirationDialog}
                  className="flex-1"
                >
                  Hủy
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}