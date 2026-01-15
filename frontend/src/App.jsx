import React, { useState, useEffect } from 'react';

// --- Icons (Inline SVGs for reliability) ---
const ZapIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

const InfoIcon = () => (
  <svg className="w-5 h-5 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
  </svg>
);

const App = () => {
  const API_BASE = 'http://127.0.0.1:8000';
  
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

  // --- Effect: Sync Calendar when Year changes ---
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
        if (!res.ok) throw new Error("Sync Failed");
        const races = await res.json();
        setRaceOptions(races);
        // Default to the first race if none selected
        if (races.length > 0) setPredRound(races[0].round.toString());
      } catch (err) {
        setPredictionError("Failed to load race calendar.");
      } finally {
        setIsSyncingCalendar(false);
      }
    };

    fetchCalendar();
  }, [predYear]);

  // --- Handlers ---
  const handleRunInference = async () => {
    setIsPredicting(true);
    setPredictionError(null);
    setPredictionData(null);

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
    setInsightData(null);
    try {
      const res = await fetch(`${API_BASE}/insights/${insightYear}`);
      if (!res.ok) throw new Error("Analysis failed");
      const data = await res.json();
      setInsightData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-4 md:p-8 font-sans selection:bg-red-500/30">
      <div className="max-w-6xl mx-auto space-y-12">
        
        {/* HEADER */}
        <header className="text-center border-b border-gray-800 pb-8">
          <h1 className="text-5xl font-extrabold text-red-600 tracking-tighter mb-2">
            F1 <span className="text-white underline decoration-red-600/30">Analytics Hub</span>
          </h1>
          <p className="text-gray-400 text-lg font-light">Predictive Modeling & Statistical Analysis for Professional Motorsports</p>
          <div className="flex justify-center gap-3 mt-6">
            {['Random Forest', 'FastAPI', 'Telemetry'].map(tag => (
              <span key={tag} className="bg-gray-800 text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-md border border-gray-700 text-gray-400">
                {tag}
              </span>
            ))}
          </div>
        </header>

        {/* MAIN LAYOUT */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* LEFT: PREDICTION ENGINE */}
          <div className="lg:col-span-2 space-y-8">
            <section className="bg-gray-800 p-6 md:p-8 rounded-3xl shadow-2xl border border-gray-700 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-linear-to-r from-red-600 to-transparent"></div>
              
              <h2 className="text-2xl font-bold mb-8 flex items-center">
                <span className="bg-red-600 w-1.5 h-6 mr-3 rounded-full"></span> 
                Predictive Analysis
              </h2>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <div className="flex flex-col">
                  <label className="text-[10px] font-black text-gray-500 mb-1.5 uppercase tracking-wider ml-1">Season</label>
                  <select 
                    value={predYear}
                    onChange={(e) => setPredYear(e.target.value)}
                    disabled={isPredicting}
                    className="bg-gray-900 text-white border border-gray-700 rounded-xl px-4 py-3 focus:ring-2 focus:ring-red-600 outline-none transition-all disabled:opacity-50 appearance-none bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27white%27 stroke-width=%272%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3e%3cpolyline points=%276 9 12 15 18 9%27%3e%3c/polyline%3e%3c/svg%3e')] bg-no-repeat bg-position-[right_1rem_center] bg-size-[1em]"
                  >
                    <option value="default">Last Completed</option>
                    {[2024, 2023, 2022, 2021, 2020, 2019, 2018].map(y => (
                      <option key={y} value={y}>{y} Season</option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col">
                  <label className="text-[10px] font-black text-gray-500 mb-1.5 uppercase tracking-wider ml-1">Event</label>
                  <select 
                    value={predRound}
                    onChange={(e) => setPredRound(e.target.value)}
                    disabled={isSyncingCalendar || isPredicting || predYear === 'default'}
                    className="bg-gray-900 text-white border border-gray-700 rounded-xl px-4 py-3 focus:ring-2 focus:ring-red-600 outline-none transition-all disabled:opacity-30 appearance-none bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27white%27 stroke-width=%272%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3e%3cpolyline points=%276 9 12 15 18 9%27%3e%3c/polyline%3e%3c/svg%3e')] bg-no-repeat bg-position-[right_1rem_center] bg-size-[1em]"
                  >
                    {isSyncingCalendar ? (
                      <option>Syncing Calendar...</option>
                    ) : predYear === 'default' ? (
                      <option value="default">Auto-Detect</option>
                    ) : (
                      raceOptions.map(r => (
                        <option key={r.round} value={r.round}>{r.name}</option>
                      ))
                    )}
                  </select>
                </div>

                <div className="flex flex-col justify-end">
                  <button 
                    onClick={handleRunInference}
                    disabled={isPredicting || (predYear !== 'default' && raceOptions.length === 0)}
                    className="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-xl transition duration-300 transform active:scale-95 shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <span>{isPredicting ? 'Inference Active...' : 'Run Inference'}</span>
                    {!isPredicting && <ZapIcon />}
                  </button>
                </div>
              </div>

              {predictionError && (
                <div className="mb-6 p-4 bg-red-900/30 border border-red-500/50 rounded-xl text-red-200 text-sm flex items-start gap-3 animate-pulse">
                  <InfoIcon />
                  <span>{predictionError}</span>
                </div>
              )}

              {isPredicting && (
                <div className="py-12 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-600 mx-auto"></div>
                  <p className="text-gray-500 text-[10px] font-bold uppercase mt-6 tracking-[0.3em]">Calculating Form & Telemetry</p>
                </div>
              )}

              {predictionData && (
                <div className="animate-in fade-in duration-500">
                  <div className="flex justify-between items-end mb-4 px-1">
                    <h3 className="text-xl font-bold text-white">{predictionData.race_name}</h3>
                    <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Model Prediction</span>
                  </div>
                  <div className="overflow-x-auto rounded-2xl border border-gray-700 bg-gray-900/50">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-gray-800/50 text-gray-400 text-[10px] uppercase font-black">
                        <tr>
                          <th className="px-6 py-4">Rank</th>
                          <th class="px-6 py-4">Driver</th>
                          <th className="px-6 py-4">Constructor</th>
                          <th className="px-6 py-4">Grid</th>
                          <th className="px-6 py-4">Actual</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-800">
                        {predictionData.predictions.map((p) => (
                          <tr key={p.Abbreviation} className="hover:bg-gray-800/50 transition duration-150">
                            <td className="px-6 py-4 font-black text-gray-100">#{p.PredictedRank}</td>
                            <td className="px-6 py-4 font-semibold text-white">{p.FullName}</td>
                            <td className="px-6 py-4 text-gray-500 font-medium">{p.TeamName}</td>
                            <td className="px-6 py-4 text-gray-400 font-mono">{p.GridPosition || 'Pit'}</td>
                            <td className={`px-6 py-4 font-black ${p.ActualPosition === p.PredictedRank ? 'text-green-500' : 'text-gray-400'}`}>
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

            {/* SEASON INSIGHTS */}
            <section className="bg-gray-800 p-6 md:p-8 rounded-3xl shadow-xl border border-gray-700">
              <h2 className="text-2xl font-bold mb-8 flex items-center">
                <span className="bg-blue-600 w-1.5 h-6 mr-3 rounded-full"></span> Season Diagnostics
              </h2>

              <div className="flex flex-wrap gap-4 mb-8">
                <select 
                  value={insightYear}
                  onChange={(e) => setInsightYear(e.target.value)}
                  className="bg-gray-900 text-white border border-gray-700 rounded-xl px-6 py-3 focus:ring-2 focus:ring-blue-600 outline-none transition-all appearance-none bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27white%27 stroke-width=%272%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3e%3cpolyline points=%276 9 12 15 18 9%27%3e%3c/polyline%3e%3c/svg%3e')] bg-no-repeat bg-position-[right_1rem_center] bg-size-[1em] pr-12"
                >
                  {[2024, 2023, 2022, 2021, 2020, 2019, 2018].map(y => (
                    <option key={y} value={y}>{y} Season</option>
                  ))}
                </select>
                <button 
                  onClick={handleRunAnalysis}
                  disabled={isAnalyzing}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-xl transition duration-300 disabled:opacity-50"
                >
                  {isAnalyzing ? 'Analyzing Data...' : 'Analyze Year'}
                </button>
              </div>

              {insightData && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-in slide-in-from-bottom-4 duration-500">
                  {[
                    { id: 'champion', label: 'Champion', value: insightData.champion.name, color: 'text-white' },
                    { id: 'pole_rate', label: 'Pole Conv.', value: `${insightData.pole_rate.value}%`, color: 'text-green-400' },
                    { id: 'overtake', label: 'Overtake King', value: insightData.overtake.driver, color: 'text-white' },
                    { id: 'reliability', label: 'Reliability', value: `${insightData.reliability.value}%`, color: 'text-orange-400' },
                    { id: 'consistency', label: 'Consistency', value: insightData.consistency.driver, color: 'text-white' },
                    { id: 'weather', label: 'Avg Climate', value: `${insightData.weather.avg_temp} °C`, color: 'text-blue-300' }
                  ].map(stat => (
                    <div 
                      key={stat.id}
                      onClick={() => setModalType(stat.id)}
                      className="bg-gray-900/40 p-5 rounded-2xl border border-gray-700 transition-all duration-300 hover:-translate-y-1 hover:cursor-pointer hover:border-red-600 group"
                    >
                      <p className="text-gray-500 text-[10px] font-black uppercase tracking-widest mb-1 group-hover:text-red-400">{stat.label}</p>
                      <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>

          {/* RIGHT: MODEL INTELLIGENCE */}
          <div className="space-y-8">
            <section className="bg-gray-800 p-6 rounded-3xl shadow-xl border border-gray-700 h-full">
              <h2 className="text-xl font-bold mb-6 flex items-center">
                <span className="bg-green-600 w-1.5 h-6 mr-3 rounded-full"></span> Data Science Specs
              </h2>
              
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-900 p-4 rounded-2xl border border-gray-700 text-center">
                    <p className="text-gray-500 text-[10px] uppercase font-black tracking-widest">R² Score</p>
                    <p className="text-2xl font-bold text-green-500">0.44</p>
                    <p className="text-[9px] text-gray-500 mt-1 italic">Validation Metric</p>
                  </div>
                  <div className="bg-gray-900 p-4 rounded-2xl border border-gray-700 text-center">
                    <p className="text-gray-500 text-[10px] uppercase font-black tracking-widest">MAE</p>
                    <p className="text-2xl font-bold text-blue-500">3.37</p>
                    <p className="text-[9px] text-gray-500 mt-1 italic">Avg Pos Error</p>
                  </div>
                </div>

                <div className="pt-4">
                  <p className="text-xs font-black text-gray-400 mb-6 uppercase tracking-widest">Feature Weight Matrix</p>
                  <div className="space-y-5">
                    {[
                      { label: 'Grid Position', weight: 55.7, color: 'bg-red-600' },
                      { label: 'Constructor Form', weight: 10.4, color: 'bg-blue-600' },
                      { label: 'Track Temp', weight: 9.0, color: 'bg-orange-600' },
                      { label: 'Driver Form', weight: 7.5, color: 'bg-purple-600' }
                    ].map(feat => (
                      <div key={feat.label}>
                        <div className="flex justify-between text-[10px] font-bold mb-1.5 uppercase tracking-tighter">
                          <span className="text-gray-300">{feat.label}</span>
                          <span className={feat.color.replace('bg-', 'text-')}>{feat.weight}%</span>
                        </div>
                        <div className="w-full bg-gray-900 h-1.5 rounded-full overflow-hidden">
                          <div 
                            className={`${feat.color} h-full transition-all duration-1000 ease-out`} 
                            style={{ width: `${feat.weight}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-blue-900/10 p-4 rounded-2xl border border-blue-800/30">
                  <p className="text-[10px] leading-relaxed text-blue-300">
                    <strong>Architecture:</strong> Random Forest Regressor optimized via GridSearchCV. Model generalizes race outcomes by converting static IDs into dynamic rolling performance vectors.
                  </p>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>

      {/* MODAL */}
      {modalType && (
        <div 
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setModalType(null)}
        >
          <div 
            className="bg-gray-800 border border-gray-700 max-w-md w-full rounded-3xl p-8 shadow-2xl relative animate-in zoom-in-95 duration-200"
            onClick={e => e.stopPropagation()}
          >
            <button 
              onClick={() => setModalType(null)}
              className="absolute top-5 right-5 text-gray-500 hover:text-white transition text-2xl"
            >
              &times;
            </button>
            <h3 className="text-xl font-black text-red-600 mb-4 uppercase tracking-tighter">
              {modalType.replace('_', ' ')} Insight
            </h3>
            <p className="text-gray-300 leading-relaxed text-base mb-8">
              {insightData[modalType]?.detail || "Additional telemetry data is being cross-referenced for this specific metric."}
            </p>
            <button 
              onClick={() => setModalType(null)}
              className="w-full bg-gray-700 hover:bg-gray-600 py-3 rounded-xl font-bold transition text-sm"
            >
              Close Insight
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;