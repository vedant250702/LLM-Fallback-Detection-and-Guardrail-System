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
    const chat_selector=useSelector((state:any)=>state.ChatMessagesReducer)
  
    const handleCopy = () => {
      navigator.clipboard.writeText(message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };

    const analyze=async()=>{
      dispatch({type:"toggle analysis loading",payload:true})
      setTimeout(() => {
        dispatch({type:"current turn_rank",payload:turn_rank})
        dispatch({type:"toggle analysis panel",payload:true})
      }, 50);

      let data=Object.keys(selector.collection)
      if(turn_rank){
        if (turn_rank in data){
          dispatch({type:"toggle analysis loading",payload:false})
        }else{

          let prev_history_length=chat_selector.prev_queries.length

          let data={turn_rank:Number(turn_rank),
                    current_query:chat_selector.prev_queries[Number(turn_rank)-1],
                    response:message,
                    context:chat_selector.context[Number(turn_rank)-1],
                    prev_queries:chat_selector.prev_queries.slice(0,prev_history_length-1),
                    prev_responses:chat_selector.prev_responses.slice(0,prev_history_length-1),
                    label:chat_selector.category[Number(turn_rank)-1]
          }

          await axios.post(import.meta.env.VITE_APP_BASEURL+"/api/query/llm_analysis",data)
          .then((response)=>{
              let payload={reason:response.data.reason,  turn_rank:turn_rank, steps:response.data.steps}
              dispatch({type:'add analysis information',payload:payload})
              dispatch({type:"toggle analysis loading",payload:false})
          })
          .catch((err)=>{
            console.log(err)
          })
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