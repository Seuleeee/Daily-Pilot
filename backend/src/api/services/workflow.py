import json
import time
from collections.abc import Generator
from typing import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from config.settings import get_settings

settings = get_settings()


# -------------------- 1. 상태 정의 --------------------
class AgentState(TypedDict):
    task: str  # 초기 과제
    plan: str  # Planning 에이전트의 계획안
    research: str  # Research 에이전트의 조사 내용
    critique: str  # Critic 에이전트의 비평
    decision: str  # Judge 에이전트의 최종 결정 또는 다음 단계 지시
    history: list[BaseMessage]  # 전체 대화 기록
    round_count: int  # 현재 라운드 수
    max_rounds: int  # 최대 라운드 수


# -------------------- 2. 출력 함수 정의 --------------------
def emit_message(agent_name: str, message: str, message_type: str = "response"):
    """실시간 메시지 출력 (SSE 형태로 구조화)"""
    output = {"agent": agent_name, "type": message_type, "content": message, "timestamp": time.time()}
    print(f"[{agent_name}] {message}")
    print(f"SSE_DATA: {json.dumps(output, ensure_ascii=False)}")
    print("-" * 50)
    time.sleep(0.5)  # 대화 느낌을 위한 약간의 지연


# -------------------- 3. 에이전트 노드 정의 --------------------
# LLM 모델 설정
llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-3.5-turbo-1106", temperature=0.7)


def control_manager_node(state: AgentState):
    """Control Manager: 토론 시작 및 과제 제시"""
    emit_message("매니저", f"🎯 라운드 {state['round_count']}을 시작합니다!", "start")
    emit_message("매니저", f"오늘의 과제는 '{state['task']}'입니다.", "task")
    emit_message("매니저", "기획자님, 계획을 수립해주세요.", "request")

    state["history"].append(
        HumanMessage(content=f"라운드 {state['round_count']}: 과제 '{state['task']}'에 대한 논의를 시작합니다.")
    )
    return state


def planning_node(state: AgentState):
    """Planning: 초기 계획 수립"""
    emit_message("기획자", "네, 계획을 수립해보겠습니다.", "thinking")

    # 이전 라운드 정보가 있다면 참고
    previous_context = ""
    if state["round_count"] > 1:
        previous_context = f"""
        이전 라운드 정보:
        - 이전 계획: {state.get("plan", "N/A")}
        - 이전 비평: {state.get("critique", "N/A")}
        이전 피드백을 반영하여 계획을 수정해주세요.
        """

    prompt = f"""
    당신은 전문 기획자입니다. 다음 과제에 대해 간단하게 계획을 수립해주세요.
    과제: {state["task"]}
    현재 라운드: {state["round_count"]}
    {previous_context}
    
    계획은 다음을 포함해야 합니다:
    1. 목표 설정
    2. 주요 단계
    3. 예상 일정
    4. 필요 자원
    5. 예상 효과
    
    친근하고 대화하는 톤으로 작성해주세요.
    """

    response = llm.invoke(prompt)
    state["plan"] = response.content
    state["history"].append(HumanMessage(content=f"[기획자] {response.content}"))

    emit_message("기획자", response.content, "plan")
    emit_message("기획자", "리서처님, 이 계획에 대해 조사해주실 수 있나요?", "request")

    return state


def research_node(state: AgentState):
    """Research: 계획에 대한 정보 조사"""
    emit_message("리서처", "기획자님의 계획을 검토해보겠습니다.", "thinking")

    prompt = f"""
    당신은 전문 리서처입니다. 기획자가 제시한 계획에 대해 간단하게 다각도로 조사해주세요.
    
    계획안: {state["plan"]}
    현재 라운드: {state["round_count"]}
    
    다음 관점에서 조사해주세요:
    1. 비용(시간, 노력) 분석
    2. 리스크 분석
    3. 성공 사례
    
    조사 결과를 대화하듯이 친근하게 설명해주세요.
    """

    response = llm.invoke(prompt)
    state["research"] = response.content
    state["history"].append(HumanMessage(content=f"[리서처] {response.content}"))

    emit_message("리서처", response.content, "research")
    emit_message("리서처", "비평가님, 이 계획과 조사 결과에 대해 어떻게 생각하시나요?", "request")

    return state


