import { useQuery } from "@tanstack/react-query";
import type { User } from "@shared/schema";

export function useAuth() {
  const { data: user, isLoading } = useQuery<User>({
    queryKey: ["/api/auth/user"],
    retry: false,
  });

  // Kiểm tra user có hết hạn không
  const isExpired = user?.expiresAt ? new Date(user.expiresAt) < new Date() : false;
  
  // User chỉ được xem là authenticated nếu không hết hạn
  const isAuthenticated = !!user && !isExpired;

  return {
    user,
    isLoading,
    isAuthenticated,
    isExpired,
    expiresAt: user?.expiresAt,
  };
}
