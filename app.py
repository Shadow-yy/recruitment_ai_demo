"""
AI招聘流程智能化管理系统 - FastAPI后端
基于「基于AI技术的招聘流程智能化落地方案」构建
作者: 王影影
"""
import json
import os
import random
import re
import copy
from typing import Optional
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# ==================== 应用初始化 ====================
app = FastAPI(title="AI智能招聘管理系统", docs_url="/api/docs")
templates = Jinja2Templates(directory="templates")

# ==================== 样板数据 ====================
DEPARTMENTS = {
    "tech": {"name": "技术研发部", "icon": "laptop"},
    "product": {"name": "产品运营部", "icon": "pie-chart"},
    "market": {"name": "市场销售部", "icon": "trending-up"},
}

WEIGHT_TEMPLATES = {
    "tech": {
        "tech_ability": {"label": "技术能力", "value": 50, "max": 100},
        "project_exp": {"label": "项目经验", "value": 30, "max": 100},
        "education": {"label": "学历背景", "value": 10, "max": 100},
        "soft_skill": {"label": "软技能", "value": 10, "max": 100},
    },
    "product": {
        "related_exp": {"label": "相关经验", "value": 40, "max": 100},
        "soft_skill": {"label": "软技能", "value": 30, "max": 100},
        "project_result": {"label": "项目成果", "value": 20, "max": 100},
        "education": {"label": "学历", "value": 10, "max": 100},
    },
    "market": {
        "industry_exp": {"label": "行业经验", "value": 40, "max": 100},
        "performance": {"label": "业绩成果", "value": 35, "max": 100},
        "soft_skill": {"label": "软技能", "value": 20, "max": 100},
        "education": {"label": "学历", "value": 5, "max": 100},
    },
}