def critic_node(state: AgentState):
    """Critic: 계획과 조사를 바탕으로 비판적 검토"""
    emit_message("비평가", "계획과 조사 내용을 꼼꼼히 살펴보겠습니다.", "thinking")

    prompt = f"""
    당신은 예리한 비평가입니다. 기획자의 계획과 리서처의 조사 결과를 종합적으로 간단하게 검토해주세요.
    
    계획안: {state["plan"]}
    조사 내용: {state["research"]}
    현재 라운드: {state["round_count"]}
    
    다음 관점에서 비판적으로 검토해주세요:
    1. 계획의 현실성
    2. 논리적 일관성
    3. 누락된 중요 요소
    4. 과도한 낙관론
    5. 구체적인 개선 제안
    
    건설적인 비판을 대화하듯이 친근하게 제시해주세요.
    """

    response = llm.invoke(prompt)
    state["critique"] = response.content
    state["history"].append(HumanMessage(content=f"[비평가] {response.content}"))

    emit_message("비평가", response.content, "critique")
    emit_message("비평가", "판사님, 최종 결정을 내려주세요.", "request")

    return state


def judge_node(state: AgentState):
    """Judge: 모든 내용을 종합하여 다음 단계를 결정"""
    emit_message("판사", "모든 의견을 종합하여 판단해보겠습니다.", "thinking")

    # 최대 라운드 체크
    is_final_round = state["round_count"] >= state["max_rounds"]

    prompt = f"""
    당신은 최종 의사결정권자인 판사입니다. 모든 토론 내용을 종합하여 결정해주세요.
    
    계획안: {state["plan"]}
    조사 내용: {state["research"]}
    비평: {state["critique"]}
    현재 라운드: {state["round_count"]}
    최대 라운드: {state["max_rounds"]}
    최종 라운드 여부: {is_final_round}
    
    {
        "최종 라운드이므로 반드시 FINALIZE를 선택해야 합니다."
        if is_final_round
        else "다음 세 가지 옵션 중 하나로 결정해주세요:"
    }
    
    - 계획에 근본적인 수정이 필요하면 'REVISE_PLAN'
    - 정보가 더 필요하면 'MORE_RESEARCH'  
    - 계획이 타당하고 실행 가능하면 'FINALIZE'
    
    결정 이유를 자세히 설명하고, 마지막 줄에 "DECISION: [선택]" 형식으로 명시해주세요.
    대화하듯이 친근하게 설명해주세요.
    """

    response = llm.invoke(prompt)
    decision_text = response.content
    state["history"].append(HumanMessage(content=f"[판사] {decision_text}"))

    emit_message("판사", decision_text, "decision")

    # 결정 파싱
    if is_final_round or "DECISION: FINALIZE" in decision_text:
        state["decision"] = "finalize"
        emit_message("판사", "🎉 최종 결정: 프로젝트 승인!", "final")
    elif "DECISION: REVISE_PLAN" in decision_text:
        state["decision"] = "revise_plan"
        state["round_count"] += 1
        emit_message("판사", f"🔄 라운드 {state['round_count']}에서 계획을 수정하겠습니다.", "continue")
    elif "DECISION: MORE_RESEARCH" in decision_text:
        state["decision"] = "more_research"
        state["round_count"] += 1
        emit_message("판사", f"🔍 라운드 {state['round_count']}에서 추가 조사하겠습니다.", "continue")
    else:
        state["decision"] = "finalize"
        emit_message("판사", "🎉 최종 결정: 프로젝트 승인!", "final")

    return state


# -------------------- 4. 조건부 엣지(라우터) 정의 --------------------
def router(state: AgentState):
    """라우터: 판사의 결정에 따라 다음 단계 결정"""
    decision = state.get("decision", "finalize")

    if decision == "revise_plan":
        return "planning"
    elif decision == "more_research":
        return "research"
    else:
        return END


# -------------------- 5. 그래프 구성 및 실행 --------------------
def create_discussion_workflow():
    """토론 워크플로우 생성"""
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

    # 조건부 엣지 연결
    workflow.add_conditional_edges("judge", router, {"planning": "planning", "research": "researcher", END: END})

    return workflow.compile()


def run_discussion(task: str, max_rounds: int = 2) -> Generator[dict, None, None]:
    """토론 실행 및 실시간 결과 반환"""
    app = create_discussion_workflow()

    initial_state = {
        "task": task,
        "history": [],
        "round_count": 1,
        "max_rounds": max_rounds,
        "plan": "",
        "research": "",
        "critique": "",
        "decision": "",
    }

    print("=" * 60)
    print("🤖 AI 에이전트 토론 시스템 시작")
    print("=" * 60)

    # 스트림으로 실행하며 각 단계 결과 반환
    yield from app.stream(initial_state, stream_mode="values")

    print("=" * 60)
    print("✅ 토론 완료")
    print("=" * 60)
