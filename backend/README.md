# PhysicsAdvisor · Backend (Phase 1 最小骨架)

> 启动日期:2026-09-08 · 破冰 14 天零代码(P0)
> 数据源:`../data/knowledge.json` + `../data/experiments/*.md`

## 启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

打开 <http://localhost:8000/docs> 看 Swagger UI。

## 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 + 资产数 |
| GET | `/graph?limit=50` | 知识图谱(节点 + 父子边) |
| GET | `/formulas?branch=力学` | 公式列表(支持分支过滤) |
| GET | `/cases?category=故事` | 应用案例(支持分类过滤) |
| GET | `/experiments` | 经典实验(从 md 解析) |

## 依赖

- fastapi 0.115+ (macOS 系统已有 0.128.8,无需安装)
- uvicorn 0.30+

## 下一步

- [ ] 接前端 `frontend/index.html` 拉 `/graph` 渲染 D3 图谱
- [ ] Docker Compose 一键启动(deploy/)
- [ ] 飞书 OAuth 登录
- [ ] 飞书 Bot 接入"公式速查 + 概念问答"流程
