"""
Blackbox 5 REST API

FastAPI-based REST interface for Blackbox 5 with integrated safety features.

Usage:
    python -m interface.api.main
    curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "What is 2+2?"}'
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uvicorn
import sys
from pathlib import Path

# Import main Blackbox 5 system
# Find the infrastructure directory by going up from interface/api
api_dir = Path(__file__).parent
interface_dir = api_dir.parent  # Go up to interface/
core_dir = interface_dir.parent  # Go up to 01-core/
infrastructure_path = core_dir / "infrastructure"

# Add paths to sys.path
sys.path.insert(0, str(core_dir))
sys.path.insert(0, str(infrastructure_path))

# Import with explicit module path to avoid circular import
import importlib.util
spec = importlib.util.spec_from_file_location("blackbox5_main", str(infrastructure_path / "main.py"))
blackbox5_main = importlib.util.module_from_spec(spec)
sys.modules['blackbox5_main'] = blackbox5_main
spec.loader.exec_module(blackbox5_main)

get_blackbox5 = blackbox5_main.get_blackbox5

# ============================================================================
# Pydantic Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message to process", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for continuity")
    agent: Optional[str] = Field(None, description="Force specific agent")
    strategy: Optional[str] = Field('auto', description="Execution strategy")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    success: bool
    session_id: str
    timestamp: str
    routing: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    guide_suggestions: Optional[List[Dict[str, Any]]] = None


class AgentInfo(BaseModel):
    """Agent information model."""
    name: str
    role: str
    category: str
    description: str
    capabilities: List[str]


class SafetyStatus(BaseModel):
    """Safety system status model."""
    kill_switch: Dict[str, Any]
    safe_mode: Dict[str, Any]
    overall_status: str


class SafeModeRequest(BaseModel):
    """Request model for safe mode operations."""
    level: str = Field(..., description="Safe mode level (limited, restricted, emergency)")
    reason: str = Field(..., description="Reason for entering safe mode", min_length=1)
    source: str = Field("api", description="Source of the request")


class RecoverRequest(BaseModel):
    """Request model for kill switch recovery."""
    message: Optional[str] = Field(None, description="Recovery message")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Blackbox 5 API",
    description="Multi-Agent Orchestration System with Safety Features",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Middleware
# ============================================================================

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ============================================================================
# Startup
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize Blackbox 5 on startup"""
    await get_blackbox5()


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns system health status including safety systems.
    """
    try:
        from safety.kill_switch import get_kill_switch
        from safety.safe_mode import get_safe_mode

        ks = get_kill_switch()
        sm = get_safe_mode()

        return {
            "status": "healthy" if ks.is_operational() else "unhealthy",
            "version": "5.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "safety": {
                "kill_switch_operational": ks.is_operational(),
                "safe_mode_active": sm.is_safe_mode(),
                "safe_mode_level": sm.current_level.value if sm.is_safe_mode() else None
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# ============================================================================
# Safety Endpoints
# ============================================================================

@app.get("/safety/status", response_model=SafetyStatus, tags=["Safety"])
async def get_safety_status():
    """
    Get comprehensive safety system status.

    Returns kill switch, safe mode, and classifier status.
    """
    try:
        from safety.kill_switch import get_kill_switch
        from safety.safe_mode import get_safe_mode

        ks = get_kill_switch()
        sm = get_safe_mode()

        return SafetyStatus(
            kill_switch={
                "operational": ks.is_operational(),
                "triggered": ks.triggered,
                "trigger_reason": ks.trigger_reason.value if ks.trigger_reason else None,
                "trigger_message": ks.trigger_message,
                "triggered_at": ks.triggered_at.isoformat() if ks.triggered_at else None,
                "recovered_at": ks.recovered_at.isoformat() if ks.recovered_at else None,
            },
            safe_mode={
                "enabled": sm.is_safe_mode(),
                "level": sm.current_level.value if sm.is_safe_mode() else None,
                "enter_reason": sm.enter_reason,
                "enter_source": sm.enter_source,
                "entered_at": sm.entered_at.isoformat() if sm.entered_at else None,
                "limits": sm.get_limits() if sm.is_safe_mode() else None,
            },
            overall_status="operational" if ks.is_operational() else "emergency_shutdown"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get safety status: {str(e)}")


@app.post("/safety/recover", tags=["Safety"])
async def recover_kill_switch(request: RecoverRequest):
    """
    Recover from kill switch and resume operations.

    Requires a recovery message for audit purposes.
    """
    try:
        from safety.kill_switch import get_kill_switch

        ks = get_kill_switch()

        if ks.is_operational():
            return {
                "success": True,
                "message": "System is operational. No recovery needed.",
                "recovered_at": ks.recovered_at.isoformat() if ks.recovered_at else None
            }

        # Attempt recovery
        recovery_msg = request.message or "Recovery via API"
        success = ks.recover(recovery_msg)

        if success:
            return {
                "success": True,
                "message": "System recovered successfully",
                "recovered_at": ks.recovered_at.isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Recovery failed",
                    "reason": ks.trigger_reason.value if ks.trigger_reason else "Unknown",
                    "message": ks.trigger_message
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recovery failed: {str(e)}")


@app.post("/safety/safe-mode/enter", tags=["Safety"])
async def enter_safe_mode(request: SafeModeRequest):
    """
    Enter safe mode at the specified level.

    Valid levels: limited, restricted, emergency
    """
    try:
        from safety.safe_mode import get_safe_mode, SafeModeLevel

        sm = get_safe_mode()

        # Map level string to enum
        level_map = {
            'limited': SafeModeLevel.LIMITED,
            'restricted': SafeModeLevel.RESTRICTED,
            'emergency': SafeModeLevel.EMERGENCY
        }

        if request.level not in level_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid safe mode level: {request.level}. Must be one of: limited, restricted, emergency"
            )

        safe_level = level_map[request.level]

        # Enter safe mode
        success = sm.enter_level(safe_level, request.reason, request.source)

        if success:
            return {
                "success": True,
                "message": f"Entered {request.level.upper()} safe mode",
                "level": request.level,
                "reason": request.reason,
                "source": request.source,
                "entered_at": sm.entered_at.isoformat(),
                "limits": sm.get_limits()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Failed to enter safe mode",
                    "current_level": sm.current_level.value
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enter safe mode: {str(e)}")


@app.post("/safety/safe-mode/exit", tags=["Safety"])
async def exit_safe_mode(reason: Optional[str] = None):
    """
    Exit safe mode and return to normal operation.

    Optionally provide a reason for audit purposes.
    """
    try:
        from safety.safe_mode import get_safe_mode

        sm = get_safe_mode()

        if not sm.is_safe_mode():
            return {
                "success": True,
                "message": "System is already in normal mode"
            }

        # Exit safe mode
        exit_msg = reason or "Exit via API"
        success = sm.exit_level(exit_msg)

        if success:
            return {
                "success": True,
                "message": "Exited safe mode",
                "reason": exit_msg
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Failed to exit safe mode",
                    "current_level": sm.current_level.value
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to exit safe mode: {str(e)}")


# ============================================================================
# Chat Endpoint
# ============================================================================

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Process a chat message with safety checks.

    This endpoint:
    1. Checks kill switch status
    2. Checks safe mode permissions
    3. Validates input with constitutional classifier
    4. Processes the request
    5. Validates output with constitutional classifier
    """
    try:
        # Import safety checks
        from safety.kill_switch import get_kill_switch
        from safety.safe_mode import get_safe_mode
        from safety.constitutional_classifier import get_classifier, ContentType

        # 1. Check kill switch
        ks = get_kill_switch()
        if not ks.is_operational():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Kill switch has been triggered",
                    "reason": ks.trigger_reason.value if ks.trigger_reason else "Unknown",
                    "message": ks.trigger_message,
                    "recovery_available": True
                }
            )

        # 2. Check safe mode
        sm = get_safe_mode()
        if sm.is_safe_mode() and not sm.is_operation_allowed("agent_execution"):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Agent execution not allowed in current mode",
                    "safe_mode_level": sm.current_level.value,
                    "enter_reason": sm.enter_reason,
                    "allowed_operations": sm.get_limits()['allowed_operations']
                }
            )

        # 3. Validate input
        classifier = get_classifier()
        input_check = classifier.check_input(request.message, ContentType.USER_INPUT)
        if not input_check.safe:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Input blocked by safety check",
                    "reason": input_check.violation.reason,
                    "violation_type": input_check.violation.violation_type.value,
                    "should_trigger_kill_switch": input_check.should_trigger_kill_switch
                }
            )

        # Get Blackbox5 instance
        bb5 = await get_blackbox5()

        # Build context
        context = request.context or {}
        if request.agent:
            context['forced_agent'] = request.agent
        if request.strategy and request.strategy != 'auto':
            context['strategy'] = request.strategy

        # Process request
        result = await bb5.process_request(request.message, request.session_id, context)

        # 4. Validate output
        if isinstance(result, dict) and 'result' in result:
            result_output = result['result'].get('output', '')
            if isinstance(result_output, str):
                output_check = classifier.check_output(result_output, ContentType.AGENT_OUTPUT)
                if not output_check.safe:
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error": "Output blocked by safety check",
                            "reason": output_check.violation.reason
                        }
                    )

        # Return response
        return ChatResponse(
            success=result.get('result', {}).get('success', False),
            session_id=result.get('session_id', ''),
            timestamp=result.get('timestamp', datetime.utcnow().isoformat()),
            routing=result.get('routing'),
            result=result.get('result'),
            error=result.get('result', {}).get('error'),
            guide_suggestions=result.get('guide_suggestions')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e)
            }
        )


