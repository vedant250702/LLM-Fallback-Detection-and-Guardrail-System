import { useState } from "react";
import ChatPanel from "./pages/ChatPanel/ChatPanel";
import DetectionPanel from "./pages/DetectionPanel/DetectionPanel";
import DrawerPanel from "./pages/DrawerPanel/DrawerPanel";
import "./App.css";
import { useSelector, UseSelector } from "react-redux";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";


const MainApp=()=>{
  
  const selector=useSelector((state:any)=>state.NavigationReducer)

  return(
    <div className="app-container">
      <DrawerPanel/>

      <div className="left-panel">
        <ChatPanel/>
      </div>

      <div className={`right-panel ${selector.analysis_panel && 'right-panel-open'}`}>
        <DetectionPanel/>
      </div>
      
    </div>
  )
}




export default function App() {

  return (
    <>
    <Router>
      <Routes>
        <Route path="/" element={<MainApp/>}/>
      </Routes>
    </Router>
    </>
  )
}
