import { useQuery } from "@tanstack/react-query";
import { LoadingSkeleton } from "@/components/ui/loading";
import { Badge } from "@/components/ui/badge";

export function RecentOrders() {
  const { data: orders, isLoading } = useQuery({
    queryKey: ['/api/orders/recent'],
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <LoadingSkeleton className="h-6 w-32" />
          <LoadingSkeleton className="h-4 w-20" />
        </div>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <LoadingSkeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </div>
    );
  }

  const getServiceName = (serviceType: string) => {
    const names: Record<string, string> = {
      'tra_cuu_ftth': 'FTTH',
      'gach_dien_evn': 'EVN',
      'nap_tien_da_mang': 'Đa mạng',
      'nap_tien_viettel': 'Viettel',
      'thanh_toan_tv_internet': 'TV-Internet',
      'tra_cuu_no_tra_sau': 'Trả sau'
    };
    return names[serviceType] || serviceType;
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: any; label: string }> = {
      'completed': { variant: 'default', label: 'Đã thanh toán' },
      'pending': { variant: 'secondary', label: 'Chưa thanh toán' },
      'processing': { variant: 'outline', label: 'Đang xử lý' },
      'failed': { variant: 'destructive', label: 'Thất bại' }
    };
    const config = statusConfig[status] || { variant: 'secondary', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'vừa xong';
    if (diffInMinutes < 60) return `${diffInMinutes} phút trước`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} giờ trước`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} ngày trước`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Đơn hàng gần đây</h3>
        <a href="#" className="text-sm text-primary hover:text-primary/80 font-medium">
          Xem tất cả
        </a>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dịch vụ</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Số tiền</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trạng thái</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thời gian</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {orders && orders.length > 0 ? (
              orders.map((order: any) => (
                <tr key={order.id}>
                  <td className="px-4 py-3 text-sm font-mono text-gray-900">
                    #{order.id.slice(-6).toUpperCase()}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {getServiceName(order.serviceType)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {order.totalAmount ? `${parseFloat(order.totalAmount).toLocaleString('vi-VN')}đ` : '-'}
                  </td>
                  <td className="px-4 py-3">
                    {getStatusBadge(order.status)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {formatTimeAgo(order.createdAt)}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                  Chưa có đơn hàng nào
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
