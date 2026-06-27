import React from "react"
import { useState } from "react";
import { MessageType } from "../../../types/DetectionData"
import { LuCopy, LuCheck } from "react-icons/lu";
import { useDispatch, useSelector } from "react-redux";
import axios from "axios";

const SystemMessage:React.FC<MessageType>=({message,turn_rank})=>{

    const [copied, setCopied] = useState(false);
    const dispatch=useDispatch()
    const selector=useSelector((state:any)=>state.AnalysisReducer)
  
    const handleCopy = () => {
      navigator.clipboard.writeText(message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };

    const analyze=async()=>{
      dispatch({type:"toggle analysis loading",payload:true})
      dispatch({type:"toggle analysis panel",payload:true})

      let data=Object.keys(selector.collection)
      if(turn_rank){
        if (turn_rank in data){
          dispatch({type:"current turn_rank",payload:turn_rank})
          dispatch({type:"toggle analysis loading",payload:false})
        }else{
          let payload={reason:'This is the reason',  turn_rank:turn_rank, confidence_score:0.56}
          dispatch({type:'add analysis information',payload:payload})
          dispatch({type:"current turn_rank",payload:turn_rank})
          dispatch({type:"toggle analysis loading",payload:false})
          // await axios.post(import.meta.env.VITE_APP_BASEURL+"/api/llm-analysis")
          // .then((response)=>{

          //   dispatch({type:"toggle analysis loading",payload:false})
          // })
          // .catch((err)=>{

          // })
        }
      }


    }
  
  return(
    <div className="message-wrapper">
      <div className="message-main system-message">
          {message}
      </div>
      <div className="system-message-actions">
              <span className={`message-action-btn ${copied ? "action-active" : ""}`} 
                      onClick={handleCopy}>
                {copied ? <LuCheck size={13} /> : <LuCopy size={13} />}
      
              </span>
              <span className="message-action-btn system-message-analyze-btn" onClick={analyze}>
                  Analyze
              </span>
        </div>
    </div>
    )
}


export default SystemMessage