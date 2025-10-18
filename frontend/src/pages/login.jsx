import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../endpoint/userendpoint';

export default function Login() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState('');
  const [signInData, setSignInData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  const handleSignInChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSignInData({
      ...signInData,
      [name]: type === 'checkbox' ? checked : value
    });
    if (errors[name]) {
      setErrors({ ...errors, [name]: '' });
    }
  };

  const validateSignIn = () => {
    const newErrors = {};
    if (!signInData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(signInData.email)) {
      newErrors.email = 'Email is invalid';
    }
    if (!signInData.password) {
      newErrors.password = 'Password is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSignInSubmit = async () => {
    setSuccessMessage('');
    setErrors({});

    if (!validateSignIn()) {
      return;
    }

    setIsLoading(true);

    try {
      const loginPayload = {
        email: signInData.email,
        password: signInData.password
      };

      console.log('🔵 LOGIN: Sending request with:', loginPayload);
      const response = await login(loginPayload);
      console.log('🟢 LOGIN: Full response received:', response);

      // Extract data from Axios response
      const data = response.data || response;
      console.log('🟢 LOGIN: Data extracted:', data);

      // Validate response
      if (!data || !data.access) {
        console.error('❌ LOGIN: Invalid response - missing access token');
        console.error('Response data:', data);
        throw new Error('Invalid response from server');
      }

      if (!data.user) {
        console.error('❌ LOGIN: Invalid response - missing user data');
        throw new Error('Invalid response from server');
      }

      console.log('🔵 LOGIN: Storing in localStorage...');

      // ✅ FIXED: Use data.access, data.refresh, data.user instead of response.*
      localStorage.setItem('access', data.access);
      console.log('✅ Stored access_token:', data.access);

      localStorage.setItem('refresh', data.refresh);
      console.log('✅ Stored refresh_token:', data.refresh);

      const userStr = JSON.stringify(data.user);
      localStorage.setItem('user', userStr);
      console.log('✅ Stored user:', userStr);

      // Verify storage
      console.log('🔍 VERIFY: access =', localStorage.getItem('access'));
      console.log('🔍 VERIFY: refresh =', localStorage.getItem('refresh'));
      console.log('🔍 VERIFY: user =', localStorage.getItem('user'));

      setSuccessMessage('Login successful! Redirecting...');

      setTimeout(() => {
        console.log('🚀 LOGIN: Navigating to /dashboard');
        navigate('/dashboard');
      }, 1000);

    } catch (error) {
      console.error('❌ LOGIN ERROR:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.error ||
        error.message ||
        'Invalid email or password';
      setErrors({ submit: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterClick = () => {
    navigate('/register');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-6">
          <h2 className="text-3xl font-bold text-gray-800">Welcome Back</h2>
          <p className="text-gray-600 mt-2">Sign in to continue</p>
        </div>

        {successMessage && (
          <div className="mb-4 p-4 bg-green-50 border-l-4 border-green-500 text-green-700 rounded">
            <p className="font-medium">{successMessage}</p>
          </div>
        )}

        {errors.submit && (
          <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
            <p className="font-medium">{errors.submit}</p>
          </div>
        )}

        <div className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={signInData.email}
              onChange={handleSignInChange}
              className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all ${
                errors.email ? 'border-red-500 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="your.email@example.com"
            />
            {errors.email && (
              <p className="text-red-500 text-sm mt-1 flex items-center">
                <span className="mr-1">⚠️</span> {errors.email}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={signInData.password}
              onChange={handleSignInChange}
              className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all ${
                errors.password ? 'border-red-500 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="Enter your password"
            />
            {errors.password && (
              <p className="text-red-500 text-sm mt-1 flex items-center">
                <span className="mr-1">⚠️</span> {errors.password}
              </p>
            )}
          </div>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                name="rememberMe"
                checked={signInData.rememberMe}
                onChange={handleSignInChange}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-gray-600">Remember me</span>
            </label>
            <span className="text-blue-600 hover:text-blue-700 hover:underline cursor-pointer">
              Forgot password?
            </span>
          </div>

          <button
            onClick={handleSignInSubmit}
            disabled={isLoading}
            className={`w-full py-3 rounded-lg font-semibold transition-all transform ${
              isLoading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white hover:scale-[1.02] active:scale-[0.98]'
            }`}
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
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
                Signing In...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{' '}
            <span
              onClick={handleRegisterClick}
              className="text-blue-600 hover:text-blue-700 font-semibold hover:underline cursor-pointer"
            >
              Register
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}