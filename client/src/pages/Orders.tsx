import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { useEffect, useState } from "react";
import { LoadingSkeleton } from "@/components/ui/loading";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function Orders() {
  const { isAuthenticated, isLoading } = useAuth();
  const { toast } = useToast();
  const [loadingServices, setLoadingServices] = useState<Record<string, boolean>>({});

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

  // Đảm bảo orders là array
  const ordersArray = Array.isArray(orders) ? orders : [];

  // Hàm gọi API get dữ liệu cho từng dịch vụ
  const handleGetData = async (serviceType: string, usePublicApi: boolean = false) => {
    const loadingKey = `${serviceType}_${usePublicApi ? 'public' : 'private'}`;
    setLoadingServices(prev => ({ ...prev, [loadingKey]: true }));

    try {
      // Gọi API local - có thể chọn private hoặc public
      const endpoint = usePublicApi 
        ? `/api/public/services/${serviceType}/data`
        : `/api/services/${serviceType}/data`;
        
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const dataSource = usePublicApi ? 'Public API (DB)' : 'Private API (Mock)';
        toast({
          title: "Thành công",
          description: `Đã lấy dữ liệu từ ${dataSource} cho ${getServiceName(serviceType)}: ${data.data ? Object.keys(data.data).length : 0} fields`,
          variant: "default",
        });
        
        // Log dữ liệu để debug
        console.log(`Data for ${serviceType} from ${dataSource}:`, data);
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error(`Error fetching data for ${serviceType}:`, error);
      toast({
        title: "Lỗi",
        description: `Không thể lấy dữ liệu cho ${getServiceName(serviceType)}: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: "destructive",
      });
    } finally {
      setLoadingServices(prev => ({ ...prev, [loadingKey]: false }));
    }
  };

  // Hàm đánh dấu bill hoàn thành - sử dụng API local
  const handleMarkCompleted = async (orderId: string) => {
    try {
      // Gọi API local để đánh dấu hoàn thành
      const response = await fetch(`/api/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: 'completed' }),
      });

      if (response.ok) {
        toast({
          title: "Thành công",
          description: `Đã đánh dấu hoàn thành cho đơn hàng #${orderId.slice(-8).toUpperCase()}`,
          variant: "default",
        });
        
        // Refresh data
        window.location.reload();
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error marking order completed:', error);
      toast({
        title: "Lỗi",
        description: `Không thể đánh dấu hoàn thành: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: "destructive",
      });
    }
  };

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

  // Kiểm tra mỗi dòng = 1 đơn hàng (như FTTH)
  const validateOrderStructure = (orders: any[]) => {
    const issues: string[] = [];
    
    orders.forEach((order, index) => {
      // Kiểm tra mỗi order có đầy đủ thông tin cần thiết
      if (!order.id) {
        issues.push(`Order ${index + 1}: Thiếu Order ID`);
      }
      if (!order.serviceType) {
        issues.push(`Order ${index + 1}: Thiếu loại dịch vụ`);
      }
      if (!order.status) {
        issues.push(`Order ${index + 1}: Thiếu trạng thái`);
      }
    });
    
    return issues;
  };

  // Hiển thị Order ID mapping như FTTH
  const renderOrderIdMapping = () => {
    if (ordersArray.length === 0) return null;
    
    return (
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          📋 Order ID Mapping (Mỗi dòng = 1 đơn hàng)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {ordersArray.map((order: any, index: number) => (
            <div key={order.id} className="flex items-center space-x-2 p-2 bg-white rounded border">
              <span className="text-sm font-mono text-blue-600">
                {order.id ? `#${order.id.slice(-8).toUpperCase()}` : 'N/A'}
              </span>
              <span className="text-gray-500">→</span>
              <span className="text-sm text-gray-700">
                {getServiceName(order.serviceType)}
              </span>
              <span className="text-xs text-gray-400">
                ({index + 1}/{ordersArray.length})
              </span>
            </div>
          ))}
        </div>
        <div className="mt-3 text-sm text-blue-700">
          💡 <strong>Strategy:</strong> Mỗi dòng = 1 đơn hàng riêng biệt (như FTTH)
        </div>
      </div>
    );
  };

  // Hiển thị nút Get dữ liệu cho từng dịch vụ
  const renderServiceDataButtons = () => {
    const serviceTypes = [
      'tra_cuu_ftth',
      'gach_dien_evn', 
      'nap_tien_da_mang',
      'nap_tien_viettel',
      'thanh_toan_tv_internet',
      'tra_cuu_no_tra_sau'
    ];

    return (
      <div className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
        <h3 className="text-lg font-semibold text-purple-900 mb-3">
          �� Get Dữ liệu từ API Local
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {serviceTypes.map((serviceType) => (
            <div key={serviceType} className="flex flex-col space-y-3 p-3 bg-white rounded-lg border border-purple-200">
              <h4 className="font-medium text-purple-800 text-center text-sm">
                {getServiceName(serviceType)}
              </h4>
              
              {/* Nút Private API (Mock Data) */}
              <Button
                onClick={() => handleGetData(serviceType, false)}
                disabled={loadingServices[`${serviceType}_private`]}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white text-xs"
                size="sm"
              >
                {loadingServices[`${serviceType}_private`] ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                    <span>Đang tải...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <i className="fas fa-database"></i>
                    <span>Mock Data</span>
                  </div>
                )}
              </Button>

              {/* Nút Public API (DB Data) */}
              <Button
                onClick={() => handleGetData(serviceType, true)}
                disabled={loadingServices[`${serviceType}_public`]}
                className="w-full bg-green-600 hover:bg-green-700 text-white text-xs"
                size="sm"
              >
                {loadingServices[`${serviceType}_public`] ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                    <span>Đang tải...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <i className="fas fa-server"></i>
                    <span>DB Data</span>
                  </div>
                )}
              </Button>

              <div className="text-xs text-gray-500 text-center space-y-1">
                <div>Private: /api/services/{serviceType}/data</div>
                <div>Public: /api/public/services/{serviceType}/data</div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 text-sm text-purple-700">
          💡 <strong>Private API:</strong> Mock data | <strong>Public API:</strong> Real data từ Database
        </div>
      </div>
    );
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

        {/* Hiển thị nút Get dữ liệu cho từng dịch vụ */}
        {renderServiceDataButtons()}

        {/* Hiển thị Order ID Mapping như FTTH */}
        {renderOrderIdMapping()}

        {/* Validation mỗi dòng = 1 đơn hàng */}
        {(() => {
          const validationIssues = validateOrderStructure(ordersArray);
          if (validationIssues.length > 0) {
            return (
              <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h3 className="text-lg font-semibold text-yellow-900 mb-3">
                  ⚠️ Validation Issues (Mỗi dòng = 1 đơn hàng)
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {validationIssues.map((issue, index) => (
                    <li key={index} className="text-sm text-yellow-700">{issue}</li>
                  ))}
                </ul>
                <div className="mt-3 text-sm text-yellow-700">
                  💡 <strong>Strategy:</strong> Cần đảm bảo mỗi dòng = 1 đơn hàng riêng biệt (như FTTH)
                </div>
              </div>
            );
          }
          return null;
        })()}

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
              {ordersArray.length > 0 ? (
                ordersArray.map((order: any, index: number) => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      <div className="flex flex-col">
                        <span className="font-bold">#{order.id.slice(-8).toUpperCase()}</span>
                        <span className="text-xs text-gray-500">Dòng {index + 1}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex flex-col">
                        <span>{getServiceName(order.serviceType)}</span>
                        <span className="text-xs text-blue-600">
                          💡 Mỗi dòng = 1 đơn hàng
                        </span>
                      </div>
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
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleMarkCompleted(order.id)}
                          className="text-green-600 hover:text-green-700"
                        >
                          <i className="fas fa-check mr-1"></i>
                          Hoàn thành
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

        {/* Summary về strategy mỗi dòng = 1 đơn hàng */}
        {ordersArray.length > 0 && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-lg font-semibold text-green-900 mb-3">
              ✅ Database Strategy Summary
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-green-800 mb-2">📊 Tổng quan:</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• Tổng số đơn hàng: <strong>{ordersArray.length}</strong></li>
                  <li>• Mỗi dòng = 1 đơn hàng riêng biệt</li>
                  <li>• Mỗi đơn có Order ID riêng</li>
                  <li>• Strategy tương tự như FTTH</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-green-800 mb-2">💡 Strategy:</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• Mỗi dòng = 1 đơn hàng</li>
                  <li>• Mỗi mã = 1 Order ID riêng</li>
                  <li>• Database update chính xác</li>
                  <li>• Không có fallback</li>
                </ul>
              </div>
            </div>
            <div className="mt-3 text-sm text-green-700">
              🎯 <strong>Kết quả:</strong> Đảm bảo mỗi dòng = 1 đơn hàng được lưu vào database chính xác
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
