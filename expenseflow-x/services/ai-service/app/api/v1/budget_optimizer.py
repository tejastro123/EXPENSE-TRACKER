from fastapi import APIRouter

router = APIRouter()

@router.get("/optimize")
async def optimize_budget(user_id: str):
    return {
        "user_id": user_id,
        "recommendations": [
            {"category": "Dining Out", "suggested_reduction_pct": 20, "estimated_savings_inr": 2500},
            {"category": "Subscriptions", "suggested_reduction_pct": 50, "estimated_savings_inr": 800}
        ]
    }
