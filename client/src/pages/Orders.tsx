import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { useEffect } from "react";
import { LoadingSkeleton } from "@/components/ui/loading";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function Orders() {
  const { isAuthenticated, isLoading } = useAuth();
  const { toast } = useToast();

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      toast({
        title: "Unauthorized",
        description: "You are logged out. Logging in again...",
        variant: "destructive",
      });
      setTimeout(() => {
        window.location.href = "/api/login";
      }, 500);
      return;
    }
  }, [isAuthenticated, isLoading, toast]);

  const { data: orders, isLoading: ordersLoading } = useQuery({
    queryKey: ['/api/orders'],
    enabled: isAuthenticated,
  });

  if (isLoading || ordersLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <LoadingSkeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    );
  }

  const getServiceName = (serviceType: string) => {
    const names: Record<string, string> = {
      'tra_cuu_ftth': 'Tra cứu FTTH',
      'gach_dien_evn': 'Gạch điện EVN',
      'nap_tien_da_mang': 'Nạp tiền đa mạng',
      'nap_tien_viettel': 'Nạp tiền Viettel',
      'thanh_toan_tv_internet': 'Thanh toán TV-Internet',
      'tra_cuu_no_tra_sau': 'Tra cứu nợ trả sau'
    };
    return names[serviceType] || serviceType;
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: any; label: string }> = {
      'completed': { variant: 'default', label: 'Hoàn thành' },
      'pending': { variant: 'secondary', label: 'Chờ xử lý' },
      'processing': { variant: 'outline', label: 'Đang xử lý' },
      'failed': { variant: 'destructive', label: 'Thất bại' }
    };
    const config = statusConfig[status] || { variant: 'secondary', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  return (
    <div className="container mx-auto p-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Đơn hàng của tôi</h1>
          <Button className="bg-primary hover:bg-primary/90">
            <i className="fas fa-plus mr-2"></i>
            Tạo đơn mới
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID Đơn hàng
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dịch vụ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trạng thái
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tổng tiền
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ngày tạo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Thao tác
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {orders && orders.length > 0 ? (
                orders.map((order: any) => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      #{order.id.slice(-8).toUpperCase()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {getServiceName(order.serviceType)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(order.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {order.totalAmount ? `${parseFloat(order.totalAmount).toLocaleString('vi-VN')}đ` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(order.createdAt).toLocaleDateString('vi-VN')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline">
                          <i className="fas fa-eye mr-1"></i>
                          Xem
                        </Button>
                        <Button size="sm" variant="outline">
                          <i className="fas fa-download mr-1"></i>
                          Xuất
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    <div className="flex flex-col items-center">
                      <i className="fas fa-inbox text-4xl text-gray-300 mb-4"></i>
                      <p>Bạn chưa có đơn hàng nào</p>
                      <Button className="mt-4 bg-primary hover:bg-primary/90">
                        Tạo đơn hàng đầu tiên
                      </Button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
