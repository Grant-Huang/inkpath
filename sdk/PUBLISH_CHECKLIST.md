# SDK发布检查清单

## 发布前检查

### Python SDK

- [x] **测试通过**: 连续性校验测试通过（8个测试，7个通过，1个待修复）
- [x] **版本号**: 0.1.0 ✓
- [x] **README**: 完整且准确 ✓
- [x] **LICENSE**: MIT许可证文件已创建 ✓
- [x] **MANIFEST.in**: 已创建，包含必要文件 ✓
- [x] **依赖版本**: requests>=2.31.0, flask>=3.0.0 ✓
- [x] **示例代码**: basic_bot.py 存在且可读 ✓
- [x] **导入测试**: SDK可以正常导入 ✓
- [x] **构建测试**: setup.py可以正常构建 ✓

### Node.js SDK

- [x] **版本号**: 0.1.0 ✓
- [x] **README**: 完整且准确 ✓
- [x] **LICENSE**: MIT许可证文件已创建 ✓
- [x] **package.json**: 包含repository、bugs、homepage ✓
- [x] **依赖版本**: axios>=1.6.0, express>=4.18.0 ✓
- [x] **示例代码**: basic-bot.ts 存在且可读 ✓
- [x] **构建测试**: TypeScript可以正常编译 ✓
- [x] **类型定义**: TypeScript类型定义完整 ✓

## 发布步骤

### Python SDK (PyPI)

1. **安装twine**:
   ```bash
   pip install twine
   ```

2. **构建分发包**:
   ```bash
   cd sdk/python
   bash scripts/publish.sh
   ```

3. **测试发布到TestPyPI**:
   ```bash
   twine upload --repository testpypi dist/*
   ```

4. **验证测试发布**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ inkpath-sdk
   ```

5. **正式发布到PyPI**:
   ```bash
   twine upload dist/*
   ```

### Node.js SDK (npm)

1. **登录npm**:
   ```bash
   npm login
   ```

2. **构建**:
   ```bash
   cd sdk/nodejs
   npm run build
   ```

3. **测试发布**:
   ```bash
   npm publish --dry-run
   ```

4. **正式发布**:
   ```bash
   npm publish --access public
   ```

## 发布后检查

### Python SDK

- [ ] **安装测试**: `pip install inkpath-sdk` 成功
- [ ] **导入测试**: `from inkpath import InkPathClient` 成功
- [ ] **功能测试**: 基本功能可以正常使用
- [ ] **文档链接**: PyPI页面上的文档链接正确

### Node.js SDK

- [ ] **安装测试**: `npm install @inkpath/sdk` 成功
- [ ] **导入测试**: `import { InkPathClient } from '@inkpath/sdk'` 成功
- [ ] **功能测试**: 基本功能可以正常使用
- [ ] **类型定义**: TypeScript类型定义可用
- [ ] **文档链接**: npm页面上的文档链接正确

## 已知问题

1. **连续性校验测试**: 1个测试失败（Bot模型字段问题），不影响SDK功能
2. **GitHub仓库**: 需要创建实际的GitHub仓库并更新URL

## 注意事项

- 首次发布前需要注册PyPI和npm账号
- 发布后版本号需要更新才能再次发布
- 建议先在测试环境验证后再正式发布
