import { useQuery } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { LoadingSkeleton } from "./ui/loading";
import { useAuth } from "../hooks/useAuth";

function useServiceTypeFromPath() {
  const [pathname] = useLocation();
  const map: Record<string, string> = {
    '/tra-cuu-ftth': 'tra_cuu_ftth',
    '/gach-dien-evn': 'gach_dien_evn',
    '/nap-tien-da-mang': 'nap_tien_da_mang',
    '/nap-tien-viettel': 'nap_tien_viettel',
    '/thanh-toan-tv-internet': 'thanh_toan_tv_internet',
    '/tra-cuu-no-tra-sau': 'tra_cuu_no_tra_sau',
  };
  return map[pathname] || undefined;
}

type Stats = {
  todayTransactions: number;
  totalRevenue: string;
  successRate: number;
  pendingOrders: number;
};

export function StatsCards() {
  const { user } = useAuth();
  const serviceType = useServiceTypeFromPath();
  
  const { data: stats, isLoading } = useQuery<Stats>({
    queryKey: ['/api/stats', user?.id, serviceType],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (user?.id) {
        params.append('userId', user.id);
      }
      if (serviceType) {
        params.append('serviceType', serviceType);
      }
      
      const url = `/api/stats?${params.toString()}`;
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error(await res.text());
      return (await res.json()) as Stats;
    },
    refetchInterval: 30000,
    enabled: !!user?.id, // Only fetch when user is authenticated
  });

  // Show loading if user is not authenticated or data is loading
  if (!user || isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <LoadingSkeleton className="h-4 w-32" />
                <LoadingSkeleton className="h-8 w-20" />
              </div>
              <LoadingSkeleton className="w-12 h-12 rounded-lg" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const statItems = [
    {
      title: "Tổng giao dịch hôm nay",
      value: stats?.todayTransactions || 0,
      icon: "fas fa-chart-line",
      bgColor: "bg-blue-50",
      iconColor: "text-primary"
    },
    {
      title: "Tổng doanh thu",
      value: `${stats?.totalRevenue || 0}đ`,
      icon: "fas fa-dollar-sign", 
      bgColor: "bg-green-50",
      iconColor: "text-green-500"
    },
    {
      title: "Giao dịch thành công",
      value: `${stats?.successRate || 0}%`,
      icon: "fas fa-check-circle",
      bgColor: "bg-green-50", 
      iconColor: "text-green-500"
    },
    {
      title: "Đơn hàng chờ xử lý",
      value: stats?.pendingOrders || 0,
      icon: "fas fa-clock",
      bgColor: "bg-yellow-50",
      iconColor: "text-yellow-500"
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {statItems.map((item, index) => (
        <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{item.title}</p>
              <p className="text-2xl font-bold text-gray-900">{item.value}</p>
            </div>
            <div className={`w-12 h-12 ${item.bgColor} rounded-lg flex items-center justify-center`}>
              <i className={`${item.icon} ${item.iconColor} text-xl`}></i>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