# 候选人数据
CANDIDATES = [
    {
        "id": 1, "name": "张明", "gender": "男", "age": 28,
        "education": "硕士", "school": "华中科技大学",
        "work_years": 5, "phone": "138****1234",
        "target_position": "高级Java开发工程师", "dept": "tech",
        "stage": "终面", "city": "武汉",
        "skills": ["Java", "Spring Boot", "微服务", "MySQL", "Redis", "Kubernetes"],
        "work_exp": [
            {"company": "字节跳动", "position": "Java开发工程师", "duration": "2022-2026", "summary": "负责核心交易系统微服务改造，QPS提升300%"},
            {"company": "美团", "position": "Java开发工程师", "duration": "2020-2022", "summary": "参与订单中台建设，支撑日均百万级订单"},
        ],
        "projects": [
            {"name": "分布式交易中台", "role": "核心开发", "desc": "设计并实现高并发交易处理系统，支持5000+QPS"},
        ],
        "interview_scores": {"tech_ability": 92, "project_exp": 88, "education": 85, "soft_skill": 78},
        "interview_notes": [
            {"round": "初试", "interviewer": "李总", "comment": "技术栈扎实，分布式经验丰富，沟通表达清晰", "verdict": "通过"},
            {"round": "复试", "interviewer": "王总", "comment": "系统设计能力强，有架构视野，推荐终面", "verdict": "通过"},
        ],
        "expected_salary": "35K-45K", "available_date": "随时到岗",
    },
    {
        "id": 2, "name": "李雪", "gender": "女", "age": 26,
        "education": "本科", "school": "武汉大学",
        "work_years": 3, "phone": "139****5678",
        "target_position": "Java开发工程师", "dept": "tech",
        "stage": "初试", "city": "武汉",
        "skills": ["Java", "Spring Cloud", "MyBatis", "Docker", "消息队列"],
        "work_exp": [
            {"company": "腾讯云", "position": "后端开发", "duration": "2023-2026", "summary": "负责云监控平台后端开发，日处理日志10TB+"},
        ],
        "projects": [
            {"name": "智能监控告警平台", "role": "后端开发", "desc": "实现多维度指标采集、告警规则引擎、通知分派"},
        ],
        "interview_scores": {"tech_ability": 85, "project_exp": 78, "education": 80, "soft_skill": 82},
        "interview_notes": [
            {"round": "初试", "interviewer": "李总", "comment": "基础扎实，有独立攻坚能力，建议进入复试", "verdict": "通过"},
        ],
        "expected_salary": "20K-28K", "available_date": "一个月内到岗",
    },
    {
        "id": 3, "name": "王浩", "gender": "男", "age": 32,
        "education": "硕士", "school": "浙江大学",
        "work_years": 8, "phone": "137****9012",
        "target_position": "技术总监", "dept": "tech",
        "stage": "offer", "city": "杭州",
        "skills": ["架构设计", "团队管理", "Java", "Go", "云原生", "DevOps", "大数据"],
        "work_exp": [
            {"company": "阿里巴巴", "position": "技术专家", "duration": "2020-2026", "summary": "负责电商中台架构升级，带领15人团队"},
            {"company": "网易", "position": "高级开发", "duration": "2018-2020", "summary": "参与游戏平台基础设施搭建"},
        ],
        "projects": [
            {"name": "全链路压测平台", "role": "技术负责人", "desc": "从0到1搭建全链路压测体系，覆盖200+核心服务"},
        ],
        "interview_scores": {"tech_ability": 95, "project_exp": 92, "education": 88, "soft_skill": 80},
        "interview_notes": [
            {"round": "初试", "interviewer": "李总", "comment": "技术视野开阔，管理经验丰富", "verdict": "通过"},
            {"round": "复试", "interviewer": "王总", "comment": "架构能力突出，团队管理经验扎实，强烈推荐", "verdict": "通过"},
            {"round": "终面", "interviewer": "CEO", "comment": "综合素质优秀，已发offer", "verdict": "通过"},
        ],
        "expected_salary": "60K-80K", "available_date": "两个月内到岗",
    },
    {
        "id": 4, "name": "陈静", "gender": "女", "age": 27,
        "education": "本科", "school": "厦门大学",
        "work_years": 4, "phone": "136****3456",
        "target_position": "产品经理", "dept": "product",
        "stage": "复试", "city": "厦门",
        "skills": ["用户研究", "数据分析", "Axure", "项目管理", "A/B测试", "用户增长"],
        "work_exp": [
            {"company": "小红书", "position": "产品经理", "duration": "2022-2026", "summary": "负责社区增长产品，DAU从200万提升至500万"},
            {"company": "哔哩哔哩", "position": "产品助理", "duration": "2020-2022", "summary": "参与创作者激励体系搭建"},
        ],
        "projects": [
            {"name": "社区用户增长体系", "role": "产品负责人", "desc": "主导推荐分发策略优化、社交裂变玩法设计，带动DAU增长150%"},
        ],
        "interview_scores": {"related_exp": 90, "soft_skill": 85, "project_result": 88, "education": 75},
        "interview_notes": [
            {"round": "初试", "interviewer": "张总", "comment": "产品sense好，数据驱动思维强，逻辑清晰", "verdict": "通过"},
            {"round": "复试", "interviewer": "刘总", "comment": "增长策略经验丰富，沟通协作能力强", "verdict": "通过"},
        ],
        "expected_salary": "25K-35K", "available_date": "一个月内到岗",
    },
    {
        "id": 5, "name": "刘洋", "gender": "男", "age": 25,
        "education": "本科", "school": "南京大学",
        "work_years": 2, "phone": "135****7890",
        "target_position": "产品运营", "dept": "product",
        "stage": "初试", "city": "南京",
        "skills": ["社群运营", "内容策划", "数据分析", "用户调研", "活动运营"],
        "work_exp": [
            {"company": "字节跳动", "position": "运营专员", "duration": "2024-2026", "summary": "负责教育线用户运营，月活提升40%"},
        ],
        "projects": [
            {"name": "用户分层运营策略", "role": "运营执行", "desc": "基于RFM模型制定差异化运营策略，转化率提升25%"},
        ],
        "interview_scores": {"related_exp": 75, "soft_skill": 78, "project_result": 72, "education": 70},
        "interview_notes": [
            {"round": "初试", "interviewer": "张总", "comment": "学习能力强，有数据分析基础，运营思路清晰", "verdict": "通过"},
        ],
        "expected_salary": "15K-20K", "available_date": "两周内到岗",
    },
    {
        "id": 6, "name": "赵丽", "gender": "女", "age": 30,
        "education": "硕士", "school": "北京大学",
        "work_years": 6, "phone": "134****2345",
        "target_position": "产品总监", "dept": "product",
        "stage": "终面", "city": "北京",
        "skills": ["产品战略", "团队管理", "商业分析", "用户研究", "敏捷开发", "OKR管理"],
        "work_exp": [
            {"company": "腾讯", "position": "高级产品经理", "duration": "2020-2026", "summary": "负责微信生态产品规划，带领8人产品团队"},
            {"company": "百度", "position": "产品经理", "duration": "2018-2020", "summary": "参与百度智能小程序产品设计"},
        ],
        "projects": [
            {"name": "微信小程序开放平台", "role": "产品负责人", "desc": "负责开发者生态产品规划，接入30万+开发者"},
        ],
        "interview_scores": {"related_exp": 92, "soft_skill": 90, "project_result": 92, "education": 88},
        "interview_notes": [
            {"round": "初试", "interviewer": "张总", "comment": "产品视野开阔，战略思维强，带团队经验丰富", "verdict": "通过"},
            {"round": "复试", "interviewer": "刘总", "comment": "商业嗅觉敏锐，有平台级产品经验，强烈推荐", "verdict": "通过"},
            {"round": "终面", "interviewer": "CEO", "comment": "综合素质高，正在谈offer细节", "verdict": "待定"},
        ],
        "expected_salary": "50K-70K", "available_date": "三个月内到岗",
    },
    {
        "id": 7, "name": "孙强", "gender": "男", "age": 29,
        "education": "本科", "school": "上海交通大学",
        "work_years": 6, "phone": "133****6789",
        "target_position": "销售总监", "dept": "market",
        "stage": "复试", "city": "上海",
        "skills": ["大客户销售", "团队管理", "商务谈判", "CRM", "渠道拓展", "招投标"],
        "work_exp": [
            {"company": "华为", "position": "销售经理", "duration": "2021-2026", "summary": "负责华东区政企客户，年签单额8000万+"},
            {"company": "中兴通讯", "position": "销售代表", "duration": "2019-2021", "summary": "负责运营商客户，年业绩500万+"},
        ],
        "projects": [
            {"name": "某省政务云项目", "role": "销售负责人", "desc": "主导3亿元政务云项目从跟进到签单全流程"},
        ],
        "interview_scores": {"industry_exp": 88, "performance": 90, "soft_skill": 82, "education": 70},
        "interview_notes": [
            {"round": "初试", "interviewer": "陈总", "comment": "大客户销售经验丰富，客情关系维护能力强", "verdict": "通过"},
            {"round": "复试", "interviewer": "周总", "comment": "行业资源丰富，销售策略清晰，抗压能力好", "verdict": "通过"},
        ],
        "expected_salary": "40K-55K", "available_date": "一个月内到岗",
    },
    {
        "id": 8, "name": "周敏", "gender": "女", "age": 27,
        "education": "本科", "school": "中山大学",
        "work_years": 4, "phone": "132****0123",
        "target_position": "市场经理", "dept": "market",
        "stage": "初试", "city": "广州",
        "skills": ["市场策划", "品牌营销", "数字营销", "SEO/SEM", "内容营销", "活动策划"],
        "work_exp": [
            {"company": "宝洁", "position": "品牌经理", "duration": "2022-2026", "summary": "负责旗下美妆品牌数字营销，年度预算2000万"},
            {"company": "联合利华", "position": "市场助理", "duration": "2020-2022", "summary": "参与新品上市推广策划"},
        ],
        "projects": [
            {"name": "618大促整合营销", "role": "项目负责人", "desc": "策划全渠道整合营销方案，GMV同比增长180%"},
        ],
        "interview_scores": {"industry_exp": 82, "performance": 78, "soft_skill": 80, "education": 75},
        "interview_notes": [
            {"round": "初试", "interviewer": "陈总", "comment": "品牌营销经验扎实，数据分析能力强，执行力好", "verdict": "通过"},
        ],
        "expected_salary": "20K-30K", "available_date": "一个月内到岗",
    },
    {
        "id": 9, "name": "吴刚", "gender": "男", "age": 35,
        "education": "硕士", "school": "清华大学",
        "work_years": 10, "phone": "131****4567",
        "target_position": "销售VP", "dept": "market",
        "stage": "终面", "city": "北京",
        "skills": ["销售管理", "战略规划", "渠道建设", "大客户经营", "团队激励", "商业谈判"],
        "work_exp": [
            {"company": "阿里云", "position": "销售总监", "duration": "2018-2026", "summary": "负责北方大区销售，团队60人，年营收5亿+"},
            {"company": "SAP", "position": "高级销售经理", "duration": "2015-2018", "summary": "负责华北区企业级客户，年度业绩1.2亿"},
        ],
        "projects": [
            {"name": "某大型央企数字化转型", "role": "项目总负责人", "desc": "主导2.5亿元企业数字化转型项目销售及交付"},
        ],
        "interview_scores": {"industry_exp": 95, "performance": 92, "soft_skill": 88, "education": 85},
        "interview_notes": [
            {"round": "初试", "interviewer": "陈总", "comment": "行业经验非常丰富，战略视野好", "verdict": "通过"},
            {"round": "复试", "interviewer": "周总", "comment": "销售管理能力突出，大客户资源丰富，强烈推荐", "verdict": "通过"},
            {"round": "终面", "interviewer": "CEO", "comment": "综合素质优秀，正在谈薪资", "verdict": "待定"},
        ],
        "expected_salary": "80K-100K", "available_date": "协商到岗",
    },
    {
        "id": 10, "name": "郑婷", "gender": "女", "age": 24,
        "education": "本科", "school": "四川大学",
        "work_years": 1, "phone": "130****8901",
        "target_position": "前端开发工程师", "dept": "tech",
        "stage": "简历初筛", "city": "成都",
        "skills": ["Vue.js", "React", "TypeScript", "Webpack", "CSS3", "Node.js"],
        "work_exp": [
            {"company": "字节跳动", "position": "前端开发实习生", "duration": "2025-2026", "summary": "参与飞书前端组件库开发与维护"},
        ],
        "projects": [
            {"name": "企业级组件库建设", "role": "前端开发", "desc": "参与50+通用组件开发，提升团队研发效率30%"},
        ],
        "interview_scores": {"tech_ability": 72, "project_exp": 65, "education": 78, "soft_skill": 70},
        "interview_notes": [
            {"round": "简历初筛", "interviewer": "HR", "comment": "基础扎实，有字节跳动实习经历，技术栈匹配", "verdict": "通过"},
        ],
        "expected_salary": "12K-18K", "available_date": "随时到岗",
    },
    {
        "id": 11, "name": "许峰", "gender": "男", "age": 31,
        "education": "硕士", "school": "南京邮电大学",
        "work_years": 7, "phone": "159****2345",
        "target_position": "高级产品经理", "dept": "product",
        "stage": "初试", "city": "南京",
        "skills": ["产品规划", "数据分析", "用户增长", "竞品分析", "PRD撰写", "敏捷开发"],
        "work_exp": [
            {"company": "滴滴出行", "position": "高级产品经理", "duration": "2021-2026", "summary": "负责司机端增长产品，提升司机留存率15%"},
            {"company": "去哪儿网", "position": "产品经理", "duration": "2019-2021", "summary": "负责酒店业务线产品迭代"},
        ],
        "projects": [
            {"name": "司机成长激励体系", "role": "产品负责人", "desc": "设计司机分层激励模型，核心司机留存率提升至85%"},
        ],
        "interview_scores": {"related_exp": 82, "soft_skill": 76, "project_result": 80, "education": 78},
        "interview_notes": [
            {"round": "初试", "interviewer": "张总", "comment": "产品方法论扎实，数据驱动意识强，待考察创新思维", "verdict": "通过"},
        ],
        "expected_salary": "30K-40K", "available_date": "一个月内到岗",
    },
    {
        "id": 12, "name": "黄磊", "gender": "男", "age": 33,
        "education": "本科", "school": "北京邮电大学",
        "work_years": 8, "phone": "158****6789",
        "target_position": "销售经理", "dept": "market",
        "stage": "offer", "city": "北京",
        "skills": ["企业客户开发", "解决方案销售", "商务谈判", "CRM管理", "渠道管理"],
        "work_exp": [
            {"company": "用友网络", "position": "销售经理", "duration": "2020-2026", "summary": "负责华北区ERP产品销售，年业绩3000万"},
            {"company": "金蝶国际", "position": "销售顾问", "duration": "2017-2020", "summary": "负责中小企业客户拓展"},
        ],
        "projects": [
            {"name": "某大型制造企业ERP项目", "role": "销售负责人", "desc": "主导800万ERP项目从方案到签单全流程"},
        ],
        "interview_scores": {"industry_exp": 85, "performance": 80, "soft_skill": 78, "education": 68},
        "interview_notes": [
            {"round": "初试", "interviewer": "陈总", "comment": "行业经验匹配，业绩稳定，客户资源良好", "verdict": "通过"},
            {"round": "复试", "interviewer": "周总", "comment": "销售能力扎实，团队协作好，已发offer", "verdict": "通过"},
        ],
        "expected_salary": "30K-45K", "available_date": "两周内到岗",
    },
]

