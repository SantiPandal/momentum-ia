"""
Simple health check endpoints - no over-engineering.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/health")
def health_check():
    """Basic health check - is the service running?"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "momentum-ia"
    }

@router.get("/ready")
def readiness_check():
    """Check if service can handle requests"""
    checks = {}
    
    # Check database connection
    try:
        from services.agent_tools import supabase
        # Simple query to test connection
        result = supabase.table("users").select("id").limit(1).execute()
        checks["database"] = "healthy"
        logger.debug("Database health check passed")
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)[:100]}"
        logger.error(f"Database health check failed: {e}")
    
    # Check if configuration is loaded
    try:
        from config import settings
        if settings.SUPABASE_URL and settings.TWILIO_ACCOUNT_SID:
            checks["config"] = "healthy"
        else:
            checks["config"] = "unhealthy: missing required config"
    except Exception as e:
        checks["config"] = f"unhealthy: {str(e)[:100]}"
    
    # Determine overall health
    all_healthy = all("healthy" in status for status in checks.values())
    
    if not all_healthy:
        logger.warning(f"Readiness check failed: {checks}")
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    
    return {"status": "ready", "checks": checks}