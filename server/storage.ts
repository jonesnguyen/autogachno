import {
  users,
  orders,
  serviceTransactions,
  systemConfig,
  adminLogs,
  userRegistrations,
  type User,
  type UpsertUser,
  type Order,
  type InsertOrder,
  type ServiceTransaction,
  type InsertServiceTransaction,
  type SystemConfig,
  type InsertSystemConfig,
  type AdminLog,
  type InsertAdminLog,
  type UserRegistration,
  type InsertUserRegistration,
} from "@shared/schema";
import { db } from "./db";
import { eq, desc, and, count, sql, like, or } from "drizzle-orm";

export interface IStorage {
  // User operations (mandatory for Replit Auth)
  getUser(id: string): Promise<User | undefined>;
  upsertUser(user: UpsertUser): Promise<User>;
  
  // Admin user management
  getAllUsers(page?: number, limit?: number, search?: string): Promise<{ users: User[], total: number }>;
  updateUserRole(id: string, role: string): Promise<User>;
  updateUserStatus(id: string, status: string): Promise<User>;
  deleteUser(id: string): Promise<void>;
  updateLastLogin(id: string): Promise<void>;
  
  // User registration operations
  createUserRegistration(registration: InsertUserRegistration): Promise<UserRegistration>;
  getUserRegistrations(status?: string): Promise<UserRegistration[]>;
  reviewUserRegistration(id: string, approved: boolean, reviewerId: string, notes?: string): Promise<UserRegistration>;
  
  // Admin logging
  createAdminLog(log: InsertAdminLog): Promise<AdminLog>;
  getAdminLogs(page?: number, limit?: number): Promise<{ logs: AdminLog[], total: number }>;
  
  // Order operations
  createOrder(order: InsertOrder): Promise<Order>;
  getOrder(id: string): Promise<Order | undefined>;
  getUserOrders(userId: string, limit?: number): Promise<Order[]>;
  updateOrderStatus(id: string, status: string, resultData?: string): Promise<Order>;
  getRecentOrders(limit?: number): Promise<Order[]>;
  getAllOrders(page?: number, limit?: number): Promise<{ orders: Order[], total: number }>;
  
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
  
  getAdminStats(): Promise<{
    totalUsers: number;
    activeUsers: number;
    totalOrders: number;
    totalRevenue: string;
    pendingRegistrations: number;
    recentActivity: AdminLog[];
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

  // Admin user management
  async getAllUsers(page = 1, limit = 20, search?: string): Promise<{ users: User[], total: number }> {
    const offset = (page - 1) * limit;
    
    let whereClause;
    if (search) {
      whereClause = or(
        like(users.email, `%${search}%`),
        like(users.firstName, `%${search}%`),
        like(users.lastName, `%${search}%`)
      );
    }

    const [usersResult, totalResult] = await Promise.all([
      db.select()
        .from(users)
        .where(whereClause)
        .orderBy(desc(users.createdAt))
        .limit(limit)
        .offset(offset),
      
      db.select({ count: count() })
        .from(users)
        .where(whereClause)
    ]);

    return {
      users: usersResult,
      total: totalResult[0].count
    };
  }

  async updateUserRole(id: string, role: string): Promise<User> {
    const [user] = await db
      .update(users)
      .set({ 
        role: role as any,
        updatedAt: new Date() 
      })
      .where(eq(users.id, id))
      .returning();
    return user;
  }

  async updateUserStatus(id: string, status: string): Promise<User> {
    const [user] = await db
      .update(users)
      .set({ 
        status: status as any,
        updatedAt: new Date() 
      })
      .where(eq(users.id, id))
      .returning();
    return user;
  }

  async deleteUser(id: string): Promise<void> {
    await db.delete(users).where(eq(users.id, id));
  }

  async updateLastLogin(id: string): Promise<void> {
    await db
      .update(users)
      .set({ lastLoginAt: new Date() })
      .where(eq(users.id, id));
  }

  // User registration operations
  async createUserRegistration(registrationData: InsertUserRegistration): Promise<UserRegistration> {
    const [registration] = await db
      .insert(userRegistrations)
      .values(registrationData)
      .returning();
    return registration;
  }

  async getUserRegistrations(status?: string): Promise<UserRegistration[]> {
    const whereClause = status ? eq(userRegistrations.status, status) : undefined;
    
    return await db
      .select()
      .from(userRegistrations)
      .where(whereClause)
      .orderBy(desc(userRegistrations.createdAt));
  }

  async reviewUserRegistration(
    id: string, 
    approved: boolean, 
    reviewerId: string, 
    notes?: string
  ): Promise<UserRegistration> {
    const [registration] = await db
      .update(userRegistrations)
      .set({
        status: approved ? 'approved' : 'rejected',
        reviewedBy: reviewerId,
        reviewedAt: new Date(),
        reviewNotes: notes,
        updatedAt: new Date()
      })
      .where(eq(userRegistrations.id, id))
      .returning();
    return registration;
  }

  // Admin logging
  async createAdminLog(logData: InsertAdminLog): Promise<AdminLog> {
    const [log] = await db
      .insert(adminLogs)
      .values(logData)
      .returning();
    return log;
  }

  async getAdminLogs(page = 1, limit = 50): Promise<{ logs: AdminLog[], total: number }> {
    const offset = (page - 1) * limit;
    
    const [logsResult, totalResult] = await Promise.all([
      db.select()
        .from(adminLogs)
        .orderBy(desc(adminLogs.createdAt))
        .limit(limit)
        .offset(offset),
      
      db.select({ count: count() })
        .from(adminLogs)
    ]);

    return {
      logs: logsResult,
      total: totalResult[0].count
    };
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

  async getAllOrders(page = 1, limit = 20): Promise<{ orders: Order[], total: number }> {
    const offset = (page - 1) * limit;
    
    const [ordersResult, totalResult] = await Promise.all([
      db.select()
        .from(orders)
        .orderBy(desc(orders.createdAt))
        .limit(limit)
        .offset(offset),
      
      db.select({ count: count() })
        .from(orders)
    ]);

    return {
      orders: ordersResult,
      total: totalResult[0].count
    };
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

  async getAdminStats(): Promise<{
    totalUsers: number;
    activeUsers: number;
    totalOrders: number;
    totalRevenue: string;
    pendingRegistrations: number;
    recentActivity: AdminLog[];
  }> {
    const [
      totalUsersResult,
      activeUsersResult,
      totalOrdersResult,
      pendingRegistrationsResult,
      recentActivityResult
    ] = await Promise.all([
      db.select({ count: count() }).from(users),
      db.select({ count: count() }).from(users).where(eq(users.status, 'active')),
      db.select({ count: count() }).from(orders),
      db.select({ count: count() }).from(userRegistrations).where(eq(userRegistrations.status, 'pending')),
      db.select().from(adminLogs).orderBy(desc(adminLogs.createdAt)).limit(10)
    ]);

    // Calculate total revenue
    const revenueResult = await db
      .select()
      .from(serviceTransactions)
      .where(eq(serviceTransactions.status, 'success'));
    
    const totalRevenue = revenueResult.reduce((sum, t) => 
      sum + (parseFloat(t.amount || '0')), 0
    );

    return {
      totalUsers: totalUsersResult[0].count,
      activeUsers: activeUsersResult[0].count,
      totalOrders: totalOrdersResult[0].count,
      totalRevenue: totalRevenue.toLocaleString('vi-VN'),
      pendingRegistrations: pendingRegistrationsResult[0].count,
      recentActivity: recentActivityResult,
    };
  }
}

export const storage = new DatabaseStorage();