# 面试历史记录（模拟）
INTERVIEW_HISTORY = []

# 当前权重（可用户调整）
_current_weights = copy.deepcopy(WEIGHT_TEMPLATES)

# ==================== 辅助函数 ====================

def compute_score(candidate, dept, weights_override=None):
    """根据部门权重计算综合匹配度得分"""
    if weights_override:
        weights = weights_override
    else:
        weights = _current_weights.get(dept, WEIGHT_TEMPLATES[dept])
    
    scores = candidate.get("interview_scores", {})
    total_weight = sum(w["value"] for w in weights.values())
    if total_weight == 0:
        return 0
    
    weighted_sum = 0
    for key, weight_info in weights.items():
        score = scores.get(key, 0)
        weighted_sum += score * (weight_info["value"] / total_weight)
    return round(weighted_sum, 1)


def generate_summary(candidate, dept):
    """生成标准化三段式智能总结"""
    dept_name = DEPARTMENTS[dept]["name"]
    score = compute_score(candidate, dept)
    
    gender_word = "男" if candidate["gender"] == "男" else "女"
    basic = f"{candidate['name']}，{gender_word}，{candidate['age']}岁，{candidate['work_years']}年{candidate['target_position']}经验，毕业于{candidate['school']}（{candidate['education']}），目标岗位{candidate['target_position']}，投递{dept_name}，整体匹配度{score}分，当前阶段：{candidate['stage']}。"
    
    skills_str = "、".join(candidate["skills"][:4])
    exp_highlights = []
    for exp in candidate.get("work_exp", []):
        exp_highlights.append(f"{exp['company']}担任{exp['position']}（{exp['duration']}）：{exp['summary']}")
    exp_text = "；".join(exp_highlights)
    
    ability = f"核心优势：具备{skills_str}等核心技能。核心经历：{exp_text}。核心优势为{candidate['skills'][0]}能力突出，在{candidate['work_exp'][0]['company']}期间{candidate['work_exp'][0]['summary']}，表现出较强的实践能力。"
    
    last_note = candidate["interview_notes"][-1] if candidate["interview_notes"] else None
    if last_note:
        scores_detail = "；".join([f"{v['label']}{candidate['interview_scores'].get(k, 0)}分" for k, v in WEIGHT_TEMPLATES[dept].items()])
        extra = f"面试官评价：{last_note['comment']}（{last_note['round']}-{last_note['interviewer']}）。各维度评分：{scores_detail}。当前结论：{last_note['verdict']}。"
    else:
        extra = "暂无面试评价记录，建议尽快安排面试。"
    
    return {"basic": basic, "ability": ability, "extra": extra}


