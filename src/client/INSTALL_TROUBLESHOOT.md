# 安装问题排查指南

## SSL 证书验证错误

如果遇到 `unable to verify the first certificate` 错误，可以尝试以下解决方案：

### 方案 1：使用国内镜像源（推荐）

```bash
# 设置淘宝镜像
npm config set registry https://registry.npmmirror.com

# 设置 Electron 镜像
npm config set electron_mirror https://npmmirror.com/mirrors/electron/

# 重新安装
npm install
```

### 方案 2：临时禁用 SSL 验证（仅开发环境）

```bash
# 临时禁用严格 SSL（不推荐生产环境使用）
npm config set strict-ssl false

# 安装完成后，建议恢复
npm config set strict-ssl true
```

### 方案 3：配置 Node.js 使用系统 CA

如果您的系统 CA 证书已正确配置，可以运行：

```bash
node --use-system-ca install.js
```

或者在 `package.json` 的安装脚本中添加：

```json
"scripts": {
  "postinstall": "node --use-system-ca install.js"
}
```

### 方案 4：手动安装 Electron

如果 Electron 安装失败，可以尝试手动安装：

```bash
# 清除缓存
npm cache clean --force

# 删除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 只安装其他依赖（排除 electron）
npm install --ignore-scripts

# 然后手动安装 Electron
npm install electron --save-dev --ignore-scripts=false
```

## 权限错误（EPERM）

如果遇到文件删除权限错误，可以尝试：

### Windows

1. **以管理员身份运行命令行**
   - 右键点击命令提示符或 PowerShell
   - 选择"以管理员身份运行"

2. **关闭可能占用文件的程序**
   - 关闭 IDE（VS Code、WebStorm 等）
   - 关闭文件资源管理器中的相关文件夹
   - 检查是否有进程占用 `node_modules` 文件夹

3. **手动删除 node_modules**
   ```bash
   # PowerShell（管理员）
   Remove-Item -Recurse -Force node_modules
   
   # 然后重新安装
   npm install
   ```

4. **使用 npm 清理命令**
   ```bash
   npm cache clean --force
   ```

## 废弃包警告

这些是警告，不影响功能，但建议更新依赖：

- `eslint@8.x` → `eslint@9.x`（已在 package.json 中更新）
- `glob@7.x` → `glob@9.x`（依赖更新后会自动升级）
- `rimraf@3.x` → `rimraf@4.x`（依赖更新后会自动升级）

## 推荐安装流程

```bash
# 1. 进入客户端目录
cd src/client

# 2. 清除缓存
npm cache clean --force

# 3. 删除旧的 node_modules（如果存在）
rm -rf node_modules package-lock.json

# 4. 设置镜像源（如果网络慢）
npm config set registry https://registry.npmmirror.com
npm config set electron_mirror https://npmmirror.com/mirrors/electron/

# 5. 安装依赖
npm install

# 6. 如果 Electron 安装失败，单独安装
npm install electron --save-dev
```

## 验证安装

安装完成后，验证是否成功：

```bash
# 检查 Electron 版本
npx electron --version

# 检查其他关键依赖
npm list vue electron axios
```
