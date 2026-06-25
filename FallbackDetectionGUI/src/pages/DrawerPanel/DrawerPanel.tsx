import { NavLink, useMatch } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  FaHome,
  FaComment,
  FaInfoCircle,
  FaClock,
  FaCog,
} from "react-icons/fa";
import "./DrawerPanel.css";
import { IoMdCloseCircle } from "react-icons/io";


// ---------- Sub‑components ----------

// DrawerLink – individual navigation link
interface DrawerLinkProps {
  to: string;
  icon: React.ReactNode;   // now accepts a React component (icon)
  label: string;
}

const DrawerLink: React.FC<DrawerLinkProps> = ({ to, icon, label }) => {
  const match = useMatch(to);
  const isActive = !!match;

  return (
    <NavLink
      to={to}
      className={`drawer-link ${isActive ? "drawer-link-active" : ""}`}
    >
      <span className="drawer-link-icon">{icon}</span>
      <span className="drawer-link-label">{label}</span>
      <span className="drawer-link-arrow">›</span>
    </NavLink>
  );
};

// DrawerBrand – logo / brand area
const DrawerBrand = () => {
  const dispatch=useDispatch()
  
  return(
  <div className="drawer-brand">
    <span className="drawer-brand-icon">◈</span>
    <div className="drawer-brand-text">
      <span className="drawer-brand-name">RAG Suite</span>
      <span className="drawer-brand-sub">Navigation</span>
    </div>
    <div className="drawer-close-button" onClick={()=>{dispatch({type:"toggle drawer panel"})}}>
        <span className="chat-panel-drawer-icon">
         <IoMdCloseCircle />
        </span>
    </div>
  </div>
)};

// DrawerDivider – simple divider
const DrawerDivider = () => <div className="drawer-divider" />;

// DrawerNav – navigation section with **explicit** links (no map)
const DrawerNav = () => (
  <nav className="drawer-nav">
    <span className="drawer-nav-label">Main Menu</span>
    <div className="drawer-links-list">
      {/* Each link is added manually – exactly what you asked for */}
      <DrawerLink to="/" icon={<FaHome />} label="Home" />
      <DrawerLink to="/about" icon={<FaInfoCircle />} label="About" />
      {/* <DrawerLink to="/chat" icon={<FaComment />} label="Chat" />
      <DrawerLink to="/info" icon={<FaInfoCircle />} label="Info" />
      <DrawerLink to="/history" icon={<FaClock />} label="History" />
      <DrawerLink to="/settings" icon={<FaCog />} label="Settings" /> */}
    </div>
  </nav>
);

// DrawerFooter – status footer
const DrawerFooter = () => (
  <div className="drawer-footer">
    <span className="drawer-footer-dot" />
    <span className="drawer-footer-text">System Online</span>
  </div>
);

// ---------- Main DrawerPanel (composition) ----------
export default function DrawerPanel() {
  const selector=useSelector((state:any)=>state.NavigationReducer)

  return (
    <div className={`drawer-background ${selector.dashboard_panel && 'drawer-background-active'}`} >
      <div className={`drawer-main-panel ${selector.dashboard_panel && 'drawer-main-panel-active'}`}>
        <DrawerBrand />
        <DrawerDivider />
        <DrawerNav />
        <DrawerDivider />
        <DrawerFooter />
      </div>
    </div>
  );
}