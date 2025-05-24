## [2025-05-24至2025-05-25] 开发报告

### 🚀 新功能开发
- 新增Conversation相关协议定义
  - 涉及文件：qbychat/websocket/conversation/v1/common.proto, qbychat/websocket/conversation/v1/service.proto
  - 提交记录：154c07cb

- 在RPCRequestMethod中添加Sync方法
  - 涉及文件：qbychat/websocket/protocol/v1/common.proto
  - 提交记录：4f1a55b0

### 🔧 代码优化
- 统一RPC命名规范为PascalCase
  - 优化类型：代码规范/可读性
  - 涉及文件：qbychat/websocket/protocol/v1/common.proto, qbychat/websocket/session/v1/common.proto
  - 提交记录：134d79ba

### ⚠️ 重要提醒
- 协议文件中RPC相关命名已统一改为PascalCase格式，需注意与旧版本客户端的兼容性问题
- 新增的Sync方法需要客户端同步更新协议定义