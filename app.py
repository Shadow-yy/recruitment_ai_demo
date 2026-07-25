# -*- coding: utf-8 -*-
import json, os, re, copy, uvicorn
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="AI智能招聘管理系统", docs_url="/api/docs")

DEPARTMENTS = {"tech": {"name": "技术研发部", "icon": "laptop"}, "product": {"name": "产品运营部", "icon": "pie-chart"}, "market": {"name": "市场销售部", "icon": "trending-up"}}
WT = {"tech": {"tech_ability": {"label": "技术能力", "value": 50}, "project_exp": {"label": "项目经验", "value": 30}, "education": {"label": "学历背景", "value": 10}, "soft_skill": {"label": "软技能", "value": 10}}, "product": {"related_exp": {"label": "相关经验", "value": 40}, "soft_skill": {"label": "软技能", "value": 30}, "project_result": {"label": "项目成果", "value": 20}, "education": {"label": "学历", "value": 10}}, "market": {"industry_exp": {"label": "行业经验", "value": 40}, "performance": {"label": "业绩成果", "value": 35}, "soft_skill": {"label": "软技能", "value": 20}, "education": {"label": "学历", "value": 5}}}
_current_weights = copy.deepcopy(WT)

CD = json.loads(open(Path(__file__).parent/"data.json","r",encoding="utf-8").read())
CANDIDATES = CD

def sc(c, d, wo=None):
    w = wo if wo else _current_weights.get(d, WT[d])
    sv = c.get("interview_scores", {}); tw = sum(v["value"] for v in w.values())
    if tw == 0: return 0
    return round(sum(sv.get(k,0)*(v["value"]/tw) for k,v in w.items()), 1)

def gs(c, d):
    s=sc(c,d); g="男" if c["gender"]=="男" else "女"
    b=f"{c['name']}，{g}，{c['age']}岁，{c['work_years']}年{c['target_position']}经验，毕业于{c['school']}（{c['education']}），目标岗位{c['target_position']}，投递{DEPARTMENTS[d]['name']}，整体匹配度{s}分，当前阶段：{c['stage']}。"
    sk="、".join(c["skills"][:4]); ex="；".join([f"{e['company']}担任{e['position']}（{e['duration']}）：{e['summary']}" for e in c.get("work_exp",[])])
    ab=f"核心优势：具备{sk}等核心技能。核心经历：{ex}。"
    l=c["interview_notes"][-1] if c["interview_notes"] else None
    if l:
        sd="；".join([f"{v['label']}{c['interview_scores'].get(k,0)}分" for k,v in WT[d].items()])
        ex2=f"面试官评价：{l['comment']}（{l['round']}-{l['interviewer']}）。各维度评分：{sd}。当前结论：{l['verdict']}。"
    else: ex2="暂无面试评价记录。"
    return {"basic":b,"ability":ab,"extra":ex2}

def acs(q, df=None):
    r=[]
    for c in CANDIDATES:
        if df and c["dept"]!=df: continue
        s=sc(c,c["dept"])
        if q in c["name"] or c["target_position"] in q or any(k in q for k in c["skills"]):
            r.append({"id":c["id"],"name":c["name"],"position":c["target_position"],"dept":DEPARTMENTS[c["dept"]]["name"],"score":s,"stage":c["stage"],"skills":c["skills"][:3],"work_years":c["work_years"],"education":c["education"]})
    r.sort(key=lambda x:-x["score"]); return r[:10]

@app.get("/", response_class=HTMLResponse)
async def index(rq:Request):
    return HTMLResponse((Path(__file__).parent/"templates"/"index.html").read_text("utf-8"))

@app.get("/api/departments/overview")
async def dept_overview():
    o={}
    for did,di in DEPARTMENTS.items():
        cs=[c for c in CANDIDATES if c["dept"]==did]; st={}
        for c in cs: s=c["stage"]; st[s]=st.get(s,0)+1
        sv=[sc(c,did) for c in cs]
        o[did]={"name":di["name"],"icon":di["icon"],"total":len(cs),"stages":st,"avg_score":round(sum(sv)/len(sv),1) if sv else 0,"top_candidate":max(cs,key=lambda c:sc(c,did))["name"] if cs else "","passed_count":sum(1 for c in cs if c["stage"] in ["终面","offer"])}
    return o

@app.get("/api/candidates")
async def list_candidates(dept:Optional[str]=Query(None),stage:Optional[str]=Query(None),sort_by:Optional[str]=Query("score_desc"),keyword:Optional[str]=Query(""),min_score:Optional[float]=Query(0)):
    r=[]
    for c in CANDIDATES:
        if dept and c["dept"]!=dept: continue
        if stage and c["stage"]!=stage: continue
        if keyword and keyword not in c["name"] and keyword not in c["target_position"] and keyword not in " ".join(c["skills"]): continue
        s=sc(c,c["dept"])
        if s<min_score: continue
        r.append({"id":c["id"],"name":c["name"],"gender":c["gender"],"age":c["age"],"education":c["education"],"school":c["school"],"work_years":c["work_years"],"target_position":c["target_position"],"dept":c["dept"],"dept_name":DEPARTMENTS[c["dept"]]["name"],"stage":c["stage"],"score":s,"skills":c["skills"][:4],"city":c["city"]})
    sk={"score_desc":lambda x:-x["score"],"score_asc":lambda x:x["score"],"name":lambda x:x["name"],"work_years_desc":lambda x:-x["work_years"]}
    r.sort(key=sk.get(sort_by,sk["score_desc"])); return r

