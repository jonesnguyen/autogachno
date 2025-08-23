// Simple E2E test for register and dev login
const baseUrl = process.env.BASE_URL || 'http://127.0.0.1:5001';

async function main() {
  const email = `autotest_${Date.now()}@local`;
  const password = '123456';

  console.log('Testing registration and login for:', email);

  const registerBody = {
    email,
    firstName: 'Auto',
    lastName: 'Test',
    password,
    confirmPassword: password,
  };

  console.log('1. Registering user...');
  const registerRes = await fetch(`${baseUrl}/api/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(registerBody),
  });
  const registerText = await registerRes.text();
  console.log('REGISTER_STATUS:', registerRes.status);
  console.log('REGISTER_BODY:', registerText);

  if (registerRes.status !== 200) {
    throw new Error(`Registration failed: ${registerText}`);
  }

  console.log('2. Attempting login...');
  const loginRes = await fetch(`${baseUrl}/api/dev/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const loginText = await loginRes.text();
  console.log('LOGIN_STATUS:', loginRes.status);
  console.log('LOGIN_BODY:', loginText);

  if (loginRes.status === 200) {
    console.log('✅ SUCCESS: User registered and login works!');
    console.log('This means password_hash and password_salt were stored correctly.');
  } else {
    console.log('❌ FAILED: Login did not work');
    console.log('This suggests password_hash or password_salt were not stored correctly.');
  }
}

main().catch((err) => {
  console.error('TEST_ERROR:', err);
  process.exit(1);
});


