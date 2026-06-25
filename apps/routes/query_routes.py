from fastapi import APIRouter 
from pydantic import BaseModel

router=APIRouter()

class ModelsInputs(BaseModel):
    turn_rank:int
    current_query:str
    prev_queries:list[str] | None
    prev_responses:list[str] | None



@router.post("/llm_call")
def api_call(request:ModelsInputs):
    print(request)
    response="Hello World"
    reason="This is the particular reason"
    confidence_score=0.56
    return {"status":True, "response":response, "reason":reason, "confidence_score":confidence_score, "current_query":request.current_query}