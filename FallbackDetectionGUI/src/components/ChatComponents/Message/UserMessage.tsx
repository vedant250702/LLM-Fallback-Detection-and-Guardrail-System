import React from "react";
import { MessageType } from "../../../types/DetectionData";
import { useState } from "react";
import { LuCopy, LuCheck } from "react-icons/lu";
import "./Message.css"

const UserMessage:React.FC<MessageType>=({message})=>{
  const [copied, setCopied] = useState(false);


  const handleCopy = () => {
    navigator.clipboard.writeText(message);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };


  return(
    <div className="message-wrapper">
      <div className="message-main user-message">
          {message}
      </div>
      <div className="user-message-actions">
        <span className={`message-action-btn ${copied ? "action-active" : ""}`} 
                onClick={handleCopy}>
          {copied ? <LuCheck size={13} /> : <LuCopy size={13} />}

        </span>
      </div>
    </div>
  )
}

export default UserMessage