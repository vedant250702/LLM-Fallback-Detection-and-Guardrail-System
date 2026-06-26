import "./LoadingMessage.css";

const LoadingMessage:React.FC=()=> {
  return (
    <div className="message-wrapper">
      <div className="message-main system-message loading-message">
        <span className="loading-dot" />
        <span className="loading-dot" />
        <span className="loading-dot" />
      </div>
    </div>
  );
}


export default LoadingMessage