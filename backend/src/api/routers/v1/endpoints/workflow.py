import asyncio
import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# 기존 워크플로우 서비스 임포트
from api.services.workflow import run_discussion

router = APIRouter(prefix="/workflows", tags=["Workflows"])


# -------------------- 1. 요청/응답 모델 정의 --------------------
class WorkflowRequest(BaseModel):
    task: str = Field(..., description="토론할 과제", min_length=1, max_length=500)
    max_rounds: int = Field(2, description="최대 라운드 수", ge=1, le=5)


class WorkflowResponse(BaseModel):
    workflow_id: str
    task: str
    status: str
    created_at: datetime


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    current_round: int
    max_rounds: int
    last_updated: datetime


# -------------------- 2. 워크플로우 상태 관리 --------------------
# 실행 중인 워크플로우 상태를 추적하는 딕셔너리
active_workflows: dict[str, dict[str, Any]] = {}


# -------------------- 3. SSE 이벤트 포맷터 --------------------
def format_sse_event(event_type: str, data: dict[str, Any]) -> str:
    """SSE 이벤트 포맷팅"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def format_agent_message(agent: str, message_type: str, content: str, workflow_id: str) -> str:
    """에이전트 메시지를 SSE 형태로 포맷팅"""
    event_data = {
        "workflow_id": workflow_id,
        "agent": agent,
        "type": message_type,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }
    return format_sse_event("agent_message", event_data)


def format_status_update(workflow_id: str, status: str, current_round: int, max_rounds: int) -> str:
    """상태 업데이트를 SSE 형태로 포맷팅"""
    event_data = {
        "workflow_id": workflow_id,
        "status": status,
        "current_round": current_round,
        "max_rounds": max_rounds,
        "timestamp": datetime.now().isoformat(),
    }
    return format_sse_event("status_update", event_data)


# -------------------- 4. 워크플로우 실행 래퍼 --------------------
async def run_workflow_with_sse(workflow_id: str, task: str, max_rounds: int):
    """워크플로우를 실행하고 SSE 이벤트 생성"""
    try:
        # 워크플로우 상태 초기화
        active_workflows[workflow_id] = {
            "status": "running",
            "current_round": 1,
            "max_rounds": max_rounds,
            "task": task,
            "started_at": datetime.now(),
            "last_updated": datetime.now(),
        }

        # 시작 이벤트 전송
        yield format_status_update(workflow_id, "started", 1, max_rounds)
        yield format_agent_message("시스템", "info", f"워크플로우 '{workflow_id}' 시작", workflow_id)

        # 워크플로우 실행
        previous_round = 1
        for step_result in run_discussion(task, max_rounds):
            # 라운드 변경 감지
            current_round = step_result.get("round_count", 1)
            if current_round > previous_round:
                yield format_status_update(workflow_id, "round_changed", current_round, max_rounds)
                previous_round = current_round

            # 상태 업데이트
            active_workflows[workflow_id].update({"current_round": current_round, "last_updated": datetime.now()})

            # 각 에이전트별 메시지 추출 및 전송
            if step_result.get("plan"):
                yield format_agent_message("기획자", "plan", step_result["plan"], workflow_id)

            if step_result.get("research"):
                yield format_agent_message("리서처", "research", step_result["research"], workflow_id)

            if step_result.get("critique"):
                yield format_agent_message("비평가", "critique", step_result["critique"], workflow_id)

            if step_result.get("decision"):
                decision = step_result["decision"]
                if decision == "finalize":
                    yield format_agent_message("판사", "final_decision", "프로젝트 최종 승인!", workflow_id)
                elif decision == "revise_plan":
                    yield format_agent_message("판사", "decision", "계획을 수정하겠습니다.", workflow_id)
                elif decision == "more_research":
                    yield format_agent_message("판사", "decision", "추가 조사가 필요합니다.", workflow_id)

            # 약간의 딜레이로 자연스러운 흐름 연출
            await asyncio.sleep(0.1)

        # 완료 상태 업데이트
        active_workflows[workflow_id]["status"] = "completed"
        active_workflows[workflow_id]["completed_at"] = datetime.now()

        yield format_status_update(workflow_id, "completed", current_round, max_rounds)
        yield format_agent_message("시스템", "info", "워크플로우 완료", workflow_id)

    except Exception as e:
        # 에러 처리
        error_message = f"워크플로우 실행 중 오류 발생: {str(e)}"

        if workflow_id in active_workflows:
            active_workflows[workflow_id]["status"] = "failed"
            active_workflows[workflow_id]["error"] = str(e)
            active_workflows[workflow_id]["last_updated"] = datetime.now()

        yield format_status_update(workflow_id, "failed", 0, max_rounds)
        yield format_agent_message("시스템", "error", error_message, workflow_id)

    finally:
        # 30분 후 자동 정리를 위한 타이머 설정 (실제 구현에서는 백그라운드 태스크 사용)
        asyncio.create_task(cleanup_workflow(workflow_id, delay=1800))


async def cleanup_workflow(workflow_id: str, delay: int = 1800):
    """워크플로우 정리 (30분 후 자동 삭제)"""
    await asyncio.sleep(delay)
    if workflow_id in active_workflows:
        del active_workflows[workflow_id]


# -------------------- 5. API 엔드포인트 정의 --------------------


@router.post("/start", response_model=WorkflowResponse)
async def start_workflow(request: WorkflowRequest):
    """새로운 워크플로우 시작"""
    try:
        workflow_id = str(uuid4())

        # 워크플로우 정보 저장
        workflow_info = {
            "workflow_id": workflow_id,
            "task": request.task,
            "max_rounds": request.max_rounds,
            "status": "pending",
            "created_at": datetime.now(),
        }

        return WorkflowResponse(**workflow_info)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"워크플로우 시작 실패: {str(e)}")


@router.post("/execute")
async def execute_workflow(request: WorkflowRequest):
    """워크플로우 실행 및 SSE 스트리밍 (직접 실행)"""
    try:
        workflow_id = str(uuid4())

        # SSE 스트리밍 응답 생성
        return StreamingResponse(
            run_workflow_with_sse(workflow_id, request.task, request.max_rounds),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"워크플로우 실행 실패: {str(e)}")


@router.get("/stream/{workflow_id}")
async def stream_workflow(workflow_id: str):
    """기존 워크플로우 스트리밍 (저장된 워크플로우용)"""
    try:
        # 워크플로우 ID 유효성 검사
        if workflow_id not in active_workflows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="워크플로우를 찾을 수 없습니다")

        workflow_info = active_workflows[workflow_id]

        # 이미 실행 중인지 확인
        if workflow_info["status"] == "running":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="워크플로우가 이미 실행 중입니다")

        # SSE 스트리밍 응답 생성
        return StreamingResponse(
            run_workflow_with_sse(workflow_id, workflow_info["task"], workflow_info["max_rounds"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"워크플로우 스트리밍 실패: {str(e)}"
        )


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """워크플로우 상태 조회"""
    try:
        if workflow_id not in active_workflows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="워크플로우를 찾을 수 없습니다")

        workflow_info = active_workflows[workflow_id]

        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=workflow_info["status"],
            current_round=workflow_info["current_round"],
            max_rounds=workflow_info["max_rounds"],
            last_updated=workflow_info["last_updated"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"상태 조회 실패: {str(e)}")


@router.delete("/stop/{workflow_id}")
async def stop_workflow(workflow_id: str):
    """워크플로우 중단"""
    try:
        if workflow_id not in active_workflows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="워크플로우를 찾을 수 없습니다")

        # 워크플로우 중단 처리
        active_workflows[workflow_id]["status"] = "stopped"
        active_workflows[workflow_id]["stopped_at"] = datetime.now()

        return {"message": f"워크플로우 '{workflow_id}' 중단됨"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"워크플로우 중단 실패: {str(e)}")


@router.get("/list")
async def list_workflows():
    """활성 워크플로우 목록 조회"""
    try:
        workflows = []
        for workflow_id, info in active_workflows.items():
            workflows.append(
                {
                    "workflow_id": workflow_id,
                    "task": info.get("task", ""),
                    "status": info["status"],
                    "current_round": info["current_round"],
                    "max_rounds": info["max_rounds"],
                    "started_at": info.get("started_at"),
                    "last_updated": info["last_updated"],
                }
            )

        return {"workflows": workflows, "total": len(workflows)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"워크플로우 목록 조회 실패: {str(e)}"
        )
