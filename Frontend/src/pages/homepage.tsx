import { Link } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { useNavigate } from 'react-router-dom'

function Home() {
  const navigate = useNavigate()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#fafafa]">
      <h1 className="text-xl font-semibold text-gray-900 mb-2">
        One Community
      </h1>
      <p className="text-gray-600 text-sm mb-6">
        Add documents to power the chatbot.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <Link
          to="/upload"
          className="px-5 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition"
        >
          Upload
        </Link>
        <Link
          to="/documents"
          className="px-5 py-2.5 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition"
        >
          My documents
        </Link>
      </div>
      <button
        onClick={handleLogout}
        className="text-sm text-gray-500 hover:text-gray-700"
      >
        Logout
      </button>
    </div>
  )
}

export default Home
