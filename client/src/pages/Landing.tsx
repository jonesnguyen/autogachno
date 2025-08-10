import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <div className="flex items-center justify-center mb-6">
            <div className="w-16 h-16 bg-primary rounded-xl flex items-center justify-center">
              <i className="fas fa-mobile-alt text-white text-2xl"></i>
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Hệ thống quản lý dịch vụ viễn thông
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Nền tảng quản lý hiện đại cho các dịch vụ viễn thông ViettelPay
          </p>
          <Button 
            size="lg" 
            className="bg-primary hover:bg-primary/90"
            onClick={() => window.location.href = "/api/login"}
          >
            <i className="fas fa-sign-in-alt mr-2"></i>
            Đăng nhập để tiếp tục
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center mb-4">
                <i className="fas fa-search text-primary text-xl"></i>
              </div>
              <CardTitle className="text-lg">Tra cứu FTTH</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Tra cứu thông tin thuê bao FTTH nhanh chóng và chính xác
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-yellow-50 rounded-lg flex items-center justify-center mb-4">
                <i className="fas fa-bolt text-yellow-500 text-xl"></i>
              </div>
              <CardTitle className="text-lg">Thanh toán điện EVN</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Thanh toán hóa đơn điện EVN tiện lợi và an toàn
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center mb-4">
                <i className="fas fa-sim-card text-green-500 text-xl"></i>
              </div>
              <CardTitle className="text-lg">Nạp tiền đa mạng</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Nạp tiền cho các nhà mạng khác nhau từ một nền tảng
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center mb-4">
                <i className="fas fa-phone text-red-500 text-xl"></i>
              </div>
              <CardTitle className="text-lg">Nạp tiền Viettel</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Nạp tiền cho thuê bao Viettel với ưu đãi đặc biệt
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center mb-4">
                <i className="fas fa-tv text-purple-500 text-xl"></i>
              </div>
              <CardTitle className="text-lg">Thanh toán TV-Internet</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Thanh toán cước phí TV và Internet đơn giản
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center mb-4">
                <i className="fas fa-file-invoice-dollar text-indigo-500 text-xl"></i>
              </div>
              <CardTitle className="text-lg">Tra cứu nợ trả sau</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Kiểm tra và quản lý công nợ thuê bao trả sau
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Tính năng nổi bật
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="fas fa-bolt text-primary text-2xl"></i>
              </div>
              <h3 className="text-lg font-semibold mb-2">Xử lý nhanh chóng</h3>
              <p className="text-gray-600">
                Xử lý hàng loạt giao dịch với tốc độ cao và độ chính xác tuyệt đối
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="fas fa-shield-alt text-primary text-2xl"></i>
              </div>
              <h3 className="text-lg font-semibold mb-2">Bảo mật cao</h3>
              <p className="text-gray-600">
                Đảm bảo an toàn thông tin và giao dịch với các biện pháp bảo mật tiên tiến
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <i className="fas fa-chart-line text-primary text-2xl"></i>
              </div>
              <h3 className="text-lg font-semibold mb-2">Báo cáo chi tiết</h3>
              <p className="text-gray-600">
                Theo dõi và phân tích dữ liệu giao dịch với các báo cáo trực quan
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
