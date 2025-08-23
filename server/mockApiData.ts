// Mock API data tương đương với Python mock server
export const SAMPLE_DATA = {
  "tra_cuu_ftth": {
    "description": "Tra cứu FTTH", 
    "sample_codes": [
      "84903123456", "84903234567", "84903345678", 
      "84903456789", "84903567890", "84903678901",
      "84903789012", "84903890123", "84903901234", "84904012345"
    ]
  },
  "gach_dien_evn": {
    "description": "Gạch điện EVN",
    "sample_codes": [
      "PE01234567890", "PE01345678901", "PE01456789012",
      "PE01567890123", "PE01678901234", "PE01789012345",
      "PE01890123456", "PE01901234567", "PE02012345678", "PE02123456789"
    ],
    "default_phone": "0987654321",
    "default_pin": "123456"
  },
  "nap_tien_da_mang": {
    "description": "Nạp tiền đa mạng",
    "sample_phones": [
      "0987123456", "0988234567", "0989345678", 
      "0985456789", "0986567890", "0984678901",
      "0983789012", "0982890123", "0981901234", "0980012345"
    ],
    "sample_prepaid": [
      "0987123456|10000", "0988234567|20000", "0989345678|50000",
      "0985456789|100000", "0986567890|200000", "0984678901|300000"
    ],
    "sample_postpaid": [
      "0983789012", "0982890123", "0981901234", "0980012345"
    ],
    "default_pin": "123456",
    "default_form": "prepaid",
    "default_amount": "10000"
  },
  "nap_tien_viettel": {
    "description": "Nạp tiền mạng Viettel",
    "sample_phones": [
      "0967123456", "0968234567", "0969345678",
      "0965456789", "0966567890", "0964678901", 
      "0963789012", "0962890123", "0961901234", "0960012345"
    ],
    "default_pin": "123456",
    "default_amount": "100000"
  },
  "thanh_toan_tv_internet": {
    "description": "Thanh toán TV - Internet",
    "sample_codes": [
      "HTV001234567", "HTV002345678", "HTV003456789",
      "HTV004567890", "HTV005678901", "HTV006789012",
      "HTV007890123", "HTV008901234", "HTV009012345", "HTV010123456"
    ],
    "default_pin": "123456"
  },
  "tra_cuu_no_tra_sau": {
    "description": "Tra cứu nợ thuê bao trả sau",
    "sample_phones": [
      "0977123456", "0978234567", "0979345678",
      "0975456789", "0976567890", "0974678901",
      "0973789012", "0972890123", "0971901234", "0970012345"
    ]
  }
};

function getRandomSample<T>(array: T[], min: number, max: number): T[] {
  const count = Math.floor(Math.random() * (max - min + 1)) + min;
  const shuffled = [...array].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

export function getMockServiceData(serviceType: string) {
  const serviceData = SAMPLE_DATA[serviceType as keyof typeof SAMPLE_DATA];
  
  if (!serviceData) {
    throw new Error(`Service type ${serviceType} not found`);
  }

  // Tạo response data tùy theo loại dịch vụ
  switch (serviceType) {
    case "tra_cuu_ftth":
      return {
        status: "success",
        service: serviceData.description,
        data: {
          subscriber_codes: getRandomSample(serviceData.sample_codes, 3, 7)
        }
      };
      
    case "gach_dien_evn":
      return {
        status: "success", 
        service: serviceData.description,
        data: {
          bill_codes: getRandomSample(serviceData.sample_codes, 3, 6),
          receiver_phone: serviceData.default_phone,
          pin: serviceData.default_pin
        }
      };
      
    case "nap_tien_da_mang":
      // Trả về cả 2 loại dữ liệu: nạp trả trước và gạch nợ trả sau
      const multiNetworkData = serviceData as any;
      const prepaidSamples = getRandomSample(multiNetworkData.sample_prepaid, 2, 4);
      const postpaidSamples = getRandomSample(multiNetworkData.sample_postpaid, 2, 4);
      const allSamples = [...prepaidSamples, ...postpaidSamples];
      
      return {
        status: "success",
        service: serviceData.description, 
        data: {
          phone_numbers: allSamples.map((code: string) => code.includes('|') ? code.split('|')[0] : code),
          phone_amount_pairs: allSamples,
          pin: multiNetworkData.default_pin,
          payment_type: multiNetworkData.default_form,
          amount: multiNetworkData.default_amount
        }
      };
      
    case "nap_tien_viettel":
      return {
        status: "success",
        service: serviceData.description,
        data: {
          phone_numbers: getRandomSample(serviceData.sample_phones, 4, 8),
          pin: serviceData.default_pin,
          amount: serviceData.default_amount
        }
      };
      
    case "thanh_toan_tv_internet":
      return {
        status: "success",
        service: serviceData.description,
        data: {
          subscriber_codes: getRandomSample(serviceData.sample_codes, 3, 7),
          pin: serviceData.default_pin
        }
      };
      
    case "tra_cuu_no_tra_sau":
      return {
        status: "success",
        service: serviceData.description,
        data: {
          phone_numbers: getRandomSample(serviceData.sample_phones, 5, 9)
        }
      };
      
    default:
      throw new Error(`Unknown service type: ${serviceType}`);
  }
}