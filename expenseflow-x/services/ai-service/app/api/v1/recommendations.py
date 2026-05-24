from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_recommendations(user_id: str):
    return {
        "user_id": user_id,
        "insights": [
            {
                "type": "savings_alert",
                "title": "Invest surplus cash",
                "description": "You have ₹25,000 idle in your savings account. Investing in a liquid mutual fund could yield an extra 6.5% interest."
            },
            {
                "type": "tax_saving",
                "title": "ELSS Tax Savings",
                "description": "You have only utilized ₹45,000 of the ₹1,50,000 Section 80C limit. Consider investing in ELSS before March 31."
            }
        ]
    }
