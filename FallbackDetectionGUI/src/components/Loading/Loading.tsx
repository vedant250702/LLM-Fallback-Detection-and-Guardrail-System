import React from 'react'
import "./Loading.css"
import { BiAnalyse } from "react-icons/bi";
const Loading = () => {
  return (
    <div className='loading-main'>
        <span className='loading-icon'>
            <BiAnalyse />
        </span> 
     <b>Analysing</b>
    </div>

  )
}

export default Loading