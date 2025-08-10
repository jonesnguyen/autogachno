import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";

// Admin middleware
const isAdmin = async (req: any, res: any, next: any) => {
  try {
    const userId = req.user?.claims?.sub;
    if (!userId) {
      return res.status(401).json({ message: "Unauthorized" });
    }
    
    const user = await storage.getUser(userId);
    if (!user || (user.role !== 'admin' && user.role !== 'manager')) {
      return res.status(403).json({ message: "Admin access required" });
    }
    
    req.adminUser = user;
    next();
  } catch (error) {
    console.error("Admin check error:", error);
    res.status(500).json({ message: "Server error" });
  }
};
import { 
  insertOrderSchema, 
  insertServiceTransactionSchema, 
  insertUserRegistrationSchema,
  insertAdminLogSchema 
} from "@shared/schema";
import { getMockServiceData } from "./mockApiData";
import { z } from "zod";

export async function registerRoutes(app: Express): Promise<Server> {
  // Auth middleware
  await setupAuth(app);

  // Auth routes
  app.get('/api/auth/user', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const user = await storage.getUser(userId);
      res.json(user);
    } catch (error) {
      console.error("Error fetching user:", error);
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

  // Service list route
  app.get('/api/services', isAuthenticated, async (req, res) => {
    try {
      const services = [
        {
          id: 'tra_cuu_ftth',
          name: 'Tra cứu FTTH',
          description: 'Tra cứu thông tin thuê bao FTTH',
          icon: 'Router',
          category: 'lookup'
        },
        {
          id: 'gach_dien_evn',
          name: 'Gạch điện EVN',
          description: 'Thanh toán hóa đơn điện EVN',
          icon: 'Zap',
          category: 'payment'
        },
        {
          id: 'nap_tien_da_mang',
          name: 'Nạp tiền đa mạng',
          description: 'Nạp tiền cho nhiều nhà mạng',
          icon: 'Smartphone',
          category: 'topup'
        },
        {
          id: 'nap_tien_viettel',
          name: 'Nạp tiền Viettel',
          description: 'Nạp tiền mạng Viettel',
          icon: 'Phone',
          category: 'topup'
        },
        {
          id: 'thanh_toan_tv_internet',
          name: 'TV - Internet',
          description: 'Thanh toán dịch vụ TV và Internet',
          icon: 'Tv',
          category: 'payment'
        },
        {
          id: 'tra_cuu_no_tra_sau',
          name: 'Tra cứu trả sau',
          description: 'Tra cứu nợ thuê bao trả sau',
          icon: 'CreditCard',
          category: 'lookup'
        }
      ];
      res.json(services);
    } catch (error) {
      console.error("Error fetching services:", error);
      res.status(500).json({ message: "Failed to fetch services" });
    }
  });

  // Service data routes
  app.get('/api/services/:serviceType/data', isAuthenticated, async (req, res) => {
    try {
      const { serviceType } = req.params;
      
      // Use built-in mock data instead of external API
      const data = getMockServiceData(serviceType);
      
      res.json(data);
    } catch (error) {
      console.error("Error fetching service data:", error);
      res.status(500).json({ message: "Failed to fetch service data" });
    }
  });

  // Order management routes
  app.post('/api/orders', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const orderData = insertOrderSchema.parse({
        ...req.body,
        userId,
      });

      const order = await storage.createOrder(orderData);
      
      // Create individual transactions for each code
      const inputData = JSON.parse(orderData.inputData);
      const codes = inputData.codes || [];
      
      for (const code of codes) {
        await storage.createServiceTransaction({
          orderId: order.id,
          code,
          status: 'pending',
        });
      }

      res.json(order);
    } catch (error) {
      console.error("Error creating order:", error);
      res.status(400).json({ message: "Failed to create order" });
    }
  });

  app.get('/api/orders', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const orders = await storage.getUserOrders(userId);
      res.json(orders);
    } catch (error) {
      console.error("Error fetching orders:", error);
      res.status(500).json({ message: "Failed to fetch orders" });
    }
  });

  app.get('/api/orders/:id', isAuthenticated, async (req: any, res) => {
    try {
      const { id } = req.params;
      const order = await storage.getOrder(id);
      
      if (!order) {
        return res.status(404).json({ message: "Order not found" });
      }

      const transactions = await storage.getOrderTransactions(id);
      
      res.json({
        ...order,
        transactions,
      });
    } catch (error) {
      console.error("Error fetching order:", error);
      res.status(500).json({ message: "Failed to fetch order" });
    }
  });

  app.patch('/api/orders/:id/status', isAuthenticated, async (req, res) => {
    try {
      const { id } = req.params;
      const { status, resultData } = req.body;
      
      const order = await storage.updateOrderStatus(id, status, resultData);
      res.json(order);
    } catch (error) {
      console.error("Error updating order status:", error);
      res.status(500).json({ message: "Failed to update order status" });
    }
  });

  // Service processing routes
  app.post('/api/services/:serviceType/process', isAuthenticated, async (req: any, res) => {
    try {
      const { serviceType } = req.params;
      const { orderId } = req.body;
      
      // Update order status to processing
      await storage.updateOrderStatus(orderId, 'processing');
      
      // Get order transactions
      const transactions = await storage.getOrderTransactions(orderId);
      
      // Process each transaction (simulate API calls)
      for (const transaction of transactions) {
        // Simulate processing delay and random results
        setTimeout(async () => {
          const isSuccess = Math.random() > 0.1; // 90% success rate
          const amount = (Math.random() * 1000000 + 100000).toFixed(0);
          
          await storage.updateTransactionStatus(
            transaction.id,
            isSuccess ? 'success' : 'failed',
            isSuccess ? amount : undefined,
            isSuccess ? 'Xử lý thành công' : 'Lỗi xử lý dịch vụ'
          );
        }, Math.random() * 5000 + 1000);
      }
      
      res.json({ message: 'Processing started' });
    } catch (error) {
      console.error("Error processing service:", error);
      res.status(500).json({ message: "Failed to process service" });
    }
  });

  // Transaction routes
  app.get('/api/orders/:orderId/transactions', isAuthenticated, async (req, res) => {
    try {
      const { orderId } = req.params;
      const transactions = await storage.getOrderTransactions(orderId);
      res.json(transactions);
    } catch (error) {
      console.error("Error fetching transactions:", error);
      res.status(500).json({ message: "Failed to fetch transactions" });
    }
  });

  // Statistics routes
  app.get('/api/stats', isAuthenticated, async (req, res) => {
    try {
      const stats = await storage.getTodayStats();
      res.json(stats);
    } catch (error) {
      console.error("Error fetching stats:", error);
      res.status(500).json({ message: "Failed to fetch stats" });
    }
  });

  // Recent orders route
  app.get('/api/orders/recent', isAuthenticated, async (req, res) => {
    try {
      const orders = await storage.getRecentOrders();
      res.json(orders);
    } catch (error) {
      console.error("Error fetching recent orders:", error);
      res.status(500).json({ message: "Failed to fetch recent orders" });
    }
  });

  // Export routes
  app.get('/api/orders/:id/export', isAuthenticated, async (req, res) => {
    try {
      const { id } = req.params;
      const order = await storage.getOrder(id);
      const transactions = await storage.getOrderTransactions(id);
      
      if (!order) {
        return res.status(404).json({ message: "Order not found" });
      }

      const { format = 'csv' } = req.query;
      
      if (format === 'json') {
        // JSON export
        const exportData = {
          order,
          transactions,
          exportedAt: new Date().toISOString(),
          summary: {
            totalTransactions: transactions.length,
            successfulTransactions: transactions.filter(t => t.status === 'success').length,
            failedTransactions: transactions.filter(t => t.status === 'failed').length,
            pendingTransactions: transactions.filter(t => t.status === 'pending').length,
          }
        };
        
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Content-Disposition', `attachment; filename="order-${id}.json"`);
        res.json(exportData);
      } else {
        // CSV export
        const csvHeader = 'STT,Mã,Trạng thái,Số tiền,Ghi chú,Thời gian tạo,Thời gian cập nhật\n';
        const csvData = transactions.map((t, index) => 
          `${index + 1},"${t.code}","${t.status}","${t.amount || ''}","${t.notes || ''}","${t.createdAt}","${t.updatedAt}"`
        ).join('\n');
        
        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="order-${id}.csv"`);
        res.send('\ufeff' + csvHeader + csvData); // Add BOM for UTF-8
      }
    } catch (error) {
      console.error("Error exporting order:", error);
      res.status(500).json({ message: "Failed to export order" });
    }
  });

  // Bulk operations API
  app.post('/api/orders/bulk-process', isAuthenticated, async (req: any, res) => {
    try {
      const { orderIds, action } = req.body;
      const userId = req.user.claims.sub;
      
      if (!Array.isArray(orderIds) || orderIds.length === 0) {
        return res.status(400).json({ message: "Invalid order IDs" });
      }

      const results = [];
      
      for (const orderId of orderIds) {
        try {
          const order = await storage.getOrder(orderId);
          if (!order || order.userId !== userId) {
            results.push({ orderId, success: false, error: "Order not found or access denied" });
            continue;
          }

          if (action === 'delete') {
            // Note: In production, you might want soft delete
            results.push({ orderId, success: true, message: "Order marked for deletion" });
          } else if (action === 'retry') {
            await storage.updateOrderStatus(orderId, 'pending');
            results.push({ orderId, success: true, message: "Order marked for retry" });
          } else {
            results.push({ orderId, success: false, error: "Unknown action" });
          }
        } catch (error) {
          results.push({ orderId, success: false, error: (error as Error).message });
        }
      }
      
      res.json({ results });
    } catch (error) {
      console.error("Error in bulk operation:", error);
      res.status(500).json({ message: "Failed to perform bulk operation" });
    }
  });

  // User Registration (Public route)
  app.post('/api/register', async (req, res) => {
    try {
      const registrationData = insertUserRegistrationSchema.parse(req.body);
      const registration = await storage.createUserRegistration(registrationData);
      
      res.json({ 
        message: "Đăng ký thành công. Yêu cầu của bạn đang chờ phê duyệt.",
        id: registration.id 
      });
    } catch (error) {
      console.error("Registration error:", error);
      res.status(400).json({ message: "Lỗi đăng ký" });
    }
  });

  // Admin routes
  app.get('/api/admin/users', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const search = req.query.search as string;
      
      const result = await storage.getAllUsers(page, limit, search);
      res.json(result);
    } catch (error) {
      console.error("Error fetching users:", error);
      res.status(500).json({ message: "Failed to fetch users" });
    }
  });

  app.patch('/api/admin/users/:id/role', isAuthenticated, isAdmin, async (req: any, res) => {
    try {
      const { id } = req.params;
      const { role } = req.body;
      
      const oldUser = await storage.getUser(id);
      const updatedUser = await storage.updateUserRole(id, role);
      
      // Log admin action
      await storage.createAdminLog({
        adminId: req.adminUser.id,
        action: 'update_user_role',
        targetType: 'user',
        targetId: id,
        oldData: JSON.stringify({ role: oldUser?.role }),
        newData: JSON.stringify({ role }),
        ipAddress: req.ip,
        userAgent: req.get('User-Agent')
      });
      
      res.json(updatedUser);
    } catch (error) {
      console.error("Error updating user role:", error);
      res.status(500).json({ message: "Failed to update user role" });
    }
  });

  app.patch('/api/admin/users/:id/status', isAuthenticated, isAdmin, async (req: any, res) => {
    try {
      const { id } = req.params;
      const { status } = req.body;
      
      const oldUser = await storage.getUser(id);
      const updatedUser = await storage.updateUserStatus(id, status);
      
      // Log admin action
      await storage.createAdminLog({
        adminId: req.adminUser.id,
        action: 'update_user_status',
        targetType: 'user',
        targetId: id,
        oldData: JSON.stringify({ status: oldUser?.status }),
        newData: JSON.stringify({ status }),
        ipAddress: req.ip,
        userAgent: req.get('User-Agent')
      });
      
      res.json(updatedUser);
    } catch (error) {
      console.error("Error updating user status:", error);
      res.status(500).json({ message: "Failed to update user status" });
    }
  });

  app.delete('/api/admin/users/:id', isAuthenticated, isAdmin, async (req: any, res) => {
    try {
      const { id } = req.params;
      
      const oldUser = await storage.getUser(id);
      await storage.deleteUser(id);
      
      // Log admin action
      await storage.createAdminLog({
        adminId: req.adminUser.id,
        action: 'delete_user',
        targetType: 'user',
        targetId: id,
        oldData: JSON.stringify(oldUser),
        newData: null,
        ipAddress: req.ip,
        userAgent: req.get('User-Agent')
      });
      
      res.json({ message: "User deleted successfully" });
    } catch (error) {
      console.error("Error deleting user:", error);
      res.status(500).json({ message: "Failed to delete user" });
    }
  });

  // Registration management
  app.get('/api/admin/registrations', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const status = req.query.status as string;
      const registrations = await storage.getUserRegistrations(status);
      res.json(registrations);
    } catch (error) {
      console.error("Error fetching registrations:", error);
      res.status(500).json({ message: "Failed to fetch registrations" });
    }
  });

  app.patch('/api/admin/registrations/:id/review', isAuthenticated, isAdmin, async (req: any, res) => {
    try {
      const { id } = req.params;
      const { approved, notes } = req.body;
      
      const reviewedRegistration = await storage.reviewUserRegistration(
        id, 
        approved, 
        req.adminUser.id, 
        notes
      );

      // If approved, create user account
      if (approved) {
        await storage.upsertUser({
          id: `reg_${reviewedRegistration.id}`, // Temporary ID, will be overridden by OAuth
          email: reviewedRegistration.email,
          firstName: reviewedRegistration.firstName,
          lastName: reviewedRegistration.lastName,
          role: 'user',
          status: 'active'
        });
      }
      
      // Log admin action
      await storage.createAdminLog({
        adminId: req.adminUser.id,
        action: approved ? 'approve_registration' : 'reject_registration',
        targetType: 'registration',
        targetId: id,
        oldData: JSON.stringify({ status: 'pending' }),
        newData: JSON.stringify({ status: approved ? 'approved' : 'rejected', notes }),
        ipAddress: req.ip,
        userAgent: req.get('User-Agent')
      });
      
      res.json(reviewedRegistration);
    } catch (error) {
      console.error("Error reviewing registration:", error);
      res.status(500).json({ message: "Failed to review registration" });
    }
  });

  // Admin statistics
  app.get('/api/admin/stats', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const stats = await storage.getAdminStats();
      res.json(stats);
    } catch (error) {
      console.error("Error fetching admin stats:", error);
      res.status(500).json({ message: "Failed to fetch admin stats" });
    }
  });

  // Admin logs
  app.get('/api/admin/logs', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 50;
      
      const result = await storage.getAdminLogs(page, limit);
      res.json(result);
    } catch (error) {
      console.error("Error fetching admin logs:", error);
      res.status(500).json({ message: "Failed to fetch admin logs" });
    }
  });

  // All orders (admin view)
  app.get('/api/admin/orders', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      
      const result = await storage.getAllOrders(page, limit);
      res.json(result);
    } catch (error) {
      console.error("Error fetching all orders:", error);
      res.status(500).json({ message: "Failed to fetch orders" });
    }
  });

  // API health check
  app.get('/api/health', (req, res) => {
    res.json({
      status: 'success',
      message: 'Viettel Pay API Server đang hoạt động',
      timestamp: new Date().toISOString(),
      services: [
        'tra_cuu_ftth',
        'gach_dien_evn', 
        'nap_tien_da_mang',
        'nap_tien_viettel',
        'thanh_toan_tv_internet',
        'tra_cuu_no_tra_sau'
      ]
    });
  });

  const httpServer = createServer(app);
  return httpServer;
}
