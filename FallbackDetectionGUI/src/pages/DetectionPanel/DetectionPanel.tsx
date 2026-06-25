import { DetectionData } from "../../types/DetectionData";
import "./DetectionPanel.css";
import { BiAnalyse } from "react-icons/bi";
import { useDispatch } from "react-redux";
import { FaWindowClose } from "react-icons/fa";

export default function DetectionPanel() {

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

        {/* 2. Status Badge + Confidence Bar */}
        <StatusSection score={70}/>

        {/* 3. Query */}
        <InfoBlock label="📌 Current Query" text="" />

        {/* 4. Retrieved Context */}
        <InfoBlock label="📄 Retrieved Context" text="" />

        {/* 5. Generated Response */}
        <InfoBlock label="🤖 Generated Response" text="" />

        {/* 6. Reason */}
        <ReasonBlock />

        {/* 7. Similarity Scores */}
        <ScoresBlock />

      </div>
    </>
  )
}

interface StatusSectionTypes{
  score:number
}
const StatusSection:React.FC<StatusSectionTypes>=({score})=>{
  return (
    <div className="dp-status-section">
      <div className="dp-status-badge">
        <span className="dp-status-dot" />
        <span className="dp-status-label">STATUS PLACEHOLDER</span>
      </div>
      <div className="dp-confidence-row">
        <span className="dp-conf-label">Confidence</span>
        <span className="dp-conf-value">{score}%</span>
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



const ReasonBlock:React.FC=()=>{
  return (
    <div className="dp-reason-block">
      <p className="dp-info-label">⚠️ Reason</p>
      <p className="dp-info-text"></p>
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
    <span className='chat-panel-analysis-icon' onClick={()=>{dispatch({type:"toggle analysis panel"})}}>
      <FaWindowClose />
    </span>
  )
}