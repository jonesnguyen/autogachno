import express from 'express';

const router = express.Router();

// Mock data tương tự thuhohpk.com
const MOCK_DATA = {
  'check_ftth': {
    data: "0912345678,0912345679,0912345680,0912345681,0912345682"
  },
  'env': {
    data: "EVN001,EVN002,EVN003,EVN004,EVN005"
  },
  'deposit': {
    data: "0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618"
  },
  'deposit_viettel': {
    data: "0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618"
  },
  'payment_tv': {
    data: "0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618"
  },
  'check_debt': {
    data: "0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618,0912345618"
  }
};

// GET /api/list-bill-not-completed - Tương tự thuhohpk.com
router.get('/api/list-bill-not-completed', (req, res) => {
  try {
    const { service_type } = req.query;
    
    console.log(`📡 Mock API request for service_type: ${service_type}`);
    
    if (!service_type) {
      return res.status(400).json({
        error: "service_type parameter is required"
      });
    }
    
    const mockData = MOCK_DATA[service_type as keyof typeof MOCK_DATA];
    
    if (!mockData) {
      return res.status(400).json({
        error: `Invalid service_type: ${service_type}. Valid types: ${Object.keys(MOCK_DATA).join(', ')}`
      });
    }
    
    console.log(`✅ Mock response for ${service_type}:`, mockData);
    
    res.json(mockData);
    
  } catch (error) {
    console.error("❌ Mock API error:", error);
    res.status(500).json({
      error: "Internal server error",
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// POST /api/tool-bill-completed - Tương tự thuhohpk.com
router.post('/api/tool-bill-completed', (req, res) => {
  try {
    const { account } = req.body;
    
    console.log(`📡 Mock bill-completed request for account: ${account}`);
    
    if (!account) {
      return res.status(400).json({
        error: "account parameter is required"
      });
    }
    
    // Mock response thành công
    const response = {
      status: "success",
      message: `Bill completed for account: ${account}`,
      account: account,
      timestamp: new Date().toISOString()
    };
    
    console.log(`✅ Mock bill-completed response:`, response);
    
    res.json(response);
    
  } catch (error) {
    console.error("❌ Mock bill-completed error:", error);
    res.status(500).json({
      error: "Internal server error",
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Test endpoint
router.get('/api/mock/test', (req, res) => {
  res.json({
    message: 'Mock thuhohpk.com API is working',
    available_endpoints: [
      'GET /api/list-bill-not-completed?service_type={type}',
      'POST /api/tool-bill-completed'
    ],
    available_service_types: Object.keys(MOCK_DATA),
    mock_data_samples: MOCK_DATA,
    timestamp: new Date().toISOString()
  });
});

export default router;