def ai_chat_search(query, dept_filter=None):
    query_lower = query.lower()
    results = []
    
    for c in CANDIDATES:
        if dept_filter and c["dept"] != dept_filter:
            continue
        
        score = compute_score(c, c["dept"])
        
        keywords = [c["name"], c["target_position"], str(c["work_years"]) + "年"] + c["skills"]
        matched = any(k in query for k in keywords) or any(k in query for k in c["skills"])
        matched = matched or query in c["name"] or c["target_position"] in query
        
        if matched:
            results.append({
                "id": c["id"], "name": c["name"], "position": c["target_position"],
                "dept": DEPARTMENTS[c["dept"]]["name"], "score": score,
                "stage": c["stage"], "skills": c["skills"][:3],
                "work_years": c["work_years"], "education": c["education"],
            })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]


# ==================== API 路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    from pathlib import Path
    html_path = Path(__file__).parent / "templates" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/departments/overview")
async def get_department_overview():
    overview = {}
    for dept_id, dept_info in DEPARTMENTS.items():
        candidates = [c for c in CANDIDATES if c["dept"] == dept_id]
        stages = {}
        for c in candidates:
            s = c["stage"]
            stages[s] = stages.get(s, 0) + 1
        
        scores = [compute_score(c, dept_id) for c in candidates]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        
        overview[dept_id] = {
            "name": dept_info["name"],
            "icon": dept_info["icon"],
            "total": len(candidates),
            "stages": stages,
            "avg_score": avg_score,
            "top_candidate": max(candidates, key=lambda c: compute_score(c, dept_id))["name"] if candidates else "",
            "passed_count": sum(1 for c in candidates if c["stage"] in ["终面", "offer"]),
        }
    return overview


