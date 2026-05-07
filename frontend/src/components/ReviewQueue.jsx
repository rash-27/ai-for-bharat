import { useEffect, useState } from 'react';
import { getPendingReviews, resolveReview } from '../api';
import { Check, X } from 'lucide-react';

export default function ReviewQueue() {
  const [reviews, setReviews] = useState([]);

  const fetchReviews = () => {
    getPendingReviews().then(setReviews).catch(console.error);
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const handleDecision = async (nodeA, nodeB, decision, score) => {
    // Basic features approximation for active learning logging
    const features = [score, score, 0, 0]; 
    await resolveReview(nodeA.id, nodeB.id, decision, features);
    fetchReviews(); // Refresh the list
  };

  if (reviews.length === 0) {
    return (
      <div className="p-8 flex flex-col items-center justify-center h-64">
        <div className="w-16 h-16 bg-green-100 text-green-500 rounded-full flex items-center justify-center mb-4">
          <Check size={32} />
        </div>
        <h2 className="text-xl font-medium text-gray-700">All caught up!</h2>
        <p className="text-gray-500">There are no pending reviews at the moment.</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-2 text-gray-800">Resolution Queue</h1>
      <p className="text-gray-500 mb-8">Review ambiguous matches predicted by the AI engine.</p>
      
      <div className="space-y-8">
        {reviews.map((review, idx) => (
          <div key={idx} className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-6 py-3 border-b border-gray-200 flex justify-between items-center">
              <span className="text-sm font-medium text-gray-600">Match Confidence: <span className="text-orange-500 font-bold">{(review.score * 100).toFixed(1)}%</span></span>
              <div className="space-x-3">
                <button 
                  onClick={() => handleDecision(review.node_a, review.node_b, 'REJECT', review.score)}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Keep Separate
                </button>
                <button 
                  onClick={() => handleDecision(review.node_a, review.node_b, 'MERGE', review.score)}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600 shadow-sm transition-colors"
                >
                  Approve Merge
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 divide-x divide-gray-200">
              <RecordCard record={review.node_a} title="Primary Record" />
              <RecordCard record={review.node_b} title="Candidate Record" compareWith={review.node_a} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RecordCard({ record, title, compareWith }) {
  const isMatch = (key) => {
    if (!compareWith) return true;
    return record[key] === compareWith[key];
  };

  return (
    <div className="p-6">
      <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-4">{title} ({record.source_system})</h3>
      <div className="space-y-4">
        <div>
          <p className="text-xs text-gray-500">Company Name</p>
          <p className={`font-medium ${!isMatch('company_name') ? 'text-red-500' : 'text-gray-900'}`}>{record.company_name}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Address</p>
          <p className={`text-sm ${!isMatch('address') ? 'text-orange-500' : 'text-gray-700'}`}>{record.address}</p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500">PIN Code</p>
            <p className="text-sm font-medium text-gray-900">{record.pin_code}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">PAN Number</p>
            {record.pan_number ? (
               <p className={`text-sm font-medium ${!isMatch('pan_number') ? 'text-red-500' : 'text-gray-900'}`}>{record.pan_number}</p>
            ) : (
               <p className="text-sm font-medium text-red-400 italic">Missing</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
