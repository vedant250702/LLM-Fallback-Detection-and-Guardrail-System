from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.routes.query_routes import router
import dotenv

dotenv.load_dotenv()
app=FastAPI()


allow_origins=["*"]

app.add_middleware(CORSMiddleware,allow_origins=allow_origins,allow_credentials=True,allow_methods=["*"])
app.include_router(prefix="/api/query",router=router)


@app.get("/")
def testRoute():
    return {'status':True}