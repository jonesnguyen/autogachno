import {
  users,
  orders,
  serviceTransactions,
  systemConfig,
  type User,
  type UpsertUser,
  type Order,
  type InsertOrder,
  type ServiceTransaction,
  type InsertServiceTransaction,
  type SystemConfig,
  type InsertSystemConfig,
} from "@shared/schema";
import { db } from "./db";
import { eq, desc, and, count } from "drizzle-orm";

export interface IStorage {
  // User operations (mandatory for Replit Auth)
  getUser(id: string): Promise<User | undefined>;
  upsertUser(user: UpsertUser): Promise<User>;
  
  // Order operations
  createOrder(order: InsertOrder): Promise<Order>;
  getOrder(id: string): Promise<Order | undefined>;
  getUserOrders(userId: string, limit?: number): Promise<Order[]>;
  updateOrderStatus(id: string, status: string, resultData?: string): Promise<Order>;
  getRecentOrders(limit?: number): Promise<Order[]>;
  
  // Service transaction operations
  createServiceTransaction(transaction: InsertServiceTransaction): Promise<ServiceTransaction>;
  getOrderTransactions(orderId: string): Promise<ServiceTransaction[]>;
  updateTransactionStatus(id: string, status: string, amount?: string, notes?: string): Promise<ServiceTransaction>;
  
  // System config operations
  getSystemConfig(key: string): Promise<SystemConfig | undefined>;
  setSystemConfig(config: InsertSystemConfig): Promise<SystemConfig>;
  
  // Statistics
  getTodayStats(): Promise<{
    todayTransactions: number;
    totalRevenue: string;
    successRate: number;
    pendingOrders: number;
  }>;
}

export class DatabaseStorage implements IStorage {
  // User operations
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async upsertUser(userData: UpsertUser): Promise<User> {
    const [user] = await db
      .insert(users)
      .values(userData)
      .onConflictDoUpdate({
        target: users.id,
        set: {
          ...userData,
          updatedAt: new Date(),
        },
      })
      .returning();
    return user;
  }

  // Order operations
  async createOrder(orderData: InsertOrder): Promise<Order> {
    const [order] = await db.insert(orders).values(orderData).returning();
    return order;
  }

  async getOrder(id: string): Promise<Order | undefined> {
    const [order] = await db.select().from(orders).where(eq(orders.id, id));
    return order;
  }

  async getUserOrders(userId: string, limit = 50): Promise<Order[]> {
    return await db
      .select()
      .from(orders)
      .where(eq(orders.userId, userId))
      .orderBy(desc(orders.createdAt))
      .limit(limit);
  }

  async updateOrderStatus(id: string, status: string, resultData?: string): Promise<Order> {
    const updateData: any = { 
      status: status as any,
      updatedAt: new Date() 
    };
    if (resultData) {
      updateData.resultData = resultData;
    }
    
    const [order] = await db
      .update(orders)
      .set(updateData)
      .where(eq(orders.id, id))
      .returning();
    return order;
  }

  async getRecentOrders(limit = 10): Promise<Order[]> {
    return await db
      .select()
      .from(orders)
      .orderBy(desc(orders.createdAt))
      .limit(limit);
  }

  // Service transaction operations
  async createServiceTransaction(transactionData: InsertServiceTransaction): Promise<ServiceTransaction> {
    const [transaction] = await db
      .insert(serviceTransactions)
      .values(transactionData)
      .returning();
    return transaction;
  }

  async getOrderTransactions(orderId: string): Promise<ServiceTransaction[]> {
    return await db
      .select()
      .from(serviceTransactions)
      .where(eq(serviceTransactions.orderId, orderId))
      .orderBy(desc(serviceTransactions.createdAt));
  }

  async updateTransactionStatus(
    id: string, 
    status: string, 
    amount?: string, 
    notes?: string
  ): Promise<ServiceTransaction> {
    const updateData: any = { 
      status: status as any,
      updatedAt: new Date() 
    };
    if (amount) updateData.amount = amount;
    if (notes) updateData.notes = notes;
    
    const [transaction] = await db
      .update(serviceTransactions)
      .set(updateData)
      .where(eq(serviceTransactions.id, id))
      .returning();
    return transaction;
  }

  // System config operations
  async getSystemConfig(key: string): Promise<SystemConfig | undefined> {
    const [config] = await db
      .select()
      .from(systemConfig)
      .where(eq(systemConfig.key, key));
    return config;
  }

  async setSystemConfig(configData: InsertSystemConfig): Promise<SystemConfig> {
    const [config] = await db
      .insert(systemConfig)
      .values(configData)
      .onConflictDoUpdate({
        target: systemConfig.key,
        set: {
          value: configData.value,
          description: configData.description,
          updatedAt: new Date(),
        },
      })
      .returning();
    return config;
  }

  // Statistics
  async getTodayStats(): Promise<{
    todayTransactions: number;
    totalRevenue: string;
    successRate: number;
    pendingOrders: number;
  }> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Get today's transactions count
    const [todayCount] = await db
      .select({ count: count() })
      .from(serviceTransactions)
      .where(eq(serviceTransactions.createdAt, today));

    // Get total revenue (completed transactions)
    const revenueResult = await db
      .select()
      .from(serviceTransactions)
      .where(eq(serviceTransactions.status, 'success'));
    
    const totalRevenue = revenueResult.reduce((sum, t) => 
      sum + (parseFloat(t.amount || '0')), 0
    );

    // Get success rate
    const totalTransactions = revenueResult.length;
    const successfulTransactions = revenueResult.filter(t => t.status === 'success').length;
    const successRate = totalTransactions > 0 ? (successfulTransactions / totalTransactions) * 100 : 0;

    // Get pending orders count
    const [pendingCount] = await db
      .select({ count: count() })
      .from(orders)
      .where(eq(orders.status, 'pending'));

    return {
      todayTransactions: todayCount.count,
      totalRevenue: totalRevenue.toLocaleString('vi-VN'),
      successRate: Math.round(successRate * 10) / 10,
      pendingOrders: pendingCount.count,
    };
  }
}

export const storage = new DatabaseStorage();
