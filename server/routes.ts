import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { insertOrderSchema, insertServiceTransactionSchema } from "@shared/schema";
import { z } from "zod";

// Mock API integration
const MOCK_API_BASE = process.env.MOCK_API_BASE || 'http://127.0.0.1:8080';

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

  // Service data routes
  app.get('/api/services/:serviceType/data', isAuthenticated, async (req, res) => {
    try {
      const { serviceType } = req.params;
      
      // Fetch from mock API
      const response = await fetch(`${MOCK_API_BASE}/api/data/${serviceType}`);
      const data = await response.json();
      
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

      // Simple CSV export
      const csvHeader = 'STT,Mã,Trạng thái,Số tiền,Ghi chú\n';
      const csvData = transactions.map((t, index) => 
        `${index + 1},"${t.code}","${t.status}","${t.amount || ''}","${t.notes || ''}"`
      ).join('\n');
      
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', `attachment; filename="order-${id}.csv"`);
      res.send(csvHeader + csvData);
    } catch (error) {
      console.error("Error exporting order:", error);
      res.status(500).json({ message: "Failed to export order" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