@app.get("/api/candidates")
async def list_candidates(
    dept: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("score_desc"),
    keyword: Optional[str] = Query(""),
    min_score: Optional[float] = Query(0),
):
    result = []
    for c in CANDIDATES:
        if dept and c["dept"] != dept:
            continue
        if stage and c["stage"] != stage:
            continue
        if keyword and keyword not in c["name"] and keyword not in c["target_position"] and keyword not in " ".join(c["skills"]):
            continue
        
        score = compute_score(c, c["dept"])
        if score < min_score:
            continue
        
        result.append({
            "id": c["id"], "name": c["name"], "gender": c["gender"], "age": c["age"],
            "education": c["education"], "school": c["school"], "work_years": c["work_years"],
            "target_position": c["target_position"], "dept": c["dept"],
            "dept_name": DEPARTMENTS[c["dept"]]["name"], "stage": c["stage"],
            "score": score, "skills": c["skills"][:4],
            "city": c["city"],
        })
    
    if sort_by == "score_desc":
        result.sort(key=lambda x: x["score"], reverse=True)
    elif sort_by == "score_asc":
        result.sort(key=lambda x: x["score"])
    elif sort_by == "name":
        result.sort(key=lambda x: x["name"])
    elif sort_by == "work_years_desc":
        result.sort(key=lambda x: x["work_years"], reverse=True)
    
    return result


