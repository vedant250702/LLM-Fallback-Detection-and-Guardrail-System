import { DetectionData } from "../../types/DetectionData";
import "./DetectionPanel.css";
import { BiAnalyse } from "react-icons/bi";
import { useDispatch } from "react-redux";
import { FaWindowClose } from "react-icons/fa";
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";



export default function DetectionPanel() {

  const chat_selector:any=useSelector((state:any)=>state.ChatMessagesReducer)
  const navigation_selector:any=useSelector((state:any)=>state.NavigationReducer)
  const analysis_selector:any=useSelector((state:any)=>state.AnalysisReducer)



  useEffect(()=>{

  },[])


  return (
    <>
      <div className="detection-panel-main">

        {/* 1. Header */}
        <div className="dp-header">
          <span className="dp-title">Fallback Analysis</span>
          <span className="analysis-button-mobile">
            <AnalysisDrawerIcon/>
          </span>
        </div>
          {analysis_selector.analysis_turn_rank_number!=null&&
            <>
              {/* 2. Status Badge + Confidence Bar */}
              <StatusSection score={chat_selector.confidence_score[Number(analysis_selector.analysis_turn_rank_number-1)]} category={chat_selector.category[Number(analysis_selector.analysis_turn_rank_number-1)]}/>

              {/* 3. Query */}
              <InfoBlock label="📌 Current Query" text={chat_selector.prev_queries[Number(analysis_selector.analysis_turn_rank_number)-1]} />

              {/* 4. Retrieved Context */}
              <InfoBlock label="📄 Retrieved Context" text="" />

              {/* 5. Generated Response */}
              {/* <InfoBlock label="🤖 Generated Response" text="" /> */}

              {/* 6. Reason */}
              <ReasonBlock text={analysis_selector.collection[analysis_selector.analysis_turn_rank_number].reason}/>

              {/* 7. Similarity Scores */}
              <ScoresBlock />
            </>
          }
      </div>
    </>
  )
}

interface StatusSectionTypes{
  score:number,
  category:number
}
const StatusSection:React.FC<StatusSectionTypes>=({score,category})=>{
  return (
    <div className="dp-status-section">
      <div className="dp-status-badge">
        <span className="dp-status-dot" />
        <span className="dp-status-label">{Number(category)==0?"NOT FALLBACK":"FALLBACK"}</span>
      </div>
      <div className="dp-confidence-row">
        <span className="dp-conf-label">Confidence</span>
        <span className="dp-conf-value">{Math.round(score*100)/100}%</span>
      </div>
      <div className="dp-bar-bg">
        <div className="dp-bar-fill" style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}


interface InfoBlockTypes{ 
      label: string; 
      text: string 
}
const InfoBlock:React.FC<InfoBlockTypes>=({label,text})=>{
  return (
    <div className="dp-info-block">
      <p className="dp-info-label">{label}</p>
      <p className="dp-info-text">{text}</p>
    </div>
  );
}


interface ReasonBlockType{
  text:string
}
const ReasonBlock:React.FC<ReasonBlockType>=({text})=>{
  return (
    <div className="dp-reason-block">
      <p className="dp-info-label">⚠️ Reason</p>
      <p className="dp-info-text">{text}</p>
    </div>
  );
}

const ScoresBlock:React.FC=()=>{
  return (
    <div className="dp-scores-block">
      <p className="dp-info-label">📊 Similarity Scores</p>
      <div className="dp-scores-list">
        {/* score rows will go here */}
      </div>
    </div>
  );
}

const AnalysisDrawerIcon:React.FC=()=>{
  const dispatch=useDispatch()
  return(
    <span className='chat-panel-analysis-icon' onClick={()=>{dispatch({type:"toggle analysis panel",payload:null})}}>
      <FaWindowClose />
    </span>
  )
}