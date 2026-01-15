import React, { useState, useEffect } from 'react';

// --- Icons ---
const ZapIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

const ChartIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const App = () => {
  const [activeTab, setActiveTab] = useState('predictions'); // 'predictions' or 'analytics'
  const API_BASE = 'http://localhost:8000';
  
  // --- Prediction State ---
  const [predYear, setPredYear] = useState('default');
  const [predRound, setPredRound] = useState('default');
  const [raceOptions, setRaceOptions] = useState([]);
  const [isSyncingCalendar, setIsSyncingCalendar] = useState(false);
  const [predictionData, setPredictionData] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionError, setPredictionError] = useState(null);

  // --- Insights State ---
  const [insightYear, setInsightYear] = useState('2024');
  const [insightData, setInsightData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [modalType, setModalType] = useState(null);

  // Sync Calendar
  useEffect(() => {
    const fetchCalendar = async () => {
      if (predYear === 'default') {
        setRaceOptions([]);
        setPredRound('default');
        return;
      }
      setIsSyncingCalendar(true);
      try {
        const res = await fetch(`${API_BASE}/schedule/${predYear}`);
        const races = await res.json();
        setRaceOptions(races);
        if (races.length > 0) setPredRound(races[0].round.toString());
      } catch (err) {
        setPredictionError("Failed to sync with F1 Calendar.");
      } finally {
        setIsSyncingCalendar(false);
      }
    };
    fetchCalendar();
  }, [predYear]);

  const handleRunInference = async () => {
    setIsPredicting(true);
    setPredictionError(null);
    let url = `${API_BASE}/predict`;
    if (predYear !== 'default' && predRound !== 'default') {
      url += `?year=${predYear}&round_num=${predRound}`;
    }
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setPredictionData(data);
    } catch (err) {
      setPredictionError(err.message);
    } finally {
      setIsPredicting(false);
    }
  };

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE}/insights/${insightYear}`);
      const data = await res.json();
      setInsightData(data);
    } catch (err) { console.error(err); } finally { setIsAnalyzing(false); }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans">
      {/* NAVBAR */}
      <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-red-600 p-2 rounded-lg">
              <ZapIcon />
            </div>
            <h1 className="text-2xl font-black tracking-tighter uppercase">F1 <span className="text-red-600">Hub</span></h1>
          </div>
          <div className="flex bg-gray-800 rounded-xl p-1">
            <button 
              onClick={() => setActiveTab('predictions')}
              className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'predictions' ? 'bg-red-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
            >
              AI Predictions
            </button>
            <button 
              onClick={() => setActiveTab('analytics')}
              className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'analytics' ? 'bg-red-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
            >
              Data Analytics
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto p-6 md:p-10">
        {activeTab === 'predictions' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in duration-700">
            {/* LEFT: ENGINE */}
            <div className="lg:col-span-2 space-y-8">
              <section className="bg-gray-900 p-8 rounded-3xl border border-gray-800 shadow-2xl relative">
                <div className="absolute top-0 left-0 w-32 h-1 bg-red-600"></div>
                <h2 className="text-3xl font-bold mb-8 tracking-tight">Race Inference Engine</h2>
                
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest ml-1">Season</label>
                    <select value={predYear} onChange={(e) => setPredYear(e.target.value)} className="w-full bg-gray-800 border-none rounded-xl p-4 text-sm focus:ring-2 focus:ring-red-600 outline-none">
                      <option value="default">Last Completed</option>
                      {[2024, 2023, 2022, 2021, 2020, 2019, 2018].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest ml-1">Event</label>
                    <select value={predRound} onChange={(e) => setPredRound(e.target.value)} disabled={isSyncingCalendar || predYear === 'default'} className="w-full bg-gray-800 border-none rounded-xl p-4 text-sm focus:ring-2 focus:ring-red-600 outline-none disabled:opacity-30">
                      {isSyncingCalendar ? <option>Syncing...</option> : raceOptions.map(r => <option key={r.round} value={r.round}>{r.name}</option>)}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button onClick={handleRunInference} disabled={isPredicting} className="w-full bg-red-600 hover:bg-red-700 h-13 rounded-xl font-bold text-lg shadow-xl shadow-red-900/20 active:scale-95 transition-all">
                      {isPredicting ? 'Crunching...' : 'Predict Race'}
                    </button>
                  </div>
                </div>

                {predictionError && (
                  <div className="mb-6 p-4 bg-red-900/20 border border-red-500/50 rounded-xl text-red-400 text-sm">{predictionError}</div>
                )}

                {predictionData && (
                  <div className="space-y-6">
                    <div className="flex justify-between items-center border-b border-gray-800 pb-4">
                      <h3 className="text-xl font-bold text-white">{predictionData.race_name}</h3>
                      <div className="flex gap-2">
                        <span className="bg-gray-800 text-[9px] font-bold px-2 py-1 rounded">RANDOM_FOREST_V2</span>
                      </div>
                    </div>
                    <div className="overflow-hidden rounded-2xl border border-gray-800">
                      <table className="w-full text-left">
                        <thead className="bg-gray-800/50 text-gray-500 text-[10px] font-black uppercase">
                          <tr>
                            <th className="px-6 py-4">Pred</th>
                            <th className="px-6 py-4">Driver</th>
                            <th className="px-6 py-4">Grid</th>
                            <th className="px-6 py-4">Actual</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                          {predictionData.predictions.slice(0, 10).map((p) => (
                            <tr key={p.Abbreviation} className="hover:bg-gray-800/30 transition">
                              <td className="px-6 py-4 font-black text-red-500">P{p.PredictedRank}</td>
                              <td className="px-6 py-4">
                                <p className="font-bold text-white">{p.FullName}</p>
                                <p className="text-[10px] text-gray-500">{p.TeamName}</p>
                              </td>
                              <td className="px-6 py-4 font-mono text-gray-400">{p.GridPosition || 'Pit'}</td>
                              <td className={`px-6 py-4 font-black ${p.ActualPosition === p.PredictedRank ? 'text-green-500' : 'text-gray-600'}`}>
                                {p.ActualPosition || 'DNF'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </section>

              {/* SEASON INSIGHTS PANEL */}
              <section className="bg-gray-900 p-8 rounded-3xl border border-gray-800">
                <div className="flex justify-between items-center mb-8">
                  <h2 className="text-2xl font-bold">Season Diagnostics</h2>
                  <div className="flex gap-2">
                    <select value={insightYear} onChange={(e) => setInsightYear(e.target.value)} className="bg-gray-800 border-none rounded-lg text-xs p-2 outline-none">
                      {[2024, 2023, 2022, 2021, 2020, 2019, 2018].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                    <button onClick={handleRunAnalysis} className="bg-blue-600 px-4 py-2 rounded-lg text-xs font-bold">Analyze</button>
                  </div>
                </div>
                {insightData ? (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    <div onClick={() => setModalType('champion')} className="bg-gray-800 p-4 rounded-2xl cursor-pointer hover:border-red-600 border border-transparent transition">
                      <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">Champ</p>
                      <p className="text-lg font-bold truncate text-white">{insightData.champion.name}</p>
                    </div>
                    <div onClick={() => setModalType('pole_rate')} className="bg-gray-800 p-4 rounded-2xl cursor-pointer hover:border-red-600 border border-transparent transition">
                      <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">Pole Conv.</p>
                      <p className="text-lg font-bold text-green-400">{insightData.pole_rate.value}%</p>
                    </div>
                    <div onClick={() => setModalType('overtake')} className="bg-gray-800 p-4 rounded-2xl cursor-pointer hover:border-red-600 border border-transparent transition">
                      <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">Overtake King</p>
                      <p className="text-lg font-bold text-white">{insightData.overtake.driver}</p>
                    </div>
                    <div onClick={() => setModalType('reliability')} className="bg-gray-800 p-4 rounded-2xl cursor-pointer hover:border-red-600 border border-transparent transition">
                      <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">DNF Rate</p>
                      <p className="text-lg font-bold text-orange-400">{insightData.reliability.value}%</p>
                    </div>
                    <div onClick={() => setModalType('consistency')} className="bg-gray-800 p-4 rounded-2xl cursor-pointer hover:border-red-600 border border-transparent transition">
                      <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">Consistency</p>
                      <p className="text-lg font-bold text-white">{insightData.consistency.driver}</p>
                    </div>
                    <div onClick={() => setModalType('weather')} className="bg-gray-800 p-4 rounded-2xl cursor-pointer hover:border-red-600 border border-transparent transition">
                      <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">Avg Temp</p>
                      <p className="text-lg font-bold text-blue-300">{insightData.weather.avg_temp}°C</p>
                    </div>
                  </div>
                ) : <p className="text-gray-600 text-sm italic">Select a season to load performance analytics...</p>}
              </section>
            </div>

            {/* RIGHT: DATA SCIENCE SPECS */}
            <aside className="space-y-6">
              <div className="bg-gray-900 p-6 rounded-3xl border border-gray-800">
                <h3 className="text-xs font-black text-gray-500 uppercase tracking-widest mb-6">Model Intelligence</h3>
                <div className="grid grid-cols-2 gap-4 mb-8">
                  <div className="bg-black/30 p-4 rounded-2xl border border-gray-800">
                    <p className="text-[9px] font-black text-gray-500 uppercase">R² Accuracy</p>
                    <p className="text-2xl font-bold text-green-500">0.44</p>
                  </div>
                  <div className="bg-black/30 p-4 rounded-2xl border border-gray-800">
                    <p className="text-[9px] font-black text-gray-500 uppercase">MAE Error</p>
                    <p className="text-2xl font-bold text-blue-500">3.37</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <p className="text-[10px] font-bold text-gray-400 uppercase">Feature Weighting</p>
                  {[
                    { l: 'Grid Position', w: 55.7, c: 'bg-red-600' },
                    { l: 'Constructor Form', w: 10.4, c: 'bg-blue-600' },
                    { l: 'Track Temp', w: 9.0, c: 'bg-orange-600' },
                    { l: 'Driver Form', w: 7.5, c: 'bg-purple-600' }
                  ].map(f => (
                    <div key={f.l}>
                      <div className="flex justify-between text-[10px] mb-1 font-bold">
                        <span className="text-gray-500">{f.l}</span>
                        <span>{f.w}%</span>
                      </div>
                      <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                        <div className={`${f.c} h-full`} style={{ width: `${f.w}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-blue-900/10 p-6 rounded-3xl border border-blue-800/30">
                <p className="text-[11px] leading-relaxed text-blue-300 italic">
                  "This project utilizes a Random Forest Regressor trained on 3,000+ race entries. By transforming static driver IDs into dynamic 'Form' vectors, the model adapts to mid-season updates."
                </p>
              </div>
            </aside>
          </div>
        ) : (
          /* ANALYTICS TAB: STREAMLIT IFRAME */
          <div className="animate-in slide-in-from-bottom-8 duration-700">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold tracking-tight">Advanced Performance Dashboard</h2>
                <p className="text-gray-500 mt-1">Deep-dive visual analysis powered by Streamlit & Plotly</p>
              </div>
              <div className="bg-green-600/10 text-green-500 text-[10px] font-black px-3 py-1 rounded-full border border-green-500/20">
                LIVE TELEMETRY ANALYSIS
              </div>
            </div>
            <div className="w-full h-[85vh] rounded-3xl overflow-hidden border border-gray-800 shadow-2xl bg-gray-900 relative">
              <iframe 
                src="http://localhost:8501" 
                className="w-full h-full border-none"
                title="F1 Analytics Dashboard"
              />
              {/* Overlay for unauthorized access or styling if needed */}
            </div>
          </div>
        )}
      </main>

      {/* MODAL */}
      {modalType && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setModalType(null)}>
          <div className="bg-gray-900 border border-gray-800 max-w-md w-full rounded-3xl p-8 shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-2xl font-bold text-red-600 mb-4 uppercase italic tracking-tighter border-b border-gray-800 pb-2">{modalType.replace('_', ' ')} Insight</h3>
            <div className="mt-4 mb-8">
               <p className="text-gray-400 text-xs font-black uppercase tracking-widest mb-2">Analysis & Logic:</p>
               <p className="text-gray-300 text-lg leading-relaxed">{insightData[modalType]?.detail}</p>
            </div>
            <button onClick={() => setModalType(null)} className="w-full bg-gray-800 hover:bg-gray-700 py-4 rounded-xl font-bold text-sm transition-colors">Dismiss</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;