@app.get("/api/candidates/{candidate_id}")
async def get_candidate_detail(candidate_id: int):
    for c in CANDIDATES:
        if c["id"] == candidate_id:
            score = compute_score(c, c["dept"])
            summary = generate_summary(c, c["dept"])
            detail = {k: v for k, v in c.items()}
            detail["score"] = score
            detail["summary"] = summary
            detail["dept_name"] = DEPARTMENTS[c["dept"]]["name"]
            detail["score_detail"] = {
                WEIGHT_TEMPLATES[c["dept"]][k]["label"]: {"score": v, "weight": WEIGHT_TEMPLATES[c["dept"]][k]["value"]}
                for k, v in c["interview_scores"].items()
            }
            return detail
    return JSONResponse({"error": "候选人不存在"}, status_code=404)


@app.get("/api/summary/{candidate_id}")
async def get_summary(candidate_id: int):
    for c in CANDIDATES:
        if c["id"] == candidate_id:
            return generate_summary(c, c["dept"])
    return JSONResponse({"error": "候选人不存在"}, status_code=404)


@app.get("/api/weights/{dept}")
async def get_weights(dept: str):
    if dept not in _current_weights:
        return JSONResponse({"error": "部门不存在"}, status_code=404)
    return _current_weights[dept]


class WeightItem(BaseModel):
    value: float

