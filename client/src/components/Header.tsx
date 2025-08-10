import { useAuth } from "@/hooks/useAuth";

interface HeaderProps {
  title: string;
  apiStatus: boolean;
}

export function Header({ title, apiStatus }: HeaderProps) {
  const { user } = useAuth();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${apiStatus ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-gray-600">
                {apiStatus ? 'API kết nối' : 'API lỗi'}
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
            <i className="fas fa-bell text-lg"></i>
          </button>
          
          <div className="flex items-center space-x-3">
            <img 
              src={user?.profileImageUrl || "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=100&h=100"} 
              alt="User avatar" 
              className="w-8 h-8 rounded-full object-cover"
            />
            <div className="text-sm">
              <p className="font-medium text-gray-900">
                {user?.firstName && user?.lastName 
                  ? `${user.firstName} ${user.lastName}`
                  : user?.email || 'Người dùng'}
              </p>
              <p className="text-gray-500">Quản trị viên</p>
            </div>
            <a 
              href="/api/logout"
              className="text-gray-400 hover:text-gray-600"
            >
              <i className="fas fa-sign-out-alt text-sm"></i>
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}
