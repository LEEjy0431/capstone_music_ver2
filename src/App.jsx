import { useState } from "react";
import HomePage from "./HomePage";
import AnalysisPage from "./AnalysisPage";
import HistoryPage from "./HistoryPage";
import StatsPage from "./StatsPage";
import ProfilePage from "./ProfilePage";

export function getTheme(dark) {
  return dark ? {
    bg:"#111111",surface:"#1c1c1c",surfaceHover:"#242424",
    gold:"#F0B429",goldDark:"#c8931e",goldText:"#1a1000",
    textPrimary:"#f0f0f0",textSecondary:"#888888",textMuted:"#555555",
    border:"#2a2a2a",cardBg:"#252525",
  } : {
    bg:"#f5f5f5",surface:"#ffffff",surfaceHover:"#f0f0f0",
    gold:"#d4900a",goldDark:"#b8780a",goldText:"#ffffff",
    textPrimary:"#111111",textSecondary:"#555555",textMuted:"#999999",
    border:"#e0e0e0",cardBg:"#f8f8f8",
  };
}

const NAV_ICONS = {
  home:(a)=>(<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={a?2.2:1.8} strokeLinecap="round" strokeLinejoin="round"><path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"/><path d="M9 21V12h6v9"/></svg>),
  analysis:(a)=>(<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={a?2.2:1.8} strokeLinecap="round" strokeLinejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>),
  history:(a)=>(<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={a?2.2:1.8} strokeLinecap="round" strokeLinejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/><polyline points="12 7 12 12 15 15"/></svg>),
  stats:(a)=>(<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={a?2.2:1.8} strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>),
  profile:(a)=>(<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={a?2.2:1.8} strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>),
};

const TABS = [
  {id:"home",label:"홈",icon:NAV_ICONS.home},
  {id:"analysis",label:"분석",icon:NAV_ICONS.analysis},
  {id:"history",label:"기록",icon:NAV_ICONS.history},
  {id:"stats",label:"통계",icon:NAV_ICONS.stats},
  {id:"profile",label:"프로필",icon:NAV_ICONS.profile},
];

function generateFakeResult(fileName) {
  const pitch=70+Math.floor(Math.random()*25);
  const rhythm=70+Math.floor(Math.random()*25);
  const dynamics=70+Math.floor(Math.random()*25);
  const tempo=70+Math.floor(Math.random()*25);
  const avg=Math.round((pitch+rhythm+dynamics+tempo)/4);
  const grade=avg>=90?"A":avg>=85?"A-":avg>=80?"B+":avg>=75?"B":avg>=70?"C+":"C";
  const now=new Date();
  const dateStr=now.toISOString().slice(0,10);
  const hour=now.getHours();
  const min=now.getMinutes();
  const ampm=hour>=12?"오후":"오전";
  const h12=hour%12||12;
  const timeStr=`${ampm} ${h12}:${String(min).padStart(2,"0")}`;
  return {
    id:Date.now(),
    title:fileName.replace(/\.[^/.]+$/,""),
    date:dateStr,time:timeStr,
    duration:`${Math.floor(Math.random()*5+1)}:${String(Math.floor(Math.random()*60)).padStart(2,"0")}`,
    score:avg,grade,pitch,rhythm,dynamics,tempo,
  };
}

export default function App() {
  const [activeTab,setActiveTab]=useState("home");
  const [darkMode,setDarkMode]=useState(true);
  const [records,setRecords]=useState([]);
  const [profile,setProfile]=useState({name:"사용자",email:"user@email.com",level:"초급",joinDate:"2026년 5월"});
  const C=getTheme(darkMode);

  function addRecord(fileName){
    const result=generateFakeResult(fileName);
    setRecords(prev=>[result,...prev]);
    return result;
  }

  const pages={
    home:<HomePage C={C} onNavigate={setActiveTab} records={records}/>,
    analysis:<AnalysisPage C={C} onNavigate={setActiveTab} onUpload={addRecord}/>,
    history:<HistoryPage C={C} records={records}/>,
    stats:<StatsPage C={C} records={records}/>,
    profile:<ProfilePage C={C} darkMode={darkMode} setDarkMode={setDarkMode} profile={profile} setProfile={setProfile} records={records}/>,
  };

  return (
    <div style={{background:C.bg,minHeight:"100dvh",maxWidth:480,margin:"0 auto",fontFamily:"'Apple SD Gothic Neo','Malgun Gothic',sans-serif",position:"relative",overflowX:"hidden",transition:"background .3s"}}>
      <style>{`*{box-sizing:border-box;margin:0;padding:0;}body{background:${darkMode?"#0a0a0a":"#e8e8e8"};}::-webkit-scrollbar{display:none;}button,input{font-family:inherit;}`}</style>
      {pages[activeTab]}
      <div style={{position:"fixed",bottom:0,left:"50%",transform:"translateX(-50%)",width:"100%",maxWidth:480,background:darkMode?"#161616":"#ffffff",borderTop:`1px solid ${C.border}`,display:"flex",padding:"10px 0 20px",zIndex:100,transition:"background .3s"}}>
        {TABS.map(tab=>(
          <button key={tab.id} onClick={()=>setActiveTab(tab.id)} style={{flex:1,background:"none",border:"none",cursor:"pointer",display:"flex",flexDirection:"column",alignItems:"center",gap:4,color:activeTab===tab.id?C.gold:C.textMuted,fontSize:11,transition:"color .2s",padding:"4px 0"}}>
            {tab.icon(activeTab===tab.id)}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}