class WeightsUpdate(BaseModel):
    weights: dict

@app.post("/api/weights/{dept}")
async def update_weights(dept: str, data: WeightsUpdate):
    if dept not in _current_weights:
        return JSONResponse({"error": "部门不存在"}, status_code=404)
    
    for key, item in data.weights.items():
        if key in _current_weights[dept]:
            _current_weights[dept][key]["value"] = max(0, min(100, item.get("value", _current_weights[dept][key]["value"])))
    
    return _current_weights[dept]


class ResumeText(BaseModel):
    text: str

@app.post("/api/resume/extract")
async def extract_resume(data: ResumeText):
    text = data.text
    extracted = {"基础信息": {}, "技能标签": [], "职业经历": [], "求职意向": {}}
    
    name_match = re.search(r'姓名[：:]\s*(\S+)', text) or re.search(r'^(\S{2,4})[，,\s]', text)
    if name_match:
        extracted["基础信息"]["姓名"] = name_match.group(1).strip()
    
    edu_match = re.search(r'(本科|硕士|博士|大专)', text)
    if edu_match:
        extracted["基础信息"]["学历"] = edu_match.group(1)
    
    school_match = re.search(r'(大学|学院)', text)
    if school_match:
        start = max(0, school_match.start() - 8)
        extracted["基础信息"]["毕业院校"] = text[start:school_match.end()].strip()
    
    phone_match = re.search(r'1[3-9]\d{9}', text)
    if phone_match:
        extracted["基础信息"]["联系方式"] = phone_match.group(0)
    
    exp_match = re.search(r'(\d+)\s*年', text)
    if exp_match:
        extracted["基础信息"]["工作年限"] = exp_match.group(0)
    
    common_skills = ["Java", "Python", "Vue.js", "React", "Spring", "MySQL", "Docker", "Kubernetes", "数据分析", "项目管理", "Axure", "CRM", "Photoshop", "TypeScript"]
    for skill in common_skills:
        if skill in text:
            extracted["技能标签"].append(skill)
    
    companies = re.findall(r'([\u4e00-\u9fa5]{2,6}(?:公司|集团|科技|有限))', text)
    for comp in companies:
        extracted["职业经历"].append({"公司": comp, "职位": "待识别", "时间": "待识别"})
    
    return extracted


class InterviewText(BaseModel):
    text: str
    candidate_id: Optional[int] = None

@app.post("/api/interview/extract")
async def extract_interview(data: InterviewText):
    text = data.text
    
    verdicts = ["通过", "复试", "待定", "不通过"]
    detected_verdict = "待定"
    for v in verdicts:
        if v in text:
            detected_verdict = v
            break
    
    result = {
        "原始面评": text,
        "提取维度": {
            "技术能力": "待评估",
            "沟通表达": "待评估",
            "逻辑思维": "待评估",
            "团队协作": "待评估",
            "岗位匹配度": "待评估",
        },
        "面试官核心观点": [],
        "建议结论": detected_verdict,
    }
    
    rating_map = {"扎实": "优秀", "良好": "良好", "一般": "一般", "较强": "良好", "突出": "优秀"}
    for dim in ["技术能力", "沟通表达", "逻辑思维", "团队协作", "岗位匹配度"]:
        for kw, rating in rating_map.items():
            if kw in text:
                result["提取维度"][dim] = rating
                break
    
    sentences = re.split(r'[。，；]', text)
    for s in sentences:
        s = s.strip()
        if len(s) > 4 and any(kw in s for kw in ["经验丰富", "能力强", "突出", "优秀", "扎实", "待考察", "需要"]):
            result["面试官核心观点"].append(s)
    
    if not result["面试官核心观点"]:
        result["面试官核心观点"] = [text[:30] + "..."]
    
    INTERVIEW_HISTORY.append(result)
    
    return result


