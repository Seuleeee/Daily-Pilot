import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

# .env 파일에서 API 키 로드
load_dotenv()


# -------------------- 1. 상태 정의 --------------------
# 모든 에이전트가 공유하고 수정할 상태를 정의합니다.
class AgentState(TypedDict):
    task: str  # 초기 과제
    plan: str  # Planning 에이전트의 계획안
    research: str  # Research 에이전트의 조사 내용
    critique: str  # Critic 에이전트의 비평
    decision: str  # Judge 에이전트의 최종 결정 또는 다음 단계 지시
    history: list[BaseMessage]  # 전체 대화 기록


# -------------------- 2. 에이전트 노드 정의 --------------------
# 각 에이전트는 하나의 노드(함수)로 정의됩니다.

# LLM 모델 설정
llm = ChatOpenAI(os.getenv("OPENAI_API_KEY"), model="gpt-3.5-turbo-1106", temperature=0.7)


def control_manager_node(state: AgentState):
    """Control Manager: 토론 시작 및 과제 제시"""
    print("---MANAGER---")
    state["history"].append(
        HumanMessage(content=f"과제: {state['task']}에 대한 논의를 시작하겠습니다. 먼저 계획을 수립해주세요.")
    )
    return state


def planning_node(state: AgentState):
    """Planning: 초기 계획 수립"""
    print("---PLANNER---")
    prompt = f"""
    당신은 전문 기획자입니다. 다음 과제와 대화 기록을 바탕으로 구체적인 실행 계획을 수립해주세요.
    과제: {state["task"]}
    대화 기록: {state["history"]}
    
    실행 계획:
    """
    response = llm.invoke(prompt)
    state["plan"] = response.content
    state["history"].append(HumanMessage(content=f"계획안: {response.content}"))
    return state


def research_node(state: AgentState):
    """Research: 계획에 대한 정보 조사 (LLM으로 시뮬레이션)"""
    print("---RESEARCHER---")
    prompt = f"""
    당신은 전문 리서처입니다. 다음 계획안에 대해 관련 데이터, 시장 상황, 예상되는 문제점 등을 조사해주세요.
    계획안: {state["plan"]}
    대화 기록: {state["history"]}
    
    조사 내용:
    """
    response = llm.invoke(prompt)
    state["research"] = response.content
    state["history"].append(HumanMessage(content=f"조사 내용: {response.content}"))
    return state


def critic_node(state: AgentState):
    """Critic: 계획과 조사를 바탕으로 비판적 검토"""
    print("---CRITIC---")
    prompt = f"""
    당신은 비평가입니다. 제시된 계획안과 리서치 결과를 바탕으로
    잠재적인 위험, 논리적 오류, 개선점 등을 날카롭게 지적해주세요.
    계획안: {state["plan"]}
    조사 내용: {state["research"]}
    대화 기록: {state["history"]}
    
    비평 내용:
    """
    response = llm.invoke(prompt)
    state["critique"] = response.content
    state["history"].append(HumanMessage(content=f"비평: {response.content}"))
    return state


def judge_node(state: AgentState):
    """Judge: 모든 내용을 종합하여 다음 단계를 결정"""
    print("---JUDGE---")
    prompt = f"""
    당신은 최종 의사결정권자인 판사입니다. 계획, 조사, 비평을 모두 검토하고 다음 행동을 결정해주세요.
    반드시 다음 세 가지 옵션 중 하나로 결정을 내려야 합니다: [REVISE_PLAN, MORE_RESEARCH, FINALIZE]

    - 계획에 근본적인 수정이 필요하면 'REVISE_PLAN'
    - 정보가 더 필요하면 'MORE_RESEARCH'
    - 계획이 타당하고 실행 가능하면 'FINALIZE'

    결정 이유를 간략히 설명하고, 마지막 줄에 "DECISION: [선택]" 형식으로 명시해주세요.
    
    계획안: {state["plan"]}
    조사 내용: {state["research"]}
    비평: {state["critique"]}
    """
    response = llm.invoke(prompt)
    decision_text = response.content
    state["history"].append(HumanMessage(content=f"판단: {decision_text}"))

    if "DECISION: REVISE_PLAN" in decision_text:
        state["decision"] = "revise_plan"
    elif "DECISION: MORE_RESEARCH" in decision_text:
        state["decision"] = "more_research"
    else:
        state["decision"] = "finalize"

    return state


# -------------------- 3. 조건부 엣지(라우터) 정의 --------------------
# Judge의 결정에 따라 워크플로우를 분기합니다.
def router(state: AgentState):
    print("---ROUTING---")
    decision = state.get("decision", "finalize")
    if decision == "revise_plan":
        return "planning"
    elif decision == "more_research":
        return "research"
    else:
        return END


# -------------------- 4. 그래프 구성 및 실행 --------------------

# 그래프 생성
workflow = StateGraph(AgentState)

# 노드 추가
workflow.add_node("control_manager", control_manager_node)
workflow.add_node("planning", planning_node)
workflow.add_node("researcher", research_node)
workflow.add_node("critic", critic_node)
workflow.add_node("judge", judge_node)

# 엣지 연결
workflow.set_entry_point("control_manager")
workflow.add_edge("control_manager", "planning")
workflow.add_edge("planning", "researcher")
workflow.add_edge("researcher", "critic")
workflow.add_edge("critic", "judge")

# 조건부 엣지 연결 (가장 중요한 부분)
workflow.add_conditional_edges("judge", router, {"planning": "planning", "research": "researcher", END: END})

# 그래프 컴파일
app = workflow.compile()

# 그래프 실행
initial_state = {"task": "사내 카페에 AI 바리스타 로봇을 도입하는 프로젝트", "history": []}

# stream을 사용하여 각 단계의 결과를 실시간으로 확인
# 💡 수정한 코드
for s in app.stream(initial_state, stream_mode="values"):
    print("---CURRENT STATE---")
    print(f"Task: {s.get('task', 'N/A')}")
    # .get()을 사용하여 키가 존재할 때만 값을 출력
    if s.get("plan"):
        print(f"Plan: {s['plan']}...")
    if s.get("research"):
        print(f"Research: {s['research']}...")
    if s.get("critique"):
        print(f"Critique: {s['critique']}...")
    if s.get("decision"):
        print(f"Decision: {s['decision']}")
    print("\n" + "=" * 30 + "\n")
