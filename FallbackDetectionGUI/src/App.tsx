import { useState } from "react";
import ChatPanel from "./pages/ChatPanel/ChatPanel";
import DetectionPanel from "./pages/DetectionPanel/DetectionPanel";
import "./App.css";



export default function App() {
  return (
    <div className="app-container">
      <div className="left-panel">
        <ChatPanel/>
      </div>
      <div className="right-panel">
        <DetectionPanel/>
      </div>
    </div>
  );
}
