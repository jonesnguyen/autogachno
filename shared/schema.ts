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

// User storage table (mandatory for Replit Auth)
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  email: varchar("email").unique(),
  firstName: varchar("first_name"),
  lastName: varchar("last_name"),
  profileImageUrl: varchar("profile_image_url"),
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

// Types
export type UpsertUser = typeof users.$inferInsert;
export type User = typeof users.$inferSelect;

export type InsertOrder = typeof orders.$inferInsert;
export type Order = typeof orders.$inferSelect;

export type InsertServiceTransaction = typeof serviceTransactions.$inferInsert;
export type ServiceTransaction = typeof serviceTransactions.$inferSelect;

export type InsertSystemConfig = typeof systemConfig.$inferInsert;
export type SystemConfig = typeof systemConfig.$inferSelect;

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
