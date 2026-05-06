import { useState, useRef } from "react";

export default function AnalysisPage({ C, onNavigate, onUpload }) {
  const [file,setFile]=useState(null);
  const [dragging,setDragging]=useState(false);
  const [analyzing,setAnalyzing]=useState(false);
  const [result,setResult]=useState(null);
  const inputRef=useRef();

  function handleFile(f){ if(!f)return; setFile(f); setResult(null); }
  function handleDrop(e){ e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]); }

  function handleAnalyze(){
    if(!file)return;
    setAnalyzing(true);
    setTimeout(()=>{
      const r=onUpload(file.name);
      setResult(r);
      setAnalyzing(false);
    },2500);
  }

  const scoreColor=(v)=>v>=90?"#80d0ff":v>=80?C.gold:"#ff9f43";

  return (
    <div style={{padding:"56px 18px 110px",display:"flex",flexDirection:"column",gap:16}}>
      <div>
        <h1 style={{fontSize:28,fontWeight:700,color:C.textPrimary,margin:0,letterSpacing:"-.02em"}}>연습 분석</h1>
        <p style={{fontSize:14,color:C.textSecondary,margin:"6px 0 0"}}>음원 파일을 업로드하여 상세한 피드백을 받으세요</p>
      </div>

      <div
        onDragOver={e=>{e.preventDefault();setDragging(true);}}
        onDragLeave={()=>setDragging(false)}
        onDrop={handleDrop}
        onClick={()=>!result&&inputRef.current.click()}
        style={{border:`2px dashed ${dragging?C.gold:result?C.goldDark:"#3a3a3a"}`,borderRadius:16,padding:"48px 24px",display:"flex",flexDirection:"column",alignItems:"center",gap:12,cursor:result?"default":"pointer",background:dragging?"rgba(240,180,41,0.05)":C.surface,transition:"all .2s"}}
      >
        <div style={{width:64,height:64,borderRadius:"50%",background:"rgba(240,180,41,0.15)",display:"flex",alignItems:"center",justifyContent:"center"}}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={C.gold} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <div style={{textAlign:"center"}}>
          <div style={{fontSize:17,fontWeight:700,color:C.textPrimary,marginBottom:6}}>
            {file?file.name:"음원 파일 업로드"}
          </div>
          <div style={{fontSize:13,color:C.textSecondary}}>
            {file?`${(file.size/1024/1024).toFixed(2)} MB`:"파일을 여기에 드래그하거나 클릭하여 선택하세요"}
          </div>
          {!file&&<div style={{fontSize:12,color:C.textMuted,marginTop:4}}>MP3, WAV, M4A 등 모든 오디오 형식 지원</div>}
        </div>
        {!file&&(
          <button style={{background:C.gold,color:C.goldText,border:"none",borderRadius:12,padding:"12px 28px",fontSize:15,fontWeight:700,cursor:"pointer",marginTop:4}}>
            파일 선택하기
          </button>
        )}
        <input ref={inputRef} type="file" accept="audio/*" style={{display:"none"}} onChange={e=>handleFile(e.target.files[0])}/>
      </div>

      {file&&!result&&(
        <button onClick={handleAnalyze} disabled={analyzing} style={{width:"100%",background:analyzing?C.goldDark:`linear-gradient(135deg,${C.gold},${C.goldDark})`,border:"none",borderRadius:14,padding:"18px",fontSize:16,fontWeight:700,color:C.goldText,cursor:analyzing?"not-allowed":"pointer",transition:".2s"}}>
          {analyzing?"⏳ 분석 중...":"🎵 분석 시작하기"}
        </button>
      )}

      {result&&(
        <>
          <div style={{background:C.surface,borderRadius:16,padding:20,display:"flex",flexDirection:"column",gap:14}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
              <div style={{fontSize:15,fontWeight:600,color:C.textPrimary}}>분석 완료 ✅</div>
              <div style={{textAlign:"right"}}>
                <div style={{fontSize:28,fontWeight:700,color:scoreColor(result.score)}}>{result.score}%</div>
                <div style={{fontSize:13,color:C.textMuted}}>{result.grade}</div>
              </div>
            </div>
            {[
              {label:"음정 정확도",value:result.pitch,  color:C.gold},
              {label:"리듬 안정성",value:result.rhythm,  color:"#7ee8a2"},
              {label:"다이나믹",   value:result.dynamics,color:"#80d0ff"},
              {label:"템포 일관성",value:result.tempo,   color:"#c77dff"},
            ].map(item=>(
              <div key={item.label}>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}>
                  <span style={{fontSize:13,color:C.textSecondary}}>{item.label}</span>
                  <span style={{fontSize:13,fontWeight:700,color:item.color}}>{item.value}%</span>
                </div>
                <div style={{height:6,background:"#2a2a2a",borderRadius:3}}>
                  <div style={{height:"100%",width:`${item.value}%`,background:item.color,borderRadius:3,transition:"width 1s ease"}}/>
                </div>
              </div>
            ))}
          </div>
          <div style={{display:"flex",gap:10}}>
            <button onClick={()=>{setFile(null);setResult(null);}} style={{flex:1,background:C.surface,border:`1px solid ${C.border}`,borderRadius:14,padding:"14px",fontSize:14,fontWeight:600,color:C.textSecondary,cursor:"pointer"}}>
              다시 업로드
            </button>
            <button onClick={()=>onNavigate("history")} style={{flex:1,background:`linear-gradient(135deg,${C.gold},${C.goldDark})`,border:"none",borderRadius:14,padding:"14px",fontSize:14,fontWeight:600,color:C.goldText,cursor:"pointer"}}>
              기록 보기 →
            </button>
          </div>
        </>
      )}
    </div>
  );
}