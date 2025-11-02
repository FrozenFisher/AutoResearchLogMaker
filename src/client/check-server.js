// 检查服务器连接状态
const http = require('http');

const API_BASE = process.env.VITE_API_BASE || 'http://localhost:8000';
const url = new URL(API_BASE + '/health');

console.log(`正在检查服务器连接: ${API_BASE}`);
console.log('');

const req = http.get(url, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    if (res.statusCode === 200) {
      console.log('✅ 服务器连接成功！');
      console.log(`响应: ${data}`);
      process.exit(0);
    } else {
      console.log(`❌ 服务器返回错误状态: ${res.statusCode}`);
      process.exit(1);
    }
  });
});

req.on('error', (err) => {
  console.log('❌ 无法连接到服务器');
  console.log('');
  console.log('可能的原因：');
  console.log('1. 服务器未启动');
  console.log('2. 服务器端口不是 8000');
  console.log('3. 防火墙阻止了连接');
  console.log('4. API_BASE 配置错误');
  console.log('');
  console.log(`当前配置: ${API_BASE}`);
  console.log('');
  console.log('解决方案：');
  console.log('1. 确保服务器已启动: python run_server.py');
  console.log('2. 检查服务器是否运行在 http://localhost:8000');
  console.log('3. 检查 .env 文件中的 VITE_API_BASE 配置');
  process.exit(1);
});

req.setTimeout(5000, () => {
  req.destroy();
  console.log('❌ 连接超时（5秒）');
  console.log('请确保服务器已启动');
  process.exit(1);
});
