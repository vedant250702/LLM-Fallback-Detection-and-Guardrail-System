from fastapi import APIRouter 
from pydantic import BaseModel
from apps.utils.RAG_Agent import RAGPipelineCareerGuidance
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import dotenv
dotenv.load_dotenv()

router=APIRouter()
api_key = os.environ["MISTRAL_APIKEY"]
retrieval_embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# classifier_embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

llm=RAGPipelineCareerGuidance(embeddings=retrieval_embedding,directory="./apps/storage/career_rag_index",api_key=api_key)


class ModelsInputs(BaseModel):
    turn_rank:int
    current_query:str
    prev_queries:list[str] | None
    prev_responses:list[str] | None


@router.post("/llm_call")
def api_call(request:ModelsInputs):
    answers=llm.generateResponses(question=request.current_query,prev_responses=request.prev_responses,prev_queries=request.prev_queries)

    reason="This is the particular reason"
    confidence_score=0.56
    return {"status":True, "response":answers["answer"], "reason":reason, "confidence_score":confidence_score, "current_query":request.current_query}



class AnalysisModel(BaseModel):
    turn_rank:int
    current_query:str
    prev_queries:list[str] | None
    prev_responses:list[str] | None

@router.post("/llm-analysis")
def analyze(request):
    return {"status":True}