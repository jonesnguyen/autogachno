import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { insertUserWithPasswordSchema } from "../shared/schema.js";
import { eq, desc, and, count } from "drizzle-orm";
import { orders, serviceTransactions, users } from "../shared/schema.js";
import proxyRouter from "./proxy";
import thuhohpkMockRouter from "./thuhohpk_mock";

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
import { getMockServiceData } from "./mockApiData";
import { db } from "./db";
import { z } from "zod";

export async function registerRoutes(app: Express): Promise<Server> {
  // Auth middleware
  await setupAuth(app);

  // Proxy routes (thuhohpk.com API)
  app.use(proxyRouter);
  
  // Mock thuhohpk.com API routes (localhost:3000)
  app.use(thuhohpkMockRouter);

  // Auth routes
  app.get('/api/auth/user', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const user = await storage.getUser(userId);
      
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      
      // Trả về toàn bộ user object bao gồm cả password
      res.json(user);
    } catch (error) {
      console.error("Error fetching user:", error);
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

  // Update current user profile
  app.patch('/api/auth/user', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const { firstName, lastName, user: newUser, password, confirmPassword } = req.body;
      
      // Validate required fields
      if (!firstName || !lastName || !newUser) {
        return res.status(400).json({ message: "Tên, họ và tên đăng nhập là bắt buộc" });
      }

      // Check if new username is already taken by another user
      const existingUser = await storage.getUserByUser(newUser);
      if (existingUser && existingUser.id !== userId) {
        return res.status(400).json({ message: "Tên đăng nhập đã được sử dụng bởi người khác" });
      }

      // Validate password if provided
      if (password) {
        if (password.length < 6) {
          return res.status(400).json({ message: "Mật khẩu phải có ít nhất 6 ký tự" });
        }
        if (password !== confirmPassword) {
          return res.status(400).json({ message: "Mật khẩu và xác nhận mật khẩu không khớp" });
        }
      }

      // Prepare update data
      const updateData: any = {
        firstName,
        lastName,
        user: newUser,
        updatedAt: new Date()
      };

      // Only update password if provided
      if (password) {
        updateData.password = password;
      }

      // Update user
      const updatedUser = await storage.updateUser(userId, updateData);
      
      res.json({
        message: "Cập nhật thông tin thành công",
        user: updatedUser
      });
    } catch (error) {
      console.error("Error updating user profile:", error);
      res.status(500).json({ message: "Failed to update user profile" });
    }
  });



  // Check user status by user (public route)
  app.get('/api/users/:user/status', async (req, res) => {
    try {
      const { user } = req.params;
      const userRecord = await storage.getUserByUser(user);
      
      if (!userRecord) {
        return res.status(404).json({ message: "User not found" });
      }
      
      res.json({
        user: userRecord.user,
        status: userRecord.status,
        message: userRecord.status === 'pending' 
          ? "Tài khoản đang chờ xét duyệt từ quản trị viên"
          : userRecord.status === 'active'
          ? "Tài khoản đã được kích hoạt"
          : "Tài khoản bị tạm khóa"
      });
    } catch (error) {
      console.error("Error checking user status:", error);
      res.status(500).json({ message: "Failed to check user status" });
    }
  });

  // Simple local login (dev only) using user/password to set admin session
  app.post('/api/dev/login', async (req: any, res) => {
    try {
      if (process.env.SKIP_AUTH !== '1') {
        return res.status(403).json({ message: 'Dev login only available in SKIP_AUTH mode' });
      }
      const { user, password } = req.body || {};
      if (!user || !password) {
        return res.status(400).json({ message: 'Tên đăng nhập và mật khẩu là bắt buộc' });
      }
      const userRecord = await storage.getUserByUser(user);
      if (!userRecord || !userRecord.password) {
        return res.status(401).json({ message: 'Invalid credentials' });
      }
      
      // Kiểm tra status của user
      if (userRecord.status === 'pending') {
        return res.status(403).json({ 
          message: 'Tài khoản của bạn đang chờ xét duyệt từ quản trị viên. Vui lòng liên hệ admin để được hỗ trợ.',
          status: 'pending'
        });
      }
      
      if (userRecord.status === 'suspended') {
        return res.status(403).json({ 
          message: 'Tài khoản của bạn đã bị tạm khóa. Vui lòng liên hệ admin để được hỗ trợ.',
          status: 'suspended'
        });
      }
      
      // So sánh password trực tiếp
      if (password !== userRecord.password) {
        return res.status(401).json({ message: 'Invalid credentials' });
      }
      
      // persist minimal user to session
      (req as any).session.user = { id: userRecord.id, user: userRecord.user };
      res.json({ message: 'Logged in', user: { id: userRecord.id, user: userRecord.user, role: userRecord.role } });
    } catch (error) {
      console.error('Dev login error:', error);
      res.status(500).json({ message: 'Login failed' });
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

  // Public data endpoint for desktop app (no auth), fetches recent codes from DB by service type
  app.get('/api/public/services/:serviceType/data', async (req, res) => {
    try {
      const { serviceType } = req.params;
      // read recent codes from DB
      const rows = await db
        .select({ code: serviceTransactions.code, createdAt: serviceTransactions.createdAt, orderId: serviceTransactions.orderId })
        .from(serviceTransactions)
        .leftJoin(orders, eq(serviceTransactions.orderId, orders.id))
        .where(eq(orders.serviceType, serviceType as any))
        .orderBy(desc(serviceTransactions.createdAt))
        .limit(20);

      const codes = rows.map(r => r.code).filter(Boolean) as string[];
      const codeOrderMap = rows
        .filter(r => !!r.code && !!r.orderId)
        .map(r => ({ code: r.code as string, orderId: r.orderId as string }));

      // Fallback to mock if DB empty
      let data: any;
      let source: 'db' | 'mock' = 'db';
      let candidateOrderId: string | undefined = rows[0]?.orderId as any;
      if (codes.length) {
        switch (serviceType) {
          case 'tra_cuu_ftth':
            data = { subscriber_codes: codes.slice(0, 10), order_id: candidateOrderId, code_order_map: codeOrderMap };
            break;
          case 'gach_dien_evn':
            data = { bill_codes: codes.slice(0, 10), order_id: candidateOrderId, code_order_map: codeOrderMap };
            break;
          case 'nap_tien_da_mang':
            // Đa mạng có thể là phone_numbers hoặc phone_amount_pairs
            const multiNetworkData = codes.map(code => {
              if (code.includes('|')) {
                const [phone, amount] = code.split('|');
                return { phone, amount: parseInt(amount) };
              }
              return { phone: code, amount: null };
            });
            data = { 
              phone_numbers: multiNetworkData.map(item => item.phone).slice(0, 10),
              phone_amount_pairs: multiNetworkData.slice(0, 10),
              order_id: candidateOrderId, 
              code_order_map: codeOrderMap 
            };
            break;
          case 'nap_tien_viettel':
          case 'tra_cuu_no_tra_sau':
            data = { phone_numbers: codes.slice(0, 10), order_id: candidateOrderId, code_order_map: codeOrderMap };
            break;
          case 'thanh_toan_tv_internet':
            data = { subscriber_codes: codes.slice(0, 10), order_id: candidateOrderId, code_order_map: codeOrderMap };
            break;
          default:
            data = {};
        }
      } else {
        data = { ...getMockServiceData(serviceType).data, code_order_map: [] };
        source = 'mock';
      }

      res.json({ status: 'success', service: serviceType, data, source });
    } catch (error) {
      console.error("Error fetching public service data:", error);
      res.status(500).json({ message: "Failed to fetch service data" });
    }
  });

  // Order management routes
  app.post('/api/orders', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const { serviceType, inputData, status, totalAmount } = req.body || {};
      if (!serviceType || !inputData) {
        return res.status(400).json({ message: 'serviceType and inputData are required' });
      }

      const parsed = typeof inputData === 'string' ? JSON.parse(inputData) : inputData;
      const codes: string[] = Array.isArray(parsed?.codes) ? parsed.codes : [];

      // Always create one order per code when multiple codes provided
      if (codes.length > 1) {
        const createdOrders: any[] = [];
        for (const code of codes) {
          const singleInput = { ...parsed, codes: [code] };
          const singleOrder = await storage.createOrder({
            userId,
            serviceType,
            status: (status || 'pending') as any,
            totalAmount,
            inputData: JSON.stringify(singleInput),
          } as any);
          await storage.createServiceTransaction({
            orderId: singleOrder.id,
            code,
            status: 'pending' as any,
          });
          createdOrders.push(singleOrder);
        }
        return res.json({ split: true, count: createdOrders.length, orders: createdOrders });
      }

      // Fallback: create single order (0 or 1 code)
      const order = await storage.createOrder({
        userId,
        serviceType,
        status: (status || 'pending') as any,
        totalAmount,
        inputData: typeof inputData === 'string' ? inputData : JSON.stringify(inputData),
      } as any);

      const oneOrMore = codes.length ? codes : [];
      for (const code of oneOrMore) {
        await storage.createServiceTransaction({
          orderId: order.id,
          code,
          status: 'pending' as any,
        });
      }

      res.json(order);
    } catch (error) {
      console.error('Error creating order:', error);
      res.status(400).json({ message: 'Failed to create order' });
    }
  });

  app.get('/api/orders', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const { serviceType } = req.query as { serviceType?: string };
      const page = Math.max(parseInt((req.query.page as string) || '1', 10), 1);
      const limit = Math.min(Math.max(parseInt((req.query.limit as string) || '20', 10), 1), 100);
      const offset = (page - 1) * limit;

      let query = db.select().from(orders).where(eq(orders.userId, userId as any));
      if (serviceType) {
        query = db.select().from(orders).where(and(eq(orders.userId, userId as any), eq(orders.serviceType, serviceType as any)));
      }
      const rows = await query.orderBy(desc(orders.createdAt)).limit(limit).offset(offset);

      let totalQuery = db.select({ count: count() }).from(orders).where(eq(orders.userId, userId as any));
      if (serviceType) {
        totalQuery = db.select({ count: count() }).from(orders).where(and(eq(orders.userId, userId as any), eq(orders.serviceType, serviceType as any)));
      }
      const totalRes = await totalQuery;
      const total = totalRes[0]?.count || 0;

      res.json({ orders: rows, total, page, limit });
    } catch (error) {
      console.error("Error fetching orders:", error);
      res.status(500).json({ message: "Failed to fetch orders" });
    }
  });

  // Recent orders route (place BEFORE /api/orders/:id to avoid route conflict)
  app.get('/api/orders/recent', isAuthenticated, async (req, res) => {
    try {
      const { serviceType } = req.query as { serviceType?: string };
      if (serviceType) {
        const svcOrders = await db
          .select()
          .from(orders)
          .where(eq(orders.serviceType, serviceType as any))
          .orderBy(desc(orders.createdAt))
          .limit(10);
        return res.json(svcOrders);
      }
      const recent = await storage.getRecentOrders();
      res.json(recent);
    } catch (error) {
      console.error("Error fetching recent orders:", error);
      res.status(500).json({ message: "Failed to fetch recent orders" });
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
      const codes = transactions.map(t => t.code);

      // Call Python automation API to start processing
      const response = await fetch(`${process.env.PY_AUTOMATION_URL}/api/automation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ serviceType, orderId, codes })
      });

      if (!response.ok) {
        const text = await response.text();
        await storage.updateOrderStatus(orderId, 'failed', JSON.stringify({ error: text }));
        return res.status(502).json({ message: 'Failed to start automation' });
      }

      res.json({ message: 'Processing started', forwardedTo: process.env.PY_AUTOMATION_URL });
    } catch (error) {
      console.error("Error processing service:", error);
      res.status(500).json({ message: "Failed to process service" });
    }
  });

  // Automation callback from Python app to update transaction status
  app.post('/api/automation/callback', async (req, res) => {
    try {
      let { orderId, code, status, amount, notes, data } = req.body || {};
      if (!code || !status) {
        return res.status(400).json({ message: 'Invalid payload' });
      }
      // If orderId missing, resolve by latest transaction for this code
      if (!orderId) {
        const rows = await db
          .select({
            id: serviceTransactions.id,
            orderId: serviceTransactions.orderId,
            createdAt: serviceTransactions.createdAt,
          })
          .from(serviceTransactions)
          .where(eq(serviceTransactions.code, code))
          .orderBy(desc(serviceTransactions.createdAt))
          .limit(1);
        orderId = rows[0]?.orderId;
        if (!orderId) {
          return res.status(404).json({ message: 'Order not found for code' });
        }
      }
      // Find transaction by code under this order
      const transactions = await storage.getOrderTransactions(orderId);
      const tx = transactions.find(t => t.code === code);
      if (!tx) {
        return res.status(404).json({ message: 'Transaction not found' });
      }
      await storage.updateTransactionStatus(tx.id, status, amount, notes, data ? JSON.stringify(data) : undefined);

      // If all done, set order status
      const all = await storage.getOrderTransactions(orderId);
      const hasPending = all.some(t => t.status === 'pending' || t.status === 'processing');
      if (!hasPending) {
        const anyFailed = all.some(t => t.status === 'failed');
        await storage.updateOrderStatus(orderId, anyFailed ? 'failed' : 'completed');
      }
      res.json({ message: 'ok' });
    } catch (error) {
      console.error('Automation callback error:', error);
      res.status(500).json({ message: 'Server error' });
    }
  });

  // List pending orders for automation (public, no auth)
  app.get('/api/automation/pending', async (req, res) => {
    try {
      const limit = Math.min(parseInt((req.query.limit as string) || '5', 10), 50);
      const pending = await db
        .select()
        .from(orders)
        .where(eq(orders.status, 'pending'))
        .orderBy(desc(orders.createdAt))
        .limit(limit);

      const results = [] as any[];
      for (const order of pending) {
        const txs = await storage.getOrderTransactions(order.id);
        results.push({
          orderId: order.id,
          serviceType: order.serviceType,
          userId: order.userId,
          transactions: txs.map(t => ({ id: t.id, code: t.code, status: t.status })),
          createdAt: order.createdAt,
        });
      }
      // Hiển thị tất cả orderId đang chờ
      res.json({ orders: results, pendingOrderIds: results.map(r => r.orderId) });
    } catch (error) {
      console.error('List pending error:', error);
      res.status(500).json({ message: 'Server error' });
    }
  });

  // Claim an order for processing (public)
  app.post('/api/automation/claim', async (req, res) => {
    try {
      const { orderId } = req.body || {};
      if (!orderId) return res.status(400).json({ message: 'orderId required' });
      const updated = await db
        .update(orders)
        .set({ status: 'processing', updatedAt: new Date() as any })
        .where(and(eq(orders.id, orderId), eq(orders.status, 'pending')))
        .returning();
      if (updated.length === 0) {
        return res.status(409).json({ message: 'Order already claimed or not pending' });
      }
      // Trả về thêm tiến trình đơn giản
      res.json({ ...updated[0], progress: 'claimed' });
    } catch (error) {
      console.error('Claim order error:', error);
      res.status(500).json({ message: 'Server error' });
    }
  });

  // Transaction routes
  app.get('/api/transactions', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const serviceType = req.query.serviceType as string;
      const page = Math.max(parseInt((req.query.page as string) || '1', 10), 1);
      const limit = Math.min(Math.max(parseInt((req.query.limit as string) || '20', 10), 1), 100);
      const offset = (page - 1) * limit;

      if (!serviceType) {
        return res.status(400).json({ message: 'serviceType is required' });
      }

      const whereClause = and(eq(orders.userId, userId), eq(orders.serviceType, serviceType as any));

      const txs = await db
        .select({
          id: serviceTransactions.id,
          orderId: serviceTransactions.orderId,
          code: serviceTransactions.code,
          status: serviceTransactions.status,
          amount: serviceTransactions.amount,
          notes: serviceTransactions.notes,
          createdAt: serviceTransactions.createdAt,
          updatedAt: serviceTransactions.updatedAt,
        })
        .from(serviceTransactions)
        .leftJoin(orders, eq(serviceTransactions.orderId, orders.id))
        .where(whereClause)
        .orderBy(desc(serviceTransactions.createdAt))
        .limit(limit)
        .offset(offset);

      const totalRes = await db
        .select({ total: count() })
        .from(serviceTransactions)
        .leftJoin(orders, eq(serviceTransactions.orderId, orders.id))
        .where(whereClause);

      const total = totalRes[0]?.total || 0;
      res.json({ transactions: txs, total, page, limit });
    } catch (error) {
      console.error("Error fetching transactions:", error);
      res.status(500).json({ message: "Failed to fetch transactions" });
    }
  });
  
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
  app.get('/api/stats', isAuthenticated, async (req: any, res) => {
    try {
      const serviceType = req.query.serviceType as string | undefined;
      const userId = req.query.userId as string || req.user.claims.sub;
      
      if (!userId) {
        return res.status(400).json({ message: "User ID is required" });
      }

      if (!serviceType) {
        // Get user-specific stats
        const userOrders = await storage.getUserOrders(userId, 1000); // Get all user orders
        const orderIds = userOrders.map(o => o.id);
        
        let allTransactions: any[] = [];
        for (const id of orderIds) {
          const txs = await storage.getOrderTransactions(id);
          allTransactions = allTransactions.concat(txs);
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayTransactions = allTransactions.filter(t => 
          new Date(t.createdAt) >= today
        ).length;

        const successful = allTransactions.filter(t => t.status === 'success');
        const totalRevenueNum = successful.reduce((sum, t) => sum + (parseFloat(t.amount || '0')), 0);
        const successRate = allTransactions.length > 0 ? (successful.length / allTransactions.length) * 100 : 0;
        const pendingOrders = userOrders.filter(o => o.status === 'pending').length;

        return res.json({
          todayTransactions,
          totalRevenue: totalRevenueNum.toLocaleString('vi-VN'),
          successRate: Math.round(successRate * 10) / 10,
          pendingOrders,
        });
      }

      // Service-specific stats for user
      const userOrders = await storage.getUserOrders(userId, 1000);
      const svcOrders = userOrders.filter(o => o.serviceType === serviceType);

      const orderIds = svcOrders.map((o) => o.id);
      let svcTxs: any[] = [];
      for (const id of orderIds) {
        const txs = await storage.getOrderTransactions(id);
        svcTxs = svcTxs.concat(txs);
      }

      const todayTransactions = svcTxs.length; // simplified
      const successful = svcTxs.filter((t) => t.status === 'success');
      const totalRevenueNum = successful.reduce((sum, t) => sum + (parseFloat(t.amount || '0')), 0);
      const successRate = svcTxs.length > 0 ? (successful.length / svcTxs.length) * 100 : 0;
      const pendingOrders = svcOrders.filter((o) => o.status === 'pending').length;

      return res.json({
        todayTransactions,
        totalRevenue: totalRevenueNum.toLocaleString('vi-VN'),
        successRate: Math.round(successRate * 10) / 10,
        pendingOrders,
      });
    } catch (error) {
      console.error("Error fetching stats:", error);
      res.status(500).json({ message: "Failed to fetch stats" });
    }
  });

  // (moved above to avoid conflict with /api/orders/:id)

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
      const userData = insertUserWithPasswordSchema.parse(req.body);
      
      // Check if user already exists
      if (userData.user) {
        const existingUser = await storage.getUserByUser(userData.user);
        if (existingUser) {
          return res.status(400).json({ message: "Tên đăng nhập đã được sử dụng" });
        }
      }

      // Create user with pending status - requires admin approval
      const { password, confirmPassword, ...userDataForDb } = userData;
      const newUser = await storage.createUser({
        ...userDataForDb,
        password: userData.password, // Lưu password thuần túy
        role: 'user',
        status: 'pending' // User phải chờ xét duyệt từ admin
      });
      
      res.json({ 
        message: "Đăng ký thành công! Tài khoản của bạn đang chờ xét duyệt từ quản trị viên. Bạn sẽ nhận được thông báo khi được phê duyệt.",
        id: newUser.id,
        status: 'pending'
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
      const status = req.query.status as string;
      
      const result = await storage.getAllUsers(page, limit, search, status);
      res.json(result);
    } catch (error) {
      console.error("Error fetching users:", error);
      res.status(500).json({ message: "Failed to fetch users" });
    }
  });

  // Get pending users specifically
  app.get('/api/admin/users/pending', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      
      const result = await storage.getAllUsers(page, limit, undefined, 'pending');
      res.json(result);
    } catch (error) {
      console.error("Error fetching pending users:", error);
      res.status(500).json({ message: "Failed to fetch pending users" });
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

  // Approve/reject pending users
  app.patch('/api/admin/users/:id/approve', isAuthenticated, isAdmin, async (req: any, res) => {
    try {
      const { id } = req.params;
      const { approved, notes } = req.body;
      
      const oldUser = await storage.getUser(id);
      if (!oldUser) {
        return res.status(404).json({ message: "User not found" });
      }
      
      if (oldUser.status !== 'pending') {
        return res.status(400).json({ message: "User is not in pending status" });
      }
      
      const newStatus = approved ? 'active' : 'suspended';
      const updatedUser = await storage.updateUserStatus(id, newStatus);
      
      // Log admin action
      await storage.createAdminLog({
        adminId: req.adminUser.id,
        action: approved ? 'approve_user' : 'reject_user',
        targetType: 'user',
        targetId: id,
        oldData: JSON.stringify({ status: oldUser.status }),
        newData: JSON.stringify({ status: newStatus, notes }),
        ipAddress: req.ip,
        userAgent: req.get('User-Agent')
      });
      
      res.json({
        message: approved ? "User approved successfully" : "User rejected successfully",
        user: updatedUser
      });
    } catch (error) {
      console.error("Error approving user:", error);
      res.status(500).json({ message: "Failed to approve user" });
    }
  });

  app.patch('/api/admin/users/:id/expiration', isAuthenticated, isAdmin, async (req: any, res) => {
    try {
      const { id } = req.params;
      const { expiresAt } = req.body;
      
      console.log('🚀 Backend: Expiration update request received');
      console.log('   User ID:', id);
      console.log('   New expiresAt:', expiresAt);
      console.log('   Request body:', req.body);
      console.log('   Admin user:', req.adminUser.id);
      
      // Kiểm tra user tồn tại
      const oldUser = await storage.getUser(id);
      if (!oldUser) {
        console.log('❌ User not found:', id);
        return res.status(404).json({ message: "User not found" });
      }
      
      console.log('👤 Old user data:', {
        id: oldUser.id,
        user: oldUser.user,
        oldExpiresAt: oldUser.expiresAt,
        role: oldUser.role,
        status: oldUser.status
      });
      
      // Thực hiện update
      console.log('🔄 Calling storage.updateUserExpiration...');
      const updatedUser = await storage.updateUserExpiration(id, expiresAt);
      
      console.log('✅ Storage update successful. Updated user:', {
        id: updatedUser.id,
        user: updatedUser.user,
        newExpiresAt: updatedUser.expiresAt,
        updatedAt: updatedUser.updatedAt
      });
      
      // Log admin action
      console.log('📝 Creating admin log...');
      const adminLog = await storage.createAdminLog({
        adminId: req.adminUser.id,
        action: 'update_user_expiration',
        targetType: 'user',
        targetId: id,
        oldData: JSON.stringify({ expiresAt: oldUser?.expiresAt }),
        newData: JSON.stringify({ expiresAt }),
        ipAddress: req.ip,
        userAgent: req.get('User-Agent')
      });
      
      console.log('📋 Admin log created:', adminLog.id);
      
      // Trả về kết quả
      console.log('📤 Sending response to frontend...');
      res.json(updatedUser);
      
    } catch (error) {
      console.error("❌ Error updating user expiration:", error);
      if (error instanceof Error) {
        console.error("   Error stack:", error.stack);
        console.error("   Error name:", error.name);
        console.error("   Error message:", error.message);
      }
      
      res.status(500).json({ 
        message: "Failed to update user expiration", 
        error: error instanceof Error ? error.message : 'Unknown error',
        errorType: error instanceof Error ? error.constructor.name : 'Unknown'
      });
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
          user: reviewedRegistration.user,
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



  // Test database connection and raw SQL
  app.get('/api/test/db', async (req, res) => {
    try {
      // Test basic connection
      const result = await db.select().from(users).limit(1);
      console.log('Database connection test successful:', result);
      
      res.json({ 
        message: 'Database connection successful',
        userCount: result.length,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Database connection test failed:', error);
      res.status(500).json({ 
        message: 'Database connection failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Simple health check endpoint
  app.get('/api/health', (req, res) => {
    res.json({ 
      status: 'OK', 
      timestamp: new Date().toISOString(),
      uptime: process.uptime()
    });
  });

  // Test admin middleware
  app.get('/api/test/admin-check', isAuthenticated, isAdmin, (req: any, res) => {
    res.json({ 
      message: 'Admin check successful',
      adminUser: req.adminUser,
      timestamp: new Date().toISOString()
    });
  });

  // Test raw SQL update
  app.post('/api/test/update-user', async (req, res) => {
    try {
      const { userId, expiresAt } = req.body;
      
      if (!userId) {
        return res.status(400).json({ message: 'userId is required' });
      }
      
      console.log(`Testing raw SQL update for user ${userId} with expiresAt: ${expiresAt}`);
      
      // Test with Drizzle ORM first
      const [user] = await db
        .update(users)
        .set({ 
          expiresAt: expiresAt ? new Date(expiresAt) : null, 
          updatedAt: new Date() 
        })
        .where(eq(users.id, userId))
        .returning();
      
      if (!user) {
        return res.status(404).json({ message: 'User not found' });
      }
      
      console.log('Drizzle ORM update successful:', user);
      
      res.json({ 
        message: 'Test update successful',
        user: user,
        method: 'Drizzle ORM'
      });
    } catch (error) {
      console.error('Test update failed:', error);
      res.status(500).json({ 
        message: 'Test update failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  // Check database schema and user data directly
  app.get('/api/test/check-user/:id', async (req, res) => {
    try {
      const { id } = req.params;
      
      console.log('🔍 Checking user data directly from database:', id);
      
      // Kiểm tra user với raw query để xem cấu trúc thực tế
      const userResult = await db.select().from(users).where(eq(users.id, id));
      
      if (userResult.length === 0) {
        return res.status(404).json({ message: 'User not found' });
      }
      
      const user = userResult[0];
      console.log('👤 Raw user data from database:', user);
      
      // Kiểm tra cấu trúc bảng
      const tableInfo = await db.execute(`
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        ORDER BY ordinal_position
      `);
      
      console.log('📋 Table structure:', tableInfo);
      
      res.json({
        message: 'User data retrieved successfully',
        user: user,
        tableStructure: tableInfo,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      console.error('Check user failed:', error);
      res.status(500).json({ 
        message: 'Check user failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