class ChatMessage(BaseModel):
    message: str
    dept: Optional[str] = None

@app.post("/api/chat")
async def chat_agent(data: ChatMessage):
    msg = data.message
    
    results = ai_chat_search(msg, data.dept)
    
    if not results:
        broad_results = ai_chat_search(msg.replace("的", "").replace("有", "").replace("年", ""))
        results = broad_results if broad_results else []
    
    if not results:
        answer = "抱歉，没有找到匹配的候选人信息。您可以换个关键词试试，比如：'找技术部Java开发'、'产品经理有哪些候选人'、'本月简历统计'等。"
    else:
        if len(results) == 1:
            r = results[0]
            answer = f"为您找到1位匹配候选人：{r['name']}，{r['position']}，{r['dept']}，匹配度{r['score']}分，当前阶段：{r['stage']}。核心技能：{'、'.join(r['skills'])}。"
        else:
            answer = f"为您找到 {len(results)} 位匹配候选人，按匹配度排序如下：\n"
            for i, r in enumerate(results[:5], 1):
                answer += f"\n{i}. {r['name']} - {r['position']}（{r['dept']}） - 匹配度{r['score']}分 - {r['stage']}"
            if len(results) > 5:
                answer += f"\n...及其他 {len(results) - 5} 位候选人"
    
    suggestions = [
        f"看看{results[0]['dept']}更多候选人" if results else "找技术部候选人",
        "本月招聘数据统计",
        "帮我对比得分最高的两位",
    ]
    
    return {
        "answer": answer,
        "results": results[:5],
        "suggestions": suggestions,
    }


@app.get("/api/stats/overview")
async def get_stats_overview():
    total = len(CANDIDATES)
    by_dept = {}
    for dept_id in DEPARTMENTS:
        candidates = [c for c in CANDIDATES if c["dept"] == dept_id]
        by_dept[dept_id] = {
            "total": len(candidates),
            "scores": [compute_score(c, dept_id) for c in candidates],
        }
    
    all_scores = []
    for c in CANDIDATES:
        all_scores.append(compute_score(c, c["dept"]))
    
    stages_count = {}
    for c in CANDIDATES:
        s = c["stage"]
        stages_count[s] = stages_count.get(s, 0) + 1
    
    return {
        "total_candidates": total,
        "avg_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "max_score": max(all_scores) if all_scores else 0,
        "min_score": min(all_scores) if all_scores else 0,
        "stages_distribution": stages_count,
        "offer_count": stages_count.get("offer", 0),
        "final_count": stages_count.get("终面", 0),
    }


@app.get("/api/stats/funnel")
async def get_funnel_data():
    stages_order = ["简历初筛", "初试", "复试", "终面", "offer"]
    funnel = []
    for stage in stages_order:
        count = sum(1 for c in CANDIDATES if c["stage"] == stage)
        funnel.append({"stage": stage, "count": count})
    return funnel


# ==================== 启动 ====================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"\n🚀 AI智能招聘管理系统已启动")
    print(f"🌐 访问地址: http://127.0.0.1:{port}")
    print(f"📚 API文档: http://127.0.0.1:{port}/api/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
async def index(request: Request):
    from pathlib import Path
    html_path = Path(__file__).parent / "templates" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
async def index(request: Request):
    from pathlib import Path
    html_path = Path(__file__).parent / "templates" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
