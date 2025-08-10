import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { ServiceContent } from "@/components/ServiceContent";
import { StatsCards } from "@/components/StatsCards";
import { RecentOrders } from "@/components/RecentOrders";

export default function Dashboard() {
  const { isAuthenticated, isLoading } = useAuth();
  const { toast } = useToast();
  const [activeService, setActiveService] = useState("tra_cuu_ftth");
  const [apiStatus, setApiStatus] = useState(true);

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

  // Check API status periodically
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8080/api/health');
        setApiStatus(response.ok);
      } catch {
        setApiStatus(false);
      }
    };

    checkApiStatus();
    const interval = setInterval(checkApiStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getServiceTitle = (serviceType: string) => {
    const titles: Record<string, string> = {
      'tra_cuu_ftth': 'Tra cứu FTTH',
      'gach_dien_evn': 'Gạch điện EVN',
      'nap_tien_da_mang': 'Nạp tiền đa mạng',
      'nap_tien_viettel': 'Nạp tiền Viettel',
      'thanh_toan_tv_internet': 'Thanh toán TV-Internet',
      'tra_cuu_no_tra_sau': 'Tra cứu nợ trả sau',
      'orders': 'Quản lý đơn hàng',
      'reports': 'Xuất báo cáo',
      'config': 'Cấu hình hệ thống'
    };
    return titles[serviceType] || serviceType;
  };

  const isService = (serviceType: string) => {
    return serviceType.startsWith('tra_cuu') || 
           serviceType.startsWith('gach_') || 
           serviceType.startsWith('nap_') || 
           serviceType.startsWith('thanh_');
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

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar 
        activeService={activeService}
        onServiceChange={setActiveService}
      />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          title={getServiceTitle(activeService)}
          apiStatus={apiStatus}
        />
        
        <main className="flex-1 overflow-auto p-6">
          {isService(activeService) ? (
            <ServiceContent serviceType={activeService} />
          ) : activeService === 'orders' ? (
            <div>
              <h3 className="text-lg font-semibold mb-4">Quản lý đơn hàng</h3>
              <RecentOrders />
            </div>
          ) : activeService === 'reports' ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Xuất báo cáo</h3>
              <p className="text-gray-600">Chức năng xuất báo cáo đang được phát triển...</p>
            </div>
          ) : activeService === 'config' ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">Cấu hình hệ thống</h3>
              <p className="text-gray-600">Chức năng cấu hình đang được phát triển...</p>
            </div>
          ) : null}
          
          {isService(activeService) && (
            <>
              <StatsCards />
              <div className="mt-8">
                <RecentOrders />
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
