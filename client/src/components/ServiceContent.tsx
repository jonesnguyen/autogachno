import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/hooks/useAuth";
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
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    codes: '',
    phone: '',
    pin: '',
    amount: '',
    paymentType: ''
  });
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(5);

  // Get service sample data
  const { data: sampleData } = useQuery({
    queryKey: ['/api/services', serviceType, 'data'],
    enabled:
      !!serviceType &&
      (serviceType.startsWith('tra_cuu') ||
        serviceType.startsWith('gach_') ||
        serviceType.startsWith('nap_') ||
        serviceType.startsWith('thanh_')),
  });

  // Load paginated transactions for current service, poll every 10s
  const { data: txPage } = useQuery<any>({
    queryKey: ['/api/transactions', serviceType, page, limit],
    queryFn: async () => {
      const res = await fetch(`/api/transactions?serviceType=${serviceType}&page=${page}&limit=${limit}`, { credentials: 'include' });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    refetchInterval: 10000,
  });

  // Load sample data mutation (from external API thuhohpk.com ONLY - NO LOCAL API)
  const loadSampleMutation = useMutation({
    mutationFn: async () => {
      const mapping: Record<string, string> = {
        tra_cuu_ftth: "check_ftth",
        gach_dien_evn: "env",
        nap_tien_da_mang: "deposit",
        nap_tien_viettel: "deposit_viettel",
        thanh_toan_tv_internet: "payment_tv",
        tra_cuu_no_tra_sau: "check_debt"
      };

      const apiServiceType = mapping[serviceType] || serviceType;
      const url = `http://localhost:3000/api/list-bill-not-completed?service_type=${apiServiceType}`;
      
      // Lấy thông tin đăng nhập từ user hiện tại
      if (!user?.user || !user?.password) {
        throw new Error("Không thể lấy thông tin đăng nhập. Vui lòng đăng nhập lại.");
      }
      
      const username = user.user;
      const password = user.password;
      
      console.log("🔐 Using credentials:", { username, password: password ? "***" : "NOT_FOUND" });

      try {
        console.log("📡 Calling Flask API:", url);
        console.log("🔐 Using credentials:", { username, password: "***" });
        
        const res = await fetch(url, {
          method: 'GET',
          headers: {
            "Token": "c0d2e27448f511b41dd1477781025053",
            "Content-Type": "application/json",
            // Truyền thông tin đăng nhập qua headers
            "X-Username": username,
            "X-Password": password
          }
        });

        console.log("✅ Status:", res.status);
        
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${await res.text()}`);
        }

        const data = await res.json();
        console.log("📄 Response:", data);
        return data;

      } catch (err) {
        console.error("❌ API error:", err);
        throw err;
      }
    },
    onSuccess: (data) => {
      // copy logic parse giống test_api.py
      let codes: string[] = [];
      if (data?.data) {
        if (typeof data.data === "string") {
          codes = data.data.split(",").map((c: string) => c.trim()).filter(Boolean);
        } else if (Array.isArray(data.data)) {
          codes = data.data.map((x: any) => (typeof x === "string" ? x : x.code || x.phone || x.account || x.bill_code)).filter(Boolean);
        }
      } else if (Array.isArray(data)) {
        codes = data.map((x: any) => (typeof x === "string" ? x : x.code || x.phone || x.account || x.bill_code)).filter(Boolean);
      }

      setFormData(f => ({ ...f, codes: codes.join("\n") }));
      toast({
        title: "Đã tải dữ liệu",
        description: `Nhận được ${codes.length} mã từ API`,
      });
    },
    onError: (error) => {
      console.error("💥 Mutation error:", error);
      
      let errorMessage = "Không thể tải dữ liệu từ API";
      
      if (error instanceof Error) {
        if (error.message.includes("Failed to fetch")) {
          errorMessage = "Network error - Không thể kết nối đến API localhost:3000";
        } else if (error.message.includes("HTTP")) {
          errorMessage = `HTTP Error: ${error.message}`;
        } else {
          errorMessage = error.message;
        }
      }
      
      toast({
        title: "Lỗi",
        description: errorMessage,
        variant: "destructive"
      });
    }
  });

// Create order mutation (save only) - Updated with API validation
const createOrderMutation = useMutation({
  mutationFn: async () => {
    const inputCodes = formData.codes.split('\n').filter(code => code.trim());
    
    if (inputCodes.length === 0) {
      throw new Error('Vui lòng nhập ít nhất một mã');
    }

    // Loại bỏ trùng lặp trong danh sách nhập vào
    const uniqueInputCodes = [...new Set(inputCodes.map(code => code.trim()))];
    const removedDuplicates = inputCodes.length - uniqueInputCodes.length;
    
    if (removedDuplicates > 0) {
      console.log(`Đã loại bỏ ${removedDuplicates} mã trùng lặp trong danh sách nhập`);
    }

    // Kiểm tra với dữ liệu từ API thuhohpk.com
    let finalCodes = uniqueInputCodes;
    let invalidCodes: string[] = [];
    
    // Lấy dữ liệu từ API để so sánh
    try {
      const mapping: Record<string, string> = {
        tra_cuu_ftth: "check_ftth",
        gach_dien_evn: "env", 
        nap_tien_da_mang: "deposit",
        nap_tien_viettel: "deposit_viettel",
        thanh_toan_tv_internet: "payment_tv",
        tra_cuu_no_tra_sau: "check_debt"
      };
      
      const apiServiceType = mapping[serviceType] || serviceType;
      const url = `http://localhost:3000/api/list-bill-not-completed?service_type=${apiServiceType}`;
      
      if (!user?.user || !user?.password) {
        throw new Error("Không thể lấy thông tin đăng nhập. Vui lòng đăng nhập lại.");
      }
      
      const username = user.user;
      const password = user.password;
      
      const apiResponse = await fetch(url, {
        method: 'GET',
        headers: {
          "Token": "c0d2e27448f511b41dd1477781025053",
          "Content-Type": "application/json",
          "X-Username": username,
          "X-Password": password
        }
      });

      if (apiResponse.ok) {
        const apiData = await apiResponse.json();
        
        // Parse API data giống logic trong loadSampleMutation
        let validApiCodes: string[] = [];
        if (apiData?.data) {
          if (typeof apiData.data === "string") {
            validApiCodes = apiData.data.split(",").map((c: string) => c.trim()).filter(Boolean);
          } else if (Array.isArray(apiData.data)) {
            validApiCodes = apiData.data.map((x: any) => (typeof x === "string" ? x : x.code || x.phone || x.account || x.bill_code)).filter(Boolean);
          }
        } else if (Array.isArray(apiData)) {
          validApiCodes = apiData.map((x: any) => (typeof x === "string" ? x : x.code || x.phone || x.account || x.bill_code)).filter(Boolean);
        }
        
        console.log(`Nhận được ${validApiCodes.length} mã hợp lệ từ API`);
        
        // Kiểm tra từng mã nhập vào có trong danh sách API không
        finalCodes = [];
        invalidCodes = [];
        
        for (const inputCode of uniqueInputCodes) {
          if (validApiCodes.includes(inputCode)) {
            finalCodes.push(inputCode);
          } else {
            invalidCodes.push(inputCode);
          }
        }
        
        if (invalidCodes.length > 0) {
          console.log(`Phát hiện ${invalidCodes.length} mã không hợp lệ:`, invalidCodes);
          
          // Hiển thị thông báo về mã không hợp lệ
          toast({
            title: "Phát hiện mã không hợp lệ",
            description: `${invalidCodes.length} mã không có trong danh sách API: ${invalidCodes.slice(0, 3).join(', ')}${invalidCodes.length > 3 ? '...' : ''}`,
            variant: "destructive",
          });
        }
        
      } else {
        throw new Error(`Không thể lấy dữ liệu từ API: HTTP ${apiResponse.status}`);
      }
    } catch (error) {
      console.error('Lỗi khi kiểm tra với API:', error);
      throw new Error(`Không thể xác thực dữ liệu với API: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    // Nếu không có mã hợp lệ nào
    if (finalCodes.length === 0) {
      throw new Error('Không có mã nào hợp lệ trong danh sách. Vui lòng kiểm tra lại dữ liệu từ API.');
    }
    
    // Validate multi-network data cho các mã còn lại
    if (isMultiNetwork) {
      if (formData.paymentType === 'prepaid') {
        // Nạp trả trước: chỉ cần số điện thoại
        const invalidCodes = [];
        
        for (const code of finalCodes) {
          if (code.includes('|')) {
            invalidCodes.push(`${code} - Sai định dạng (nạp trả trước chỉ cần số điện thoại)`);
          }
        }
        
        if (invalidCodes.length > 0) {
          throw new Error(`Dữ liệu không hợp lệ:\n${invalidCodes.join('\n')}`);
        }
      } else if (formData.paymentType === 'postpaid') {
        // Gạch nợ trả sau: phải có format sđt|số tiền
        const validAmounts = [10000, 20000, 30000, 50000, 100000, 200000, 300000, 500000];
        const invalidCodes = [];
        
        for (const code of finalCodes) {
          const parts = code.split('|');
          if (parts.length !== 2) {
            invalidCodes.push(`${code} - Sai định dạng (gạch nợ trả sau cần: sđt|số tiền)`);
            continue;
          }
          
          const amount = parseInt(parts[1]);
          if (!validAmounts.includes(amount)) {
            invalidCodes.push(`${code} - Số tiền ${amount} không hợp lệ (chỉ cho phép: ${validAmounts.join(', ')})`);
          }
        }
        
        if (invalidCodes.length > 0) {
          throw new Error(`Dữ liệu không hợp lệ:\n${invalidCodes.join('\n')}`);
        }
      } else if (!formData.paymentType) {
        throw new Error('Vui lòng chọn loại dịch vụ (Nạp trả trước hoặc Gạch nợ trả sau)');
      }
    }
    
    const inputData = {
      codes: finalCodes, // Sử dụng danh sách đã lọc trùng lặp
      phone: serviceType === 'gach_dien_evn' ? '' : formData.phone,
      pin: '',
      amount: (serviceType === 'gach_dien_evn' || serviceType === 'nap_tien_viettel') ? '' : formData.amount,
      paymentType: formData.paymentType
    };

    const response = await apiRequest('POST', '/api/orders', {
      serviceType,
      inputData: JSON.stringify(inputData),
      status: 'pending'
    });
    
    const result = await response.json();
    
    // Thêm thông tin về validation checking vào kết quả
    result.validationInfo = {
      originalCount: inputCodes.length,
      uniqueInputCount: uniqueInputCodes.length,
      removedInputDuplicates: removedDuplicates,
      invalidCodesCount: invalidCodes.length,
      finalProcessedCount: finalCodes.length
    };
    
    return result;
  },
  onSuccess: (order) => {
    const info = order.validationInfo || {};
    
    let description = `Đã lưu thành công ${info.finalProcessedCount || 'các'} mã vào hệ thống.`;
    
    if (info.removedInputDuplicates > 0 || info.invalidCodesCount > 0) {
      const details = [];
      if (info.removedInputDuplicates > 0) {
        details.push(`${info.removedInputDuplicates} mã trùng trong danh sách`);
      }
      if (info.invalidCodesCount > 0) {
        details.push(`${info.invalidCodesCount} mã không có trong API`);
      }
      description += ` Đã bỏ qua: ${details.join(', ')}.`;
    }
    
    description += ' Bot sẽ tự động xử lý.';
    
    toast({
      title: "Đã lưu danh sách",
      description,
    });
    
    // Refresh list
    queryClient.invalidateQueries({ queryKey: ['/api/transactions', serviceType] });
    
    // Clear form nếu thành công
    setFormData(prev => ({ ...prev, codes: '' }));
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
    
    let errorMessage = "Không thể tạo đơn hàng";
    if (error instanceof Error) {
      errorMessage = error.message;
    }
    
    toast({
      title: "Lỗi",
      description: errorMessage,
      variant: "destructive",
    });
  },
});

  // Remove manual processing; automation cron will pick up pending orders

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

  const needsPhone = false; // Gạch điện EVN không cần số điện thoại nhận
  const needsPin = false; // Không cần mã PIN cho bất kỳ dịch vụ nào
  const needsAmount = false; // Không cần số tiền cho bất kỳ dịch vụ nào
  const isMultiNetwork = serviceType === 'nap_tien_da_mang';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Input Form */}
      <div className="lg:col-span-1">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Thông tin {serviceType.includes('tra_cuu') ? 'tra cứu' : 'thanh toán'}
            </h3>
            <div className="flex gap-2">
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
          </div>
          
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2">
                {getInputLabel(serviceType)}
              </Label>
              <Textarea
                value={formData.codes}
                onChange={(e) => setFormData({ ...formData, codes: e.target.value })}
                placeholder={
                  isMultiNetwork && formData.paymentType === 'prepaid' 
                    ? 'Nhập: danh sách số điện thoại (VD: 0329880000)'
                    : isMultiNetwork && formData.paymentType === 'postpaid'
                    ? 'Nhập: sđt|số tiền (VD: 0329880000|10000)'
                    : serviceType === 'gach_dien_evn'
                    ? 'Nhập danh sách mã hóa đơn EVN, mỗi mã một dòng...'
                    : 'Nhập danh sách, mỗi mã một dòng...'
                }
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
            
            {isMultiNetwork && (
              <div>
                <Label className="text-sm font-medium text-gray-700 mb-2">
                  Loại dịch vụ
                </Label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="paymentType"
                      value="prepaid"
                      checked={formData.paymentType === 'prepaid'}
                      onChange={(e) => setFormData({ ...formData, paymentType: e.target.value })}
                      className="mr-2"
                    />
                    Gạch nợ trả sau
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="paymentType"
                      value="postpaid"
                      checked={formData.paymentType === 'postpaid'}
                      onChange={(e) => setFormData({ ...formData, paymentType: e.target.value })}
                      className="mr-2"
                    />
                    Nạp trả trước
                    
                  </label>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  {formData.paymentType === 'prepaid' 
                    ? 'Nhập: danh sách số điện thoại (VD: 0329880000)'
                    : 'Nhập: sđt|số tiền (VD: 0329880000|10000)'
                  }
                </div>
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
            
            <div className="flex">
              <Button
                onClick={() => createOrderMutation.mutate()}
                disabled={
                  createOrderMutation.isPending || 
                  !formData.codes.trim() || 
                  (isMultiNetwork && !formData.paymentType)
                }
                className="w-full bg-primary hover:bg-primary/90"
              >
                {createOrderMutation.isPending ? (
                  <Loading size="sm" className="mr-2" />
                ) : (
                  <i className="fas fa-save mr-2"></i>
                )}
                {isMultiNetwork && !formData.paymentType 
                  ? 'Vui lòng chọn loại dịch vụ'
                  : 'Lưu danh sách vào hệ thống'
                }
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
              <div className="text-sm text-gray-600">Tổng: {txPage?.total || 0}</div>
              <div className="text-sm text-gray-600">Trang:</div>
              <select className="border rounded px-2 py-1 text-sm" value={page}
                onChange={(e) => setPage(parseInt(e.target.value))}>
                {Array.from({ length: Math.max(1, Math.ceil((txPage?.total || 0) / limit)) }).map((_, i) => (
                  <option key={i+1} value={i+1}>{i+1}</option>
                ))}
              </select>
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
                    {serviceType === 'gach_dien_evn'
                      ? 'Mã hóa đơn'
                      : ['nap_tien_da_mang', 'nap_tien_viettel', 'tra_cuu_no_tra_sau'].includes(serviceType)
                      ? 'Số điện thoại'
                      : 'Mã thuê bao'}
                  </th>
                  {isMultiNetwork && (
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Loại dịch vụ</th>
                  )}
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trạng thái</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Số tiền</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thời gian</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ghi chú</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {txPage && txPage.transactions && txPage.transactions.length > 0 ? (
                  txPage.transactions.map((t: any, index: number) => {
                    // Phân tích loại dịch vụ cho nạp tiền đa mạng
                    let serviceType = '';
                    let displayAmount = t.amount ? `${parseFloat(t.amount).toLocaleString('vi-VN')}đ` : '-';
                    
                    if (isMultiNetwork) {
                      // Phân tích từ code để xác định loại dịch vụ
                      const code = t.code;
                      if (code.includes('|')) {
                        // Có dấu | -> Nạp trả trước
                        serviceType = 'Nạp trả trước';
                        
                        // Tách số tiền từ code
                        const parts = code.split('|');
                        if (parts.length === 2) {
                          try {
                            const amount = parseInt(parts[1]);
                            if (!isNaN(amount)) {
                              displayAmount = `${amount.toLocaleString('vi-VN')}đ`;
                              // Cập nhật amount trong database nếu chưa có
                              if (!t.amount) {
                                console.log(`Cần cập nhật amount cho ${code}: ${amount}`);
                              }
                            }
                          } catch (e) {
                            // Nếu không parse được số tiền, giữ nguyên
                            console.log(`Không parse được số tiền từ ${code}:`, e);
                          }
                        }
                      } else {
                        // Không có dấu | -> Gạch nợ trả sau
                        serviceType = 'Gạch nợ trả sau';
                        displayAmount = '-'; // Gạch nợ trả sau không có số tiền
                      }
                      
                      // Nếu có notes từ database, ưu tiên sử dụng
                      if (t.notes && t.notes.includes('Multi-network:')) {
                        if (t.notes.includes('Nạp trả trước')) {
                          serviceType = 'Nạp trả trước';
                          // Nạp trả trước có số tiền từ database
                          if (t.amount) {
                            displayAmount = `${parseFloat(t.amount).toLocaleString('vi-VN')}đ`;
                          }
                        } else if (t.notes.includes('Gạch nợ trả sau')) {
                          serviceType = 'Gạch nợ trả sau';
                          // Gạch nợ trả sau không có số tiền
                          displayAmount = '-';
                        }
                      }
                      
                      // Debug log
                      console.log(`Code: ${code}, ServiceType: ${serviceType}, Amount: ${displayAmount}, DB Amount: ${t.amount}`);
                    }
                    
                    return (
                      <tr key={t.id}>
                        <td className="px-4 py-3 text-sm text-gray-700">{index + 1}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{t.code}</td>
                        {isMultiNetwork && (
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {serviceType ? (
                              <Badge variant={serviceType === 'Nạp trả trước' ? 'default' : 'secondary'}>
                                {serviceType}
                              </Badge>
                            ) : (
                              '-'
                            )}
                          </td>
                        )}
                        <td className="px-4 py-3 text-sm">
                          <Badge variant={t.status === 'success' ? 'default' : t.status === 'failed' ? 'destructive' : t.status === 'processing' ? 'outline' : 'secondary'}>
                            {t.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">{displayAmount}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {t.createdAt ? (() => {
                            try {
                              // Tạo date object từ createdAt
                              const date = new Date(t.createdAt);
                              
                              // Debug: Log thông tin chi tiết về thời gian
                              if (index === 0) {
                                console.log('=== DEBUG THỜI GIAN ===');
                                console.log('Raw createdAt từ DB:', t.createdAt);
                                console.log('Type của createdAt:', typeof t.createdAt);
                                console.log('Date object:', date);
                                console.log('Date.getTime():', date.getTime());
                                console.log('Date.toISOString():', date.toISOString());
                                console.log('Date.toUTCString():', date.toUTCString());
                                console.log('Date.toString():', date.toString());
                                console.log('Date.toLocaleString():', date.toLocaleString());
                                console.log('Date.toLocaleString(vi-VN):', date.toLocaleString('vi-VN'));
                                console.log('=== END DEBUG ===');
                              }
                              
                              // Giả sử thời gian từ DB đã bị cộng thêm 7 giờ, cần trừ đi để có giờ Việt Nam đúng
                              // Lấy thời gian từ DB và trừ đi 7 giờ
                              const dbTime = date.getTime();
                              const vietnamTime = new Date(dbTime - (7 * 60 * 60 * 1000));
                              
                              // Format theo múi giờ Việt Nam
                              return vietnamTime.toLocaleString('vi-VN', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit'
                              });
                            } catch (e) {
                              console.error('Lỗi parse thời gian:', e);
                              return '-';
                            }
                          })() : '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">{t.notes || ''}</td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={isMultiNetwork ? 7 : 6} className="px-4 py-8 text-center text-gray-500">
                      {'Không có giao dịch nào. Vui lòng lưu danh sách để tạo đơn.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
