import { db } from './db';
import {
  users,
  orders,
  serviceTransactions,
  type InsertOrder,
  type InsertServiceTransaction,
} from '@shared/schema';
import { getMockServiceData } from './mockApiData';

async function ensureUser(id: string, user: string) {
  // Minimal insert if not exists
  const existing = await db.select().from(users).where(users.id.eq(id)).limit(1);
  if (existing.length === 0) {
    await db.insert(users).values({ id, user, firstName: 'Seed', lastName: 'User', role: 'admin', status: 'active' as any });
  }
}

function sampleCodesFor(serviceType: string): string[] {
  const data = getMockServiceData(serviceType as any).data as any;
  if (data.subscriber_codes) return data.subscriber_codes;
  if (data.bill_codes) return data.bill_codes;
  if (data.phone_numbers) return data.phone_numbers;
  return [];
}

async function seedService(serviceType: string, userId: string) {
  const codes = sampleCodesFor(serviceType).slice(0, 10);
  if (codes.length === 0) return;

  const inputData = {
    codes,
  };

  const [order] = await db
    .insert(orders)
    .values({
      userId,
      serviceType: serviceType as any,
      status: 'pending' as any,
      inputData: JSON.stringify(inputData),
    } satisfies InsertOrder)
    .returning();

  const txValues: InsertServiceTransaction[] = codes.map((code) => ({
    orderId: order.id,
    code,
    status: 'pending' as any,
  }));
  await db.insert(serviceTransactions).values(txValues);
  return order.id;
}

async function main() {
  const userId = 'admin-local';
  const user = 'Demodiemthu';
  await ensureUser(userId, user);

  const services = [
    'tra_cuu_ftth',
    'gach_dien_evn',
    'nap_tien_da_mang',
    'nap_tien_viettel',
    'thanh_toan_tv_internet',
    'tra_cuu_no_tra_sau',
  ];

  const created: string[] = [];
  for (const s of services) {
    const id = await seedService(s, userId);
    if (id) created.push(id);
  }

  // eslint-disable-next-line no-console
  console.log('Seeded orders:', created);
  process.exit(0);
}

main().catch((err) => {
  // eslint-disable-next-line no-console
  console.error(err);
  process.exit(1);
});



