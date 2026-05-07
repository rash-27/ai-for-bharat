import { useState, useEffect } from 'react';
import { searchBusinesses, getUbidDetails } from '../api';
import { Search, Activity, Clock, Box, Building2 } from 'lucide-react';
import { useLocation } from 'react-router-dom';

export default function IntelligenceMap() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [selectedUbid, setSelectedUbid] = useState(null);
  const [ubidData, setUbidData] = useState(null);
  const [loading, setLoading] = useState(false);
  const location = useLocation();

  useEffect(() => {
    // If navigated with a pre-selected UBID
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
        <p className="text-gray-500">Search across millions of records seamlessly via Elastic.</p>
        
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
          <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-8 text-white relative">
            <div className="absolute top-8 right-8">
              <span className={`px-4 py-2 rounded-full text-sm font-bold tracking-wider ${
                ubidData.status === 'ACTIVE' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 
                'bg-red-500/20 text-red-400 border border-red-500/30'
              }`}>
                STATUS: {ubidData.status}
              </span>
            </div>
            <h2 className="text-3xl font-bold mb-2">{ubidData.company_name}</h2>
            <div className="flex items-center space-x-4 text-slate-300">
              <span className="flex items-center"><Box size={16} className="mr-2" /> {ubidData.ubid}</span>
              <span className="flex items-center"><Clock size={16} className="mr-2" /> Last Event: {ubidData.latest_event_date ? new Date(ubidData.latest_event_date).toLocaleDateString() : 'N/A'}</span>
            </div>
          </div>
          
          <div className="p-8 bg-slate-50">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center"><Building2 className="mr-2" /> Connected Source Records</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {ubidData.nodes.map((node, i) => (
                <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-bold uppercase tracking-wider text-blue-500 bg-blue-50 px-2 py-1 rounded">{node.source_system}</span>
                  </div>
                  <p className="font-semibold text-gray-800 mb-1">{node.company_name}</p>
                  <p className="text-sm text-gray-500 mb-4">{node.address}</p>
                  <div className="pt-4 border-t border-gray-100 flex justify-between items-center text-sm">
                    <span className="text-gray-400">ID: {node.id.split('_')[1]?.substring(0,8)}...</span>
                    {node.pan_number && <span className="text-gray-600 font-medium">PAN: {node.pan_number}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
