import { sql } from 'drizzle-orm';
import {
  index,
  jsonb,
  pgTable,
  timestamp,
  varchar,
  text,
  integer,
  decimal,
  pgEnum,
} from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Session storage table (mandatory for Replit Auth)
export const sessions = pgTable(
  "sessions",
  {
    sid: varchar("sid").primaryKey(),
    sess: jsonb("sess").notNull(),
    expire: timestamp("expire").notNull(),
  },
  (table) => [index("IDX_session_expire").on(table.expire)],
);

// User role enum
export const userRoleEnum = pgEnum('user_role', ['user', 'admin', 'manager']);

// User status enum
export const userStatusEnum = pgEnum('user_status', ['active', 'suspended', 'pending']);

// User storage table (mandatory for Replit Auth)
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  user: varchar("user").unique(), // Changed from email to user
  firstName: varchar("first_name"),
  lastName: varchar("last_name"),
  password: varchar("password"), // Password thuần túy thay vì hash
  profileImageUrl: varchar("profile_image_url"),
  role: userRoleEnum("role").default('user').notNull(),
  status: userStatusEnum("status").default('pending').notNull(), // Changed default from 'active' to 'pending'
  expiresAt: timestamp("expires_at"), // Thời hạn sử dụng user
  lastLoginAt: timestamp("last_login_at"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Service types enum
export const serviceTypeEnum = pgEnum('service_type', [
  'tra_cuu_ftth',
  'gach_dien_evn', 
  'nap_tien_da_mang',
  'nap_tien_viettel',
  'thanh_toan_tv_internet',
  'tra_cuu_no_tra_sau'
]);

// Order status enum
export const orderStatusEnum = pgEnum('order_status', [
  'pending',
  'processing', 
  'completed',
  'failed',
  'cancelled'
]);

// Transaction status enum
export const transactionStatusEnum = pgEnum('transaction_status', [
  'pending',
  'success',
  'failed',
  'processing'
]);

// Orders table
export const orders = pgTable("orders", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull().references(() => users.id),
  serviceType: serviceTypeEnum("service_type").notNull(),
  status: orderStatusEnum("status").notNull().default('pending'),
  totalAmount: decimal("total_amount", { precision: 15, scale: 2 }),
  inputData: text("input_data").notNull(), // JSON string of input data
  resultData: text("result_data"), // JSON string of results
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Service transactions table
export const serviceTransactions = pgTable("service_transactions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  orderId: varchar("order_id").notNull().references(() => orders.id),
  code: varchar("code").notNull(), // Phone number, bill code, etc.
  status: transactionStatusEnum("status").notNull().default('pending'),
  amount: decimal("amount", { precision: 15, scale: 2 }),
  notes: text("notes"),
  processingData: text("processing_data"), // JSON for additional data
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// System configuration table
export const systemConfig = pgTable("system_config", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  key: varchar("key").notNull().unique(),
  value: text("value").notNull(),
  description: text("description"),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Admin activity logs table
export const adminLogs = pgTable("admin_logs", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  adminId: varchar("admin_id").notNull().references(() => users.id),
  action: varchar("action").notNull(), // create_user, update_user, delete_user, etc.
  targetType: varchar("target_type").notNull(), // user, order, system_config
  targetId: varchar("target_id"),
  oldData: text("old_data"), // JSON of previous data
  newData: text("new_data"), // JSON of new data
  ipAddress: varchar("ip_address"),
  userAgent: text("user_agent"),
  createdAt: timestamp("created_at").defaultNow(),
});

// User registration requests table (for manual approval)
export const userRegistrations = pgTable("user_registrations", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  user: varchar("user").notNull().unique(), // Changed from email to user
  firstName: varchar("first_name").notNull(),
  lastName: varchar("last_name").notNull(),
  phone: varchar("phone"),
  organization: varchar("organization"),
  requestReason: text("request_reason"),
  status: varchar("status").default('pending').notNull(), // pending, approved, rejected
  reviewedBy: varchar("reviewed_by").references(() => users.id),
  reviewedAt: timestamp("reviewed_at"),
  reviewNotes: text("review_notes"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Types
export type UpsertUser = typeof users.$inferInsert;
export type User = typeof users.$inferSelect;

export type InsertOrder = typeof orders.$inferInsert;
export type Order = typeof orders.$inferSelect;

export type InsertServiceTransaction = typeof serviceTransactions.$inferInsert;
export type ServiceTransaction = typeof serviceTransactions.$inferSelect;

export type InsertSystemConfig = typeof systemConfig.$inferInsert;
export type SystemConfig = typeof systemConfig.$inferSelect;

export type InsertAdminLog = typeof adminLogs.$inferInsert;
export type AdminLog = typeof adminLogs.$inferSelect;

export type InsertUserRegistration = typeof userRegistrations.$inferInsert;
export type UserRegistration = typeof userRegistrations.$inferSelect;

// Schemas
export const insertOrderSchema = createInsertSchema(orders).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertServiceTransactionSchema = createInsertSchema(serviceTransactions).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertSystemConfigSchema = createInsertSchema(systemConfig).omit({
  id: true,
  updatedAt: true,
});

export const insertUserRegistrationSchema = createInsertSchema(userRegistrations).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
  reviewedBy: true,
  reviewedAt: true,
  reviewNotes: true,
});

// New schema for user registration with password
export const insertUserWithPasswordSchema = createInsertSchema(users).omit({
  id: true,
  profileImageUrl: true,
  role: true,
  status: true,
  lastLoginAt: true,
  createdAt: true,
  updatedAt: true,
}).extend({
  user: z.string().min(1, "Tên đăng nhập không được để trống"), // Changed from email to user
  password: z.string().min(6, "Mật khẩu phải có ít nhất 6 ký tự"),
  confirmPassword: z.string(),
  expiresAt: z.string().optional().transform((val) => val ? new Date(val) : null), // Chuyển đổi string thành Date
}).refine((data) => data.password === data.confirmPassword, {
  message: "Mật khẩu và xác nhận mật khẩu phải giống nhau",
  path: ["confirmPassword"],
});

export const insertAdminLogSchema = createInsertSchema(adminLogs).omit({
  id: true,
  createdAt: true,
});
