import { useState } from "react";
import { useLocation } from "wouter";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

export default function Login() {
  const [, navigate] = useLocation();
  const { toast } = useToast();
  const [user, setUser] = useState("");
  const [password, setPassword] = useState("");
  const [showExpiredAlert, setShowExpiredAlert] = useState(false);

  const loginMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/dev/login", { user, password });
      return res.json();
    },
    onSuccess: (data) => {
      // Kiểm tra nếu user đã hết hạn
      if (data.user?.expiresAt && new Date(data.user.expiresAt) < new Date()) {
        setShowExpiredAlert(true);
        toast({ 
          title: "Tài khoản đã hết hạn", 
          description: "Vui lòng liên hệ quản trị viên để gia hạn", 
          variant: "destructive" 
        });
        return;
      }
      
      toast({ title: "Đăng nhập thành công" });
      navigate("/");
      // Fallback hard reload to refresh auth state
      setTimeout(() => window.location.reload(), 100);
    },
    onError: (error: any) => {
      toast({ title: "Đăng nhập thất bại", description: error.message, variant: "destructive" });
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !password) {
      toast({ title: "Thiếu thông tin", description: "Nhập tên đăng nhập và mật khẩu", variant: "destructive" });
      return;
    }
    setShowExpiredAlert(false);
    loginMutation.mutate();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl">Đăng nhập</CardTitle>
          <CardDescription>Nhập thông tin để truy cập hệ thống</CardDescription>
        </CardHeader>
        <CardContent>
          {showExpiredAlert && (
            <Alert className="mb-4 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800 dark:text-red-200">
                Tài khoản của bạn đã hết hạn. Vui lòng liên hệ quản trị viên để gia hạn.
              </AlertDescription>
            </Alert>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="user">Tên đăng nhập</Label>
              <Input id="user" type="text" value={user} onChange={(e) => setUser(e.target.value)} placeholder="Nhập tên tài khoản" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••" />
            </div>
            <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? "Đang đăng nhập..." : "Đăng nhập"}
            </Button>
            <Button type="button" variant="outline" className="w-full" onClick={() => navigate("/")}>Về trang chủ</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}


