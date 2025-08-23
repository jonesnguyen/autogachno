import express from 'express';
import axios from 'axios';

const router = express.Router();

// Basic Authentication credentials
const USERNAME = "Demodiemthu";
const PASSWORD = "123456";
const CREDENTIALS = Buffer.from(`${USERNAME}:${PASSWORD}`).toString('base64');

// Service types mapping
const SERVICE_TYPES: Record<string, string> = {
  'tra_cuu_ftth': 'check_ftth',
  'gach_dien_evn': 'env',
  'nap_tien_da_mang': 'deposit',
  'nap_tien_viettel': 'deposit_viettel',
  'thanh_toan_tv_internet': 'payment_tv',
  'tra_cuu_no_tra_sau': 'check_debt'
};

// Proxy endpoint để gọi API thuhohpk.com
router.get('/api/proxy/thuhohpk/:serviceType', async (req, res) => {
  try {
    const { serviceType } = req.params;
    const apiServiceType = SERVICE_TYPES[serviceType] || serviceType;
    
    const url = `https://thuhohpk.com/api/list-bill-not-completed?service_type=${apiServiceType}`;
    
    console.log(`📡 Proxy request for service: ${serviceType} -> ${apiServiceType}`);
    console.log(`🌐 Calling: ${url}`);
    
    const response = await axios.get(url, {
      headers: {
        'Authorization': `Basic ${CREDENTIALS}`,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      timeout: 30000
    });
    
    console.log(`✅ Proxy response: ${response.status}`);
    
    res.json({
      status: 'success',
      service_type: serviceType,
      data: response.data,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error(`❌ Proxy error for ${req.params.serviceType}:`, error);
    
    if (axios.isAxiosError(error)) {
      res.status(error.response?.status || 500).json({
        status: 'error',
        message: error.message,
        details: error.response?.data || 'Unknown error',
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(500).json({
        status: 'error',
        message: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      });
    }
  }
});

// Test endpoint
router.get('/api/proxy/test', (req, res) => {
  res.json({
    status: 'success',
    message: 'Proxy server is running',
    available_services: Object.keys(SERVICE_TYPES),
    timestamp: new Date().toISOString()
  });
});

// Health check endpoint
router.get('/api/proxy/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
});

export default router;
