# AI智能招聘管理系统

基于「基于AI技术的招聘流程智能化落地方案」构建的交互式Demo

## 功能模块

| 模块 | 说明 |
|------|------|
| 部门总览地图 | 三个部门卡片，显示投递数/阶段分布/平均匹配度 |
| 候选人列表 | 按匹配度排序，支持部门/阶段/关键词筛选 |
| 候选人详情 | AI三段式总结、分项评分条、面试记录、工作经历 |
| 评分权重调节 | 拖动滑块调整各维度比重，实时重排候选人 |
| AI智能体问答 | 自然语言检索简历库 |
| 简历智能提取 | 粘贴简历文本，AI提取结构化信息 |
| 面评智能提取 | 粘贴面试评价，提取能力评级、观点、结论 |
| 招聘漏斗图 | 可视化展示各阶段转化数据 |

## 技术栈

- **后端**: FastAPI + Python 3.11
- **前端**: HTML/CSS/JS 单页应用，Lucide图标
- **数据**: 12位跨3部门的候选人数据

## 快速启动

```bash
pip install -r requirements.txt
python app.py
# 访问 http://127.0.0.1:8080
```

## API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/departments/overview | 部门总览 |
| GET | /api/candidates | 候选人列表(支持筛选) |
| GET | /api/candidates/{id} | 候选人详情+AI总结 |
| GET | /api/weights/{dept} | 获取部门权重 |
| POST | /api/weights/{dept} | 更新部门权重 |
| POST | /api/resume/extract | 简历智能提取 |
| POST | /api/interview/extract | 面评智能提取 |
| POST | /api/chat | AI智能体问答 |
| GET | /api/stats/overview | 全局统计 |
| GET | /api/stats/funnel | 招聘漏斗数据 |

## 部署到Render

1. Fork/Push 此仓库到你的 GitHub
2. 在 [Render.com](https://render.com) 创建新 Web Service
3. 连接你的 GitHub 仓库
4. Render 会自动识别 `render.yaml` 配置
5. 部署完成后即可获得在线链接

## 部署到Railway

1. Push 到 GitHub
2. 在 [Railway.app](https://railway.app) 创建新项目
3. 连接 GitHub 仓库
4. 启动命令: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. 部署完成
