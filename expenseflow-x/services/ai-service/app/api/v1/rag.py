from fastapi import APIRouter

router = APIRouter()

@router.get("/query")
async def query_knowledge_base(question: str):
    # Mock RAG response
    return {
        "question": question,
        "answer": "Under Section 80C of the Indian Income Tax Act, you can claim a deduction of up to ₹1.5 Lakhs by investing in tax-saving instruments such as PPF, ELSS, NPS, and NSC.",
        "sources": ["indian_finance_guide.txt"]
    }
