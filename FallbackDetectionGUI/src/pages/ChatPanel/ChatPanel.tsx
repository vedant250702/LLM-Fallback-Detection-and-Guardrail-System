import React, { useEffect } from 'react'
import { useState } from 'react';
import axios from 'axios'
import "./ChatPanel.css"
import { BsLayoutSidebarInset } from "react-icons/bs";
import { FaArrowUp } from "react-icons/fa6";
import { BiAnalyse } from "react-icons/bi";
import UserMessage from '../../components/ChatComponents/Message/UserMessage';
import SystemMessage from '../../components/ChatComponents/Message/SystemMessage';
import { useDispatch, useSelector } from 'react-redux';
import EmptyChat from '../../components/ChatComponents/EmptyChat/EmptyChat';
import LoadingMessage from '../../components/ChatComponents/Loading/LoadingMessage';



const ChatPanel:React.FC = () => {
  const [message, setMessage] = useState('');
  const [isLoading, setisLoading] = useState(false)

  const dispatch=useDispatch()
  const selector:any=useSelector((state:any)=>state.ChatMessagesReducer)
  const components_selector=useSelector((state:any)=>state.ChatDisplayReducer)



  const handleSend = async() => {
    if (message.trim() && !isLoading) {
      // Here you would send the message to your chat logic
      let turn_rank=selector.turn_rank
      let data={
        turn_rank:turn_rank[turn_rank.length-1],
        current_query:message,
        prev_queries:selector.prev_queries,
        prev_responses:selector.prev_responses
      }

      dispatch({type:"add chat component",payload:{role:"user",message:message}})
      setMessage('')
      setisLoading(true)
      await axios.post(import.meta.env.VITE_APP_BASEURL+"/api/query/llm_call",data)
      .then((response)=>{
          // Updating the storage for the Response
          setisLoading(false)
          dispatch({type:"update new response", payload:response.data})

          // Adding the Message Component for the response of the LLM
          dispatch({type:"add chat component",payload:{role:"system",message:response.data.response}})
          console.log(selector)
      })
      .catch((err)=>{
        console.log(err)
      })

    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className='chat-panel-main'>
      {/* HEADER OF THE APP WHERE NAME, DRAWER AND ANALYSIS BUTTONS WILL BE VISIBLE */}
        <div className='chat-panel-header-section'>
          <HeadingDrawerIcon/>
          <HeadingText/>
          <div className='chat-panel-header-right-corner'>
            <AnalysisDrawerIcon/>
          </div>

        </div>


        {/* MESSAGE SECTION WHERE ALL THE MESSAGES WILL BE APPENDED */}
        <div className='chat-panel-message-section'>
          <div className='chat-panel-message-sub-section'>
          {components_selector.messages.length==0 && <EmptyChat/>}
          {components_selector.messages.map((val:any, index:number)=>(
              <>
                {val.role=="user"?
                  <UserMessage message={val.message} turn_rank={index+1}/>
                :val.role=="system"&&
                  <SystemMessage message={val.message} turn_rank={(index+1)/2}/>
                }
              </>
            ))
          }
          {isLoading && <LoadingMessage />}
          

          </div>

        </div>
          
        <div className='chat-panel-input-section'>
          <InputSection message={message} handleKeyDown={handleKeyDown} setMessage={setMessage} handleSend={handleSend}/>
        </div>

    </div>
  )
}








// Below are the Functional Components used in the Chat Panel
const HeadingText:React.FC=()=>{
  return (
    <div className='chat-panel-name'>
      <h3>Career Guidance</h3>
      <b>RAG Agent + Fallback Detection</b>
    </div>
  )
}

const HeadingDrawerIcon:React.FC=()=>{
    const dispatch=useDispatch()
  return(
    <span className='chat-panel-drawer-icon' onClick={()=>{dispatch({type:"toggle drawer panel"})}}>
      <BsLayoutSidebarInset />
    </span>
  )
}

const AnalysisDrawerIcon:React.FC=()=>{
  const dispatch=useDispatch()
  return(
    <span className='chat-panel-analysis-icon' onClick={()=>{dispatch({type:"toggle analysis panel",payload:null})}}>
      <BiAnalyse />
    </span>
  )
}


interface InputSectionTypes{
  message:string,
  setMessage:Function,
  handleKeyDown:any,
  handleSend:any,
}
const InputSection:React.FC<InputSectionTypes>=({message,setMessage,handleKeyDown,handleSend})=>{

  return(
    <>
      <div className="input-container">
        <input
          type="text"
          className="chat-input"
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className="send-button" onClick={handleSend} aria-label="Send">
          <span>
            <FaArrowUp />
          </span>
        </button>
      </div>
    </>
  )
}


export default ChatPanel