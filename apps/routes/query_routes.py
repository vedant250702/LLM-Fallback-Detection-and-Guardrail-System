from fastapi import APIRouter 
from pydantic import BaseModel
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import dotenv

from apps.utils.RAG_Agent import RAGPipelineCareerGuidance
from apps.utils.FallbackDetection import ClassificationModel, FormatModelClassificationInput


### Generating the Instances of the required methods.
dotenv.load_dotenv()
router=APIRouter()
api_key = os.environ["MISTRAL_APIKEY"]
retrieval_embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
classifier_embedding="intfloat/e5-base-v2"

llm=RAGPipelineCareerGuidance(embeddings=retrieval_embedding,directory="./apps/storage/career_rag_index",api_key=api_key)
classifier=ClassificationModel(device="cpu",embedder_model_name=classifier_embedding,model_path="./apps/model/fallback_attention_model.pt")


#------------------------------------------
# Below are the methods for the API Calls |      
#------------------------------------------

class ModelsInputs(BaseModel):
    turn_rank:int
    current_query:str
    prev_queries:list[str] | None
    prev_responses:list[str] | None


@router.post("/llm_call")
def api_call(request:ModelsInputs):

    # Calling LLM API for generating the Response.
    result=llm.generateResponses(question=request.current_query,prev_responses=request.prev_responses,prev_queries=request.prev_queries)

    # Format Input for the classification model.
    input_data=FormatModelClassificationInput(query=request.current_query, response=result["answer"], retrieved_context=result["context"],prev_queries=request.prev_queries,prev_responses=request.prev_responses,turn_rank=request.turn_rank)

    # Making the predictions based on the generated response, history and query.
    predictions=classifier.predict(input_data=input_data,return_proba=True)
    
    pred=predictions[0]
    pred_class=pred.index(max(pred))

    reason="This is the particular reason"

    return {"status":True, "response":result["answer"], "reason":reason, "confidence_score":max(pred)*100, "current_query":request.current_query, "category":pred_class}



class AnalysisModel(BaseModel):
    turn_rank:int
    current_query:str
    prev_queries:list[str] | None
    prev_responses:list[str] | None

@router.post("/llm-analysis")
def analyze(request):
    return {"status":True}