@app.get("/api/candidates/{cid}")
async def get_detail(cid:int):
    for c in CANDIDATES:
        if c["id"]==cid:
            s=sc(c,c["dept"]); u=gs(c,c["dept"]); d={k:v for k,v in c.items()}
            d["score"]=s; d["summary"]=u; d["dept_name"]=DEPARTMENTS[c["dept"]]["name"]
            d["score_detail"]={WT[c["dept"]][k]["label"]:{"score":v,"weight":WT[c["dept"]][k]["value"]} for k,v in c["interview_scores"].items()}
            return d
    return JSONResponse({"error":"不存在"}, status_code=404)

@app.get("/api/weights/{dept}")
async def get_weights(dept:str):
    if dept not in _current_weights: return JSONResponse({"error":"不存在"}, status_code=404)
    return _current_weights[dept]

class WU(BaseModel): weights: dict
@app.post("/api/weights/{dept}")
async def update_weights(dept:str,data:WU):
    if dept not in _current_weights: return JSONResponse({"error":"不存在"}, status_code=404)
    for k,v in data.weights.items():
        if k in _current_weights[dept]: _current_weights[dept][k]["value"]=max(0,min(100,v.get("value",_current_weights[dept][k]["value"])))
    return _current_weights[dept]

class RT(BaseModel): text: str
@app.post("/api/resume/extract")
async def extract_resume(data:RT):
    t=data.text; r={"基础信息":{},"技能标签":[],"职业经历":[]}
    nm=re.search(r'姓名[：:]\s*(\S+)',t) or re.search(r'^(\S{2,4})[，,\s]',t)
    if nm: r["基础信息"]["姓名"]=nm.group(1).strip()
    em=re.search(r'(本科|硕士|博士|大专)',t)
    if em: r["基础信息"]["学历"]=em.group(1)
    sm=re.search(r'(大学|学院)',t)
    if sm: r["基础信息"]["毕业院校"]=t[max(0,sm.start()-8):sm.end()].strip()
    pm=re.search(r'1[3-9]\d{9}',t)
    if pm: r["基础信息"]["联系方式"]=pm.group(0)
    for sk in ["Java","Python","Vue.js","React","Spring","MySQL","Docker","K8s","数据分析","项目管理","Axure","CRM"]:
        if sk in t: r["技能标签"].append(sk)
    for co in re.findall(r'([\u4e00-\u9fa5]{2,6}(?:公司|集团|科技|有限))',t):
        r["职业经历"].append({"公司":co,"职位":"待识别","时间":"待识别"})
    return r

class IT(BaseModel): text: str; candidate_id:Optional[int]=None
@app.post("/api/interview/extract")
async def extract_interview(data:IT):
    t=data.text; vd="待定"
    for v in ["通过","复试","待定","不通过"]:
        if v in t: vd=v; break
    r={"原始面评":t,"提取维度":{"技术能力":"待评估","沟通表达":"待评估","逻辑思维":"待评估","团队协作":"待评估","岗位匹配度":"待评估"},"面试官核心观点":[],"建议结论":vd}
    rm={"扎实":"优秀","良好":"良好","一般":"一般","较强":"良好","突出":"优秀"}
    for dm in ["技术能力","沟通表达","逻辑思维","团队协作","岗位匹配度"]:
        for kw,ra in rm.items():
            if kw in t: r["提取维度"][dm]=ra; break
    for s in re.split(r'[。，；]',t):
        s=s.strip()
        if len(s)>4 and any(kw in s for kw in ["经验丰富","能力强","突出","优秀","扎实","待考察"]):
            r["面试官核心观点"].append(s)
    if not r["面试官核心观点"]: r["面试官核心观点"]=[t[:30]+"..."]
    return r

class CM(BaseModel): message: str; dept: Optional[str]=None
@app.post("/api/chat")
async def chat_agent(data:CM):
    rs=acs(data.message,data.dept)
    if not rs: rs=acs(data.message.replace("的","").replace("有","").replace("年",""))
    if not rs: ans="抱歉，没有找到匹配的候选人信息。"
    elif len(rs)==1: r=rs[0]; ans=f"为您找到1位匹配候选人：{r['name']}，{r['position']}，{r['dept']}，匹配度{r['score']}分，当前阶段：{r['stage']}。"
    else:
        ans=f"为您找到{len(rs)}位匹配候选人，按匹配度排序如下：\n"+"\n".join([f"\n{i+1}. {r['name']}-{r['position']}({r['dept']})-{r['score']}分-{r['stage']}" for i,r in enumerate(rs[:5])])
        if len(rs)>5: ans+=f"\n...及其他{len(rs)-5}位候选人"
    su=[f"看看{rs[0]['dept']}更多候选人" if rs else "找技术部候选人","本月招聘数据统计","帮我对比得分最高的两位"]
    return {"answer":ans,"results":rs[:5],"suggestions":su}

@app.get("/api/stats/overview")
async def stats_overview():
    ac=[sc(c,c["dept"]) for c in CANDIDATES]
    scd={}; [scd.update({c["stage"]:scd.get(c["stage"],0)+1}) for c in CANDIDATES]
    return {"total_candidates":len(CANDIDATES),"avg_score":round(sum(ac)/len(ac),1) if ac else 0,"max_score":max(ac) if ac else 0,"min_score":min(ac) if ac else 0,"stages_distribution":scd,"offer_count":scd.get("offer",0),"final_count":scd.get("终面",0)}

@app.get("/api/stats/funnel")
async def funnel():
    return [{"stage":s,"count":sum(1 for c in CANDIDATES if c["stage"]==s)} for s in ["简历初筛","初试","复试","终面","offer"]]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\nAI招聘系统启动: http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
