"""
RAG Financial Knowledge System
Uses LangChain + Pinecone for semantic search over financial knowledge base
"""
from typing import List, Optional, Dict
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document


class FinancialRAGSystem:
    """
    RAG (Retrieval-Augmented Generation) system for financial knowledge.

    Architecture:
    1. Financial knowledge base documents (personal finance, investing, tax, etc.)
    2. Chunk + embed with OpenAI text-embedding-3-small
    3. Store embeddings in Pinecone vector DB
    4. Query: embed user question → semantic search → augment LLM prompt
    """

    def __init__(self, openai_api_key: str, pinecone_api_key: str, pinecone_index: str):
        self.openai_api_key = openai_api_key
        self.pinecone_api_key = pinecone_api_key
        self.pinecone_index = pinecone_index

        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            model="text-embedding-3-small",
        )
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model="gpt-4o",
            temperature=0.3,
        )
        self.vectorstore = None
        self._initialize_pinecone()

    def _initialize_pinecone(self):
        """Connect to Pinecone vector database"""
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=self.pinecone_api_key)
            from langchain_community.vectorstores import Pinecone as LangchainPinecone
            self.vectorstore = LangchainPinecone.from_existing_index(
                index_name=self.pinecone_index,
                embedding=self.embeddings,
            )
            print("✅ Connected to Pinecone vector store")
        except Exception as e:
            print(f"⚠️ Pinecone connection failed: {e}. Using in-memory fallback.")
            self.vectorstore = None

    def ingest_knowledge_base(self, knowledge_dir: str = "ml/rag/knowledge_base"):
        """Load, chunk, and embed financial documents into Pinecone"""
        print(f"📚 Loading documents from {knowledge_dir}...")

        loader = DirectoryLoader(knowledge_dir, glob="**/*.txt", loader_cls=TextLoader)
        docs = loader.load()
        print(f"  Loaded {len(docs)} documents")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )
        chunks = splitter.split_documents(docs)
        print(f"  Split into {len(chunks)} chunks")

        if self.vectorstore:
            self.vectorstore.add_documents(chunks)
            print(f"✅ Ingested {len(chunks)} chunks into Pinecone")
        else:
            # Fallback: in-memory FAISS
            from langchain_community.vectorstores import FAISS
            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
            print(f"✅ Ingested {len(chunks)} chunks into in-memory FAISS")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Semantic search over knowledge base"""
        if not self.vectorstore:
            return []

        results = self.vectorstore.similarity_search_with_score(query, k=top_k)
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "score": float(score),
            }
            for doc, score in results
        ]

    def answer_question(self, question: str, financial_context: str = "") -> str:
        """Answer a financial question using RAG"""
        if not self.vectorstore:
            return "Knowledge base not available."

        # Augment with personal financial context
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=False,
        )

        augmented_question = question
        if financial_context:
            augmented_question = (
                f"Personal Financial Context:\n{financial_context}\n\n"
                f"Question: {question}"
            )

        result = chain.invoke({"query": augmented_question})
        return result.get("result", "Unable to answer the question.")


# ── Indian Finance Knowledge Base Documents ─────────────────────────────────────

INDIAN_FINANCE_KNOWLEDGE = """
# Indian Personal Finance Guide

## Tax-Saving Investments (Section 80C)
- PPF (Public Provident Fund): Tax-free returns ~7.1%, 15-year lock-in
- ELSS (Equity Linked Savings Scheme): 3-year lock-in, market-linked returns
- NSC (National Savings Certificate): Fixed returns, 5-year tenure
- Life Insurance Premiums: Up to ₹1.5L deductible
- Home Loan Principal: Tax deductible under 80C

## Emergency Fund Guidelines
- Maintain 3-6 months of monthly expenses
- Keep in liquid instruments: savings account, liquid mutual funds
- Never invest emergency fund in equity

## SIP (Systematic Investment Plan) Tips
- Start early: Power of compounding
- Automate monthly investments
- Avoid stopping during market downturns
- Choose funds based on risk profile and investment horizon

## Credit Score Management
- Pay all bills on time — most critical factor (35% weight)
- Keep credit utilization below 30%
- Don't apply for multiple loans simultaneously
- Maintain old credit cards (length of history matters)

## 50-30-20 Budgeting Rule
- 50% of income: Needs (rent, food, utilities, EMIs)
- 30% of income: Wants (entertainment, dining, travel)
- 20% of income: Savings and investments

## GST on Financial Products
- Insurance premiums: 18% GST
- Mutual fund management fees: 18% GST
- Banking services: 18% GST

## Health Insurance
- Minimum recommended: ₹5-10L individual, ₹10-20L family floater
- Tax deduction: Up to ₹25,000 for self/family (₹50,000 for senior parents)

## National Pension System (NPS)
- Additional tax benefit: ₹50,000 under 80CCD(1B)
- Tier-I: Mandatory, locked till retirement
- Tier-II: Voluntary, withdrawable anytime

## Debt Management
- Debt-to-income ratio should not exceed 40%
- Prioritize high-interest debt (credit cards: 36-48% p.a.)
- Snowball method: Pay smallest debt first for motivation
- Avalanche method: Pay highest interest debt first (saves more)
"""


def create_knowledge_base(output_dir: str = "ml/rag/knowledge_base"):
    """Create initial financial knowledge base documents"""
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "indian_finance_guide.txt"), "w") as f:
        f.write(INDIAN_FINANCE_KNOWLEDGE)

    print(f"✅ Knowledge base created in {output_dir}")


if __name__ == "__main__":
    create_knowledge_base()
    print("Run ingestion with: rag = FinancialRAGSystem(...); rag.ingest_knowledge_base()")
