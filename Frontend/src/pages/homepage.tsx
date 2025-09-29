import { supabase } from '../lib/supabaseClient'
import { useNavigate } from 'react-router-dom'

function Home() {
  const navigate = useNavigate()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <h1 className="text-3xl font-bold text-gray-800 mb-4">
        Welcome to the Home Page 🎉
      </h1>
      <p className="text-gray-600 mb-6">
        This is a protected route. Only logged-in users can see this page.
      </p>
      <button
        onClick={handleLogout}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Logout
      </button>
    </div>
  )
}

export default Home