# ============================================================================
# Agent Endpoints
# ============================================================================

@app.get("/agents", response_model=List[AgentInfo], tags=["Agents"])
async def list_agents():
    """
    List all available agents.
    """
    try:
        bb5 = await get_blackbox5()

        agents = []
        for name, agent in bb5._agents.items():
            agents.append(AgentInfo(
                name=name,
                role=agent.role,
                category=agent.category or "general",
                description=agent.config.description,
                capabilities=agent.config.capabilities
            ))

        return agents

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@app.get("/agents/{agent_name}", response_model=AgentInfo, tags=["Agents"])
async def get_agent_info(agent_name: str):
    """
    Get detailed information about a specific agent.
    """
    try:
        bb5 = await get_blackbox5()

        agent = bb5._agents.get(agent_name)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_name}' not found"
            )

        return AgentInfo(
            name=agent_name,
            role=agent.role,
            category=agent.category or "general",
            description=agent.config.description,
            capabilities=agent.config.capabilities
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {str(e)}")


# ============================================================================
# Skills Endpoints
# ============================================================================

@app.get("/skills", tags=["Skills"])
async def list_skills(category: Optional[str] = None):
    """
    List all available skills, optionally filtered by category.
    """
    try:
        bb5 = await get_blackbox5()

        if not bb5._skill_manager:
            raise HTTPException(
                status_code=503,
                detail="Skill manager not available"
            )

        skills_data = {}
        for cat in bb5._skill_manager.list_categories():
            if category and cat != category:
                continue
            skills = bb5._skill_manager.get_skills_by_category(cat)
            skills_data[cat] = [
                {"name": s.name, "description": s.description}
                for s in skills
            ]

        return skills_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list skills: {str(e)}")


# ============================================================================
# Guides Endpoints
# ============================================================================

@app.get("/guides/search")
async def search_guides(q: str):
    """Search for guides by keyword"""
    try:
        bb5 = await get_blackbox5()
        results = bb5._guide.search_guides(q)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search guides: {str(e)}")


@app.get("/guides/intent")
async def find_guides_by_intent(intent: str):
    """Find guides by natural language intent"""
    try:
        bb5 = await get_blackbox5()
        matches = bb5._guide.find_by_intent(intent, {})
        return {"matches": matches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find guides: {str(e)}")


# ============================================================================
# Statistics Endpoint
# ============================================================================

@app.get("/stats", tags=["System"])
async def get_statistics():
    """
    Get system statistics.
    """
    try:
        bb5 = await get_blackbox5()
        return await bb5.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
