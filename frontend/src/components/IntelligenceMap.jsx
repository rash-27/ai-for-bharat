import { useState, useEffect } from 'react';
import { searchBusinesses, getUbidDetails } from '../api';
import { Search, Clock, Box, Building2, Zap, AlertTriangle } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const SILO_STYLES = {
  labour:  { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300', dot: 'bg-orange-500' },
  bescom:  { bg: 'bg-blue-100',   text: 'text-blue-700',   border: 'border-blue-300',   dot: 'bg-blue-500' },
  kspcb:   { bg: 'bg-emerald-100',text: 'text-emerald-700',border: 'border-emerald-300',dot: 'bg-emerald-500' },
  unknown: { bg: 'bg-gray-100',   text: 'text-gray-700',   border: 'border-gray-300',   dot: 'bg-gray-500' },
};

function getSiloStyle(source) {
  return SILO_STYLES[source?.toLowerCase()] || SILO_STYLES.unknown;
}

function formatDate(iso) {
  if (!iso) return 'N/A';
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function AgeLabel({ ageMonths, isDeciding, status }) {
  if (isDeciding) {
    if (status === 'ACTIVE') {
      return (
        <p className="text-xs text-green-700 mt-1">
          ⚡ Most recent activity — rescued the entire cluster to <strong>ACTIVE</strong>
        </p>
      );
    }
    return (
      <p className="text-xs text-red-600 mt-1">
        ⚠️ Most recent activity across the cluster — {ageMonths.toFixed(0)}+ months ago — cluster is <strong>DORMANT</strong>
      </p>
    );
  }
  return (
    <p className="text-xs text-gray-400 mt-1">
      Stale by itself ({ageMonths.toFixed(0)} months ago) — rescued by a more recent cluster event
    </p>
  );
}

export default function IntelligenceMap() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [selectedUbid, setSelectedUbid] = useState(null);
  const [ubidData, setUbidData] = useState(null);
  const [loading, setLoading] = useState(false);
  const location = useLocation();

  useEffect(() => {
    if (location.state?.ubid) {
      handleSelectUbid(location.state.ubid);
    }
  }, [location]);

  useEffect(() => {
    if (query.length > 2) {
      const delayDebounce = setTimeout(() => {
        searchBusinesses(query).then(setResults).catch(console.error);
      }, 300);
      return () => clearTimeout(delayDebounce);
    } else {
      setResults([]);
    }
  }, [query]);

  const handleSelectUbid = async (ubid) => {
    setQuery('');
    setResults([]);
    setSelectedUbid(ubid);
    setLoading(true);
    try {
      const data = await getUbidDetails(ubid);
      setUbidData(data);
    } catch (e) {
      console.error(e);
      setUbidData(null);
    }
    setLoading(false);
  };

  return (
    <div className="p-8 max-w-6xl mx-auto min-h-screen">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4 text-gray-800">Intelligence Search</h1>
        <p className="text-gray-500">Search across millions of records seamlessly via Algolia.</p>

        <div className="mt-8 relative max-w-2xl mx-auto">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search by Company Name (e.g. Rao Textiles)..."
              className="w-full pl-12 pr-4 py-4 rounded-full border border-gray-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          {results.length > 0 && (
            <div className="absolute w-full mt-2 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden z-10 text-left">
              {results.map((hit) => (
                <div
                  key={hit.objectID}
                  onClick={() => handleSelectUbid(hit.assigned_ubid)}
                  className="px-6 py-4 hover:bg-gray-50 cursor-pointer border-b border-gray-50 last:border-0"
                >
                  <p className="font-semibold text-gray-800">{hit.company_name}</p>
                  <div className="flex justify-between items-center mt-1">
                    <p className="text-sm text-gray-500">{hit.assigned_ubid}</p>
                    <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded-full">{hit.status || 'UNKNOWN'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {loading && <div className="text-center text-gray-500 mt-12">Loading Graph Data...</div>}

      {ubidData && !loading && (
        <div className="bg-white rounded-3xl shadow-sm border border-gray-200 overflow-hidden mt-8">
          {/* Header */}
          <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-8 text-white relative">
            <div className="absolute top-8 right-8">
              <span className={`px-4 py-2 rounded-full text-sm font-bold tracking-wider ${
                ubidData.status === 'ACTIVE'
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                  : 'bg-red-500/20 text-red-400 border border-red-500/30'
              }`}>
                STATUS: {ubidData.status}
              </span>
            </div>
            <h2 className="text-3xl font-bold mb-2">{ubidData.company_name}</h2>
            <div className="flex items-center space-x-4 text-slate-300">
              <span className="flex items-center"><Box size={16} className="mr-2" /> {ubidData.ubid}</span>
              <span className="flex items-center">
                <Clock size={16} className="mr-2" />
                Last Event: {ubidData.latest_event_date ? formatDate(ubidData.latest_event_date) : 'N/A'}
              </span>
            </div>
          </div>

          {/* Source Record Cards */}
          <div className="p-8 bg-slate-50 border-b border-gray-200">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center">
              <Building2 className="mr-2" /> Connected Source Records
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {ubidData.nodes.map((node, i) => {
                const style = getSiloStyle(node.source_system);
                return (
                  <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <span className={`text-xs font-bold uppercase tracking-wider px-2 py-1 rounded ${style.bg} ${style.text}`}>
                        {node.source_system}
                      </span>
                    </div>
                    <p className="font-semibold text-gray-800 mb-1">{node.company_name}</p>
                    <p className="text-sm text-gray-500 mb-4">{node.address}</p>
                    <div className="pt-4 border-t border-gray-100 flex justify-between items-center text-sm">
                      <span className="text-gray-400">ID: {node.id.split('_')[1]?.substring(0, 8)}...</span>
                      {node.pan_number && <span className="text-gray-600 font-medium">PAN: {node.pan_number}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Kafka Event Timeline */}
          {ubidData.event_timeline && ubidData.event_timeline.length > 0 && (
            <div className="p-8">
              <h3 className="text-lg font-bold text-gray-800 mb-2 flex items-center">
                <Zap className="mr-2 text-yellow-500" size={20} />
                Activity Timeline
                <span className="ml-3 text-xs font-normal text-gray-400 uppercase tracking-wider">Kafka Events · Newest First</span>
              </h3>
              <p className="text-sm text-gray-500 mb-8">
                The system scans all events across every connected source record. A single recent event keeps the entire UBID cluster <strong>ACTIVE</strong>.
              </p>

              <div className="relative">
                {/* Vertical connector line */}
                <div className="absolute left-5 top-2 bottom-2 w-0.5 bg-gray-200" />

                <div className="space-y-6">
                  {ubidData.event_timeline.map((event, idx) => {
                    const style = getSiloStyle(event.source_system);
                    const isDeciding = event.is_deciding_event;
                    return (
                      <div key={idx} className="relative flex items-start gap-6">
                        {/* Timeline dot */}
                        <div className={`relative z-10 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                          isDeciding
                            ? 'bg-yellow-400 border-yellow-500 shadow-lg shadow-yellow-200'
                            : `${style.bg} ${style.border}`
                        }`}>
                          {isDeciding
                            ? <Zap size={16} className="text-white" />
                            : <Clock size={14} className={style.text} />
                          }
                        </div>

                        {/* Event card */}
                        <div className={`flex-1 rounded-2xl border p-5 transition-all ${
                          isDeciding
                            ? 'bg-yellow-50 border-yellow-300 shadow-sm'
                            : 'bg-white border-gray-200'
                        }`}>
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${style.bg} ${style.text}`}>
                                {event.source_system}
                              </span>
                              {isDeciding && (
                                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-yellow-400 text-yellow-900">
                                  ⚡ Deciding Event
                                </span>
                              )}
                            </div>
                            <span className="text-sm font-semibold text-gray-700">{formatDate(event.event_date)}</span>
                          </div>
                          <p className="text-gray-800 font-medium mt-1">{event.company_name}</p>
                          <AgeLabel
                            ageMonths={event.age_months}
                            isDeciding={isDeciding}
                            status={ubidData.status}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Bottom verdict */}
                <div className={`mt-8 ml-16 rounded-2xl p-5 border flex items-center gap-4 ${
                  ubidData.status === 'ACTIVE'
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                }`}>
                  {ubidData.status === 'ACTIVE'
                    ? <Zap size={24} className="text-green-600 flex-shrink-0" />
                    : <AlertTriangle size={24} className="text-red-500 flex-shrink-0" />
                  }
                  <div>
                    <p className={`font-bold text-sm ${ubidData.status === 'ACTIVE' ? 'text-green-800' : 'text-red-800'}`}>
                      Verdict: UBID Cluster is {ubidData.status}
                    </p>
                    <p className={`text-xs mt-0.5 ${ubidData.status === 'ACTIVE' ? 'text-green-600' : 'text-red-600'}`}>
                      {ubidData.status === 'ACTIVE'
                        ? `The most recent event across all ${ubidData.event_timeline.length} source record(s) is within 18 months — cluster is alive.`
                        : `No activity across any of the ${ubidData.event_timeline.length} source record(s) in the last 18 months — cluster is dormant.`
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
