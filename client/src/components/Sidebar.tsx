import { cn } from "@/lib/utils";

interface SidebarProps {
  activeService: string;
  onServiceChange: (service: string) => void;
}

export function Sidebar({ activeService, onServiceChange }: SidebarProps) {
  const services = [
    {
      id: "tra_cuu_ftth",
      name: "Tra cứu FTTH",
      icon: "fas fa-search"
    },
    {
      id: "gach_dien_evn", 
      name: "Gạch điện EVN",
      icon: "fas fa-bolt"
    },
    {
      id: "nap_tien_da_mang",
      name: "Nạp tiền đa mạng", 
      icon: "fas fa-sim-card"
    },
    {
      id: "nap_tien_viettel",
      name: "Nạp tiền Viettel",
      icon: "fas fa-phone"
    },
    {
      id: "thanh_toan_tv_internet",
      name: "Thanh toán TV-Internet",
      icon: "fas fa-tv"
    },
    {
      id: "tra_cuu_no_tra_sau",
      name: "Tra cứu nợ trả sau",
      icon: "fas fa-file-invoice-dollar"
    }
  ];

  const managementItems = [
    {
      id: "orders",
      name: "Đơn hàng",
      icon: "fas fa-shopping-cart"
    },
    {
      id: "reports",
      name: "Xuất báo cáo", 
      icon: "fas fa-download"
    },
    {
      id: "config",
      name: "Cấu hình",
      icon: "fas fa-cog"
    }
  ];

  return (
    <div className="w-64 bg-white shadow-lg border-r border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <i className="fas fa-mobile-alt text-white text-lg"></i>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">ViettelPay</h1>
            <p className="text-sm text-gray-500">Quản lý dịch vụ</p>
          </div>
        </div>
      </div>
      
      <nav className="mt-6">
        <div className="px-4">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
            Dịch vụ chính
          </h3>
        </div>
        
        {services.map((service) => (
          <button
            key={service.id}
            onClick={() => onServiceChange(service.id)}
            className={cn(
              "w-full flex items-center px-4 py-3 text-sm font-medium transition-colors text-left",
              activeService === service.id
                ? "text-primary bg-primary/5 border-r-2 border-primary"
                : "text-gray-700 hover:bg-gray-50"
            )}
          >
            <i className={cn(
              service.icon,
              "mr-3",
              activeService === service.id ? "text-primary" : "text-gray-400"
            )}></i>
            {service.name}
          </button>
        ))}
        
        <div className="px-4 mt-8">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
            Quản lý
          </h3>
        </div>
        
        {managementItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onServiceChange(item.id)}
            className={cn(
              "w-full flex items-center px-4 py-3 text-sm font-medium transition-colors text-left",
              activeService === item.id
                ? "text-primary bg-primary/5 border-r-2 border-primary"
                : "text-gray-700 hover:bg-gray-50"
            )}
          >
            <i className={cn(
              item.icon,
              "mr-3", 
              activeService === item.id ? "text-primary" : "text-gray-400"
            )}></i>
            {item.name}
          </button>
        ))}
      </nav>
    </div>
  );
}
