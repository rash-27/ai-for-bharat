import { useEffect, useState } from 'react';
import { getDashboardStats } from '../api';
import { Database, Link, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const [stats, setStats] = useState({ total_records: 0, total_ubids: 0, pending_reviews: 0 });
  const navigate = useNavigate();

  useEffect(() => {
    getDashboardStats().then(setStats).catch(console.error);
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">Executive Overview</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-4 bg-blue-50 rounded-full text-blue-500">
            <Database size={32} />
          </div>
          <div>
            <p className="text-gray-500 text-sm font-medium">Siloed Records Ingested</p>
            <p className="text-3xl font-bold text-gray-800">{stats.total_records.toLocaleString()}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-4 bg-green-50 rounded-full text-green-500">
            <Link size={32} />
          </div>
          <div>
            <p className="text-gray-500 text-sm font-medium">Unique UBIDs Generated</p>
            <p className="text-3xl font-bold text-gray-800">{stats.total_ubids.toLocaleString()}</p>
          </div>
        </div>

        <div 
          onClick={() => navigate('/reviews')}
          className={`p-6 rounded-2xl shadow-sm border flex items-center space-x-4 cursor-pointer transition-all hover:-translate-y-1 ${
            stats.pending_reviews > 0 ? 'bg-red-50 border-red-200' : 'bg-white border-gray-100'
          }`}
        >
          <div className={`p-4 rounded-full ${stats.pending_reviews > 0 ? 'bg-red-100 text-red-500' : 'bg-gray-50 text-gray-400'}`}>
            <AlertTriangle size={32} />
          </div>
          <div>
            <p className={`text-sm font-medium ${stats.pending_reviews > 0 ? 'text-red-500' : 'text-gray-500'}`}>Pending Manual Reviews</p>
            <p className={`text-3xl font-bold ${stats.pending_reviews > 0 ? 'text-red-600' : 'text-gray-800'}`}>
              {stats.pending_reviews.toLocaleString()}
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
