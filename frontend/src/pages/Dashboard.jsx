import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { logout } from '../endpoint/userendpoint';

function Dashboard() {
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    try {
      setIsLoggingOut(true);
      
      // Try to call the logout endpoint
      await logout();
      console.log('✅ Logout successful');
      
    } catch (error) {
      // If logout fails due to token issues (403), we still proceed
      console.warn('⚠️ Logout API call failed:', error);
      
      // Check if it's a token validation error
      if (error.response?.status === 403 || error.response?.data?.code === 'token_not_valid') {
        console.log('Token invalid, proceeding with local logout');
      }
    } finally {
      // Always clear local storage and navigate, regardless of API success
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      localStorage.removeItem('user');
      
      console.log('🧹 Cleared all tokens and user data');
      
      setIsLoggingOut(false);
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
          <button 
            onClick={handleLogout}
            disabled={isLoggingOut}
            className={`px-6 py-2.5 rounded-lg font-semibold transition-all transform ${
              isLoggingOut
                ? 'bg-gray-400 cursor-not-allowed opacity-60'
                : 'bg-red-600 hover:bg-red-700 text-white hover:scale-105 active:scale-95'
            }`}
          >
            {isLoggingOut ? (
              <span className="flex items-center">
                <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Logging out...
              </span>
            ) : (
              'Logout'
            )}
          </button>
        </div>

        <div className="mt-8 bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-700 mb-4">Welcome back!</h2>
          <p className="text-gray-600">Your dashboard content goes here.</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;