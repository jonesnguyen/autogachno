import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loading } from "@/components/ui/loading";
import { Badge } from "@/components/ui/badge";
import { isUnauthorizedError } from "@/lib/authUtils";

interface ServiceContentProps {
  serviceType: string;
}

export function ServiceContent({ serviceType }: ServiceContentProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    codes: '',
    phone: '',
    pin: '',
    amount: '',
    paymentType: ''
  });

  // Get service sample data
  const { data: sampleData } = useQuery({
    queryKey: ['/api/services', serviceType, 'data'],
    enabled: !!serviceType && serviceType.startsWith('tra_cuu') || serviceType.startsWith('gach_') || serviceType.startsWith('nap_') || serviceType.startsWith('thanh_'),
  });

  // Load sample data mutation
  const loadSampleMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('GET', `/api/services/${serviceType}/data`);
      return response.json();
    },
    onSuccess: (data) => {
      if (data.status === 'success') {
        const serviceData = data.data;
        let codes = '';
        
        if (serviceData.subscriber_codes) {
          codes = serviceData.subscriber_codes.join('\n');
        } else if (serviceData.bill_codes) {
          codes = serviceData.bill_codes.join('\n');
        } else if (serviceData.phone_numbers) {
          codes = serviceData.phone_numbers.join('\n');
        }

        setFormData({
          codes,
          phone: serviceData.receiver_phone || '',
          pin: serviceData.pin || '',
          amount: serviceData.amount || '',
          paymentType: serviceData.payment_type || ''
        });
      }
    },
    onError: (error) => {
      if (isUnauthorizedError(error)) {
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
      toast({
        title: "Lỗi",
        description: "Không thể tải dữ liệu mẫu",
        variant: "destructive",
      });
    },
  });

  // Create order mutation
  const createOrderMutation = useMutation({
    mutationFn: async () => {
      const codes = formData.codes.split('\n').filter(code => code.trim());
      const inputData = {
        codes,
        phone: formData.phone,
        pin: formData.pin,
        amount: formData.amount,
        paymentType: formData.paymentType
      };

      const response = await apiRequest('POST', '/api/orders', {
        serviceType,
        inputData: JSON.stringify(inputData),
        status: 'pending'
      });
      return response.json();
    },
    onSuccess: (order) => {
      toast({
        title: "Thành công",
        description: "Đã tạo đơn hàng thành công",
      });
      
      // Start processing
      processingMutation.mutate({ orderId: order.id });
      queryClient.invalidateQueries({ queryKey: ['/api/orders'] });
    },
    onError: (error) => {
      if (isUnauthorizedError(error)) {
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
      toast({
        title: "Lỗi",
        description: "Không thể tạo đơn hàng",
        variant: "destructive",
      });
    },
  });

  // Processing mutation
  const processingMutation = useMutation({
    mutationFn: async ({ orderId }: { orderId: string }) => {
      const response = await apiRequest('POST', `/api/services/${serviceType}/process`, {
        orderId
      });
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Đang xử lý",
        description: "Bắt đầu xử lý dịch vụ",
      });
    },
    onError: (error) => {
      if (isUnauthorizedError(error)) {
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
      toast({
        title: "Lỗi",
        description: "Không thể xử lý dịch vụ",
        variant: "destructive",
      });
    },
  });

  const getServiceTitle = (type: string) => {
    const titles: Record<string, string> = {
      'tra_cuu_ftth': 'Tra cứu FTTH',
      'gach_dien_evn': 'Gạch điện EVN',
      'nap_tien_da_mang': 'Nạp tiền đa mạng',
      'nap_tien_viettel': 'Nạp tiền Viettel',
      'thanh_toan_tv_internet': 'Thanh toán TV-Internet',
      'tra_cuu_no_tra_sau': 'Tra cứu nợ trả sau'
    };
    return titles[type] || type;
  };

  const getInputLabel = (type: string) => {
    const labels: Record<string, string> = {
      'tra_cuu_ftth': 'Danh sách mã thuê bao FTTH',
      'gach_dien_evn': 'Danh sách mã hóa đơn EVN', 
      'nap_tien_da_mang': 'Danh sách số điện thoại',
      'nap_tien_viettel': 'Danh sách số điện thoại Viettel',
      'thanh_toan_tv_internet': 'Danh sách mã thuê bao TV-Internet',
      'tra_cuu_no_tra_sau': 'Danh sách số điện thoại trả sau'
    };
    return labels[type] || 'Danh sách mã';
  };

  const needsPhone = serviceType === 'gach_dien_evn';
  const needsPin = ['gach_dien_evn', 'nap_tien_da_mang', 'nap_tien_viettel', 'thanh_toan_tv_internet'].includes(serviceType);
  const needsAmount = ['nap_tien_da_mang', 'nap_tien_viettel'].includes(serviceType);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Input Form */}
      <div className="lg:col-span-1">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Thông tin {serviceType.includes('tra_cuu') ? 'tra cứu' : 'thanh toán'}
            </h3>
            <Button
              onClick={() => loadSampleMutation.mutate()}
              disabled={loadSampleMutation.isPending}
              size="sm"
              className="bg-primary hover:bg-primary/90"
            >
              {loadSampleMutation.isPending ? (
                <Loading size="sm" className="mr-1" />
              ) : (
                <i className="fas fa-download mr-1"></i>
              )}
              Lấy dữ liệu
            </Button>
          </div>
          
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2">
                {getInputLabel(serviceType)}
              </Label>
              <Textarea
                value={formData.codes}
                onChange={(e) => setFormData({ ...formData, codes: e.target.value })}
                placeholder="Nhập danh sách, mỗi mã một dòng..."
                className="h-32 resize-none text-sm"
              />
            </div>
            
            {needsPhone && (
              <div>
                <Label className="text-sm font-medium text-gray-700 mb-2">
                  Số điện thoại nhận
                </Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="text-sm"
                />
              </div>
            )}
            
            {needsPin && (
              <div>
                <Label className="text-sm font-medium text-gray-700 mb-2">
                  Mã PIN
                </Label>
                <Input
                  type="password"
                  value={formData.pin}
                  onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
                  className="text-sm"
                />
              </div>
            )}

            {needsAmount && (
              <div>
                <Label className="text-sm font-medium text-gray-700 mb-2">
                  Số tiền
                </Label>
                <Input
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="text-sm"
                />
              </div>
            )}
            
            <div className="flex space-x-3">
              <Button
                onClick={() => createOrderMutation.mutate()}
                disabled={createOrderMutation.isPending || !formData.codes.trim()}
                className="flex-1 bg-primary hover:bg-primary/90"
              >
                {createOrderMutation.isPending ? (
                  <Loading size="sm" className="mr-2" />
                ) : (
                  <i className="fas fa-play mr-2"></i>
                )}
                Bắt đầu
              </Button>
              <Button
                disabled
                variant="secondary"
                className="flex-1"
              >
                <i className="fas fa-stop mr-2"></i>
                Dừng
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Results Display */}
      <div className="lg:col-span-2">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Kết quả {serviceType.includes('tra_cuu') ? 'tra cứu' : 'thanh toán'}
            </h3>
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-2 text-sm">
                <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                <span className="text-gray-600">Sẵn sàng</span>
              </div>
              <Button size="sm" className="bg-green-600 hover:bg-green-700">
                <i className="fas fa-file-excel mr-1"></i>
                Xuất Excel
              </Button>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">STT</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {serviceType.includes('hoa_don') ? 'Mã hóa đơn' : 
                     serviceType.includes('phone') || serviceType.includes('tra_sau') ? 'Số điện thoại' : 'Mã thuê bao'}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trạng thái</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Số tiền</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ghi chú</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                    Nhấn "Bắt đầu" để xử lý dịch vụ
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
