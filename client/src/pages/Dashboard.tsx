import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { ServiceContent } from "@/components/ServiceContent";
import { StatsCards } from "@/components/StatsCards";



type DashboardProps = { initialService?: string };

const serviceIdToSlug: Record<string, string> = {
  'tra_cuu_ftth': '/tra-cuu-ftth',
  'gach_dien_evn': '/gach-dien-evn',
  'nap_tien_da_mang': '/nap-tien-da-mang',
  'nap_tien_viettel': '/nap-tien-viettel',
  'thanh_toan_tv_internet': '/thanh-toan-tv-internet',
  'tra_cuu_no_tra_sau': '/tra-cuu-no-tra-sau',
};

export default function Dashboard({ initialService }: DashboardProps = {}) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const [, navigate] = useLocation();
  const { toast } = useToast();
  const [activeService, setActiveService] = useState(initialService || 'tra_cuu_ftth');


  const handleServiceChange = (serviceId: string) => {
    setActiveService(serviceId);
    const slug = serviceIdToSlug[serviceId];
    if (slug) navigate(slug);
  };



  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      toast({
        title: "Unauthorized",
        description: "Bạn cần đăng nhập để tiếp tục",
        variant: "destructive",
      });
      setTimeout(() => {
        window.location.href = "/login";
      }, 500);
      return;
    }
  }, [isAuthenticated, isLoading, toast]);

  // Removed API health check - not needed and causing connection errors

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
        onServiceChange={handleServiceChange}
      />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          title={getServiceTitle(activeService)}
          user={user}
        />
        
        <main className="flex-1 overflow-auto p-6">
          {isService(activeService) ? (
            <ServiceContent serviceType={activeService} />
          ) : activeService === 'orders' ? (
            <div>
              <h3 className="text-lg font-semibold mb-4">Quản lý đơn hàng</h3>
              <p className="text-gray-600">Chức năng quản lý đơn hàng đang được phát triển...</p>
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
          
          {/* {isService(activeService) && (
            <>
              <StatsCards />
            </>
          )} */}
        </main>
      </div>


    </div>
  );
}
