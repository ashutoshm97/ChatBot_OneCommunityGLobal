import { useState } from 'react'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import { supabase } from '../lib/supabaseClient'
import { LoginFormSchema, SignUpFormSchema } from '../lib/schemas'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})

  const validateForm = (): boolean => {
    setFormErrors({})
    try {
      if (isSignUp) {
        SignUpFormSchema.parse({ email, password, confirmPassword })
      } else {
        LoginFormSchema.parse({ email, password })
      }
      return true
    } catch (err: any) {
      if (err.errors) {
        const errors: Record<string, string> = {}
        err.errors.forEach((e: any) => {
          if (e.path) {
            errors[e.path[0]] = e.message
          }
        })
        setFormErrors(errors)
      }
      return false
    }
  }

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    setLoading(true)
    setError('')

    try {
      if (isSignUp) {
        // Sign up with Supabase
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/auth/callback`
          }
        })
        
        if (error) throw error
        
        setError('Check your email for the confirmation link!')
      } else {
        // Sign in with Supabase
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password
        })
        
        if (error) throw error
        
        // Login successful - your App.tsx will detect the auth state change
        // and redirect automatically via the onAuthStateChange listener
      }
    } catch (err: any) {
      console.error('Auth error:', err)
      
      // Handle specific Supabase error messages
      let errorMessage = 'An error occurred during authentication'
      
      if (err.message) {
        switch (err.message) {
          case 'Invalid login credentials':
            errorMessage = 'Invalid email or password'
            break
          case 'Email not confirmed':
            errorMessage = 'Please check your email and confirm your account'
            break
          case 'User already registered':
            errorMessage = 'An account with this email already exists'
            break
          case 'Password should be at least 6 characters':
            errorMessage = 'Password must be at least 6 characters long'
            break
          default:
            errorMessage = err.message
        }
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    try {
      setLoading(true)
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })
      
      if (error) throw error
    } catch (err: any) {
      console.error('Google sign in error:', err)
      setError('Failed to sign in with Google')
      setLoading(false)
    }
  }

  const getFieldError = (field: string) => formErrors[field] || ''

  const resetForm = () => {
    setEmail('')
    setPassword('')
    setConfirmPassword('')
    setFormErrors({})
    setError('')
  }

  const handleModeToggle = () => {
    setIsSignUp(!isSignUp)
    resetForm()
  }

  const handleForgotPassword = async () => {
    if (!email) {
      setError('Please enter your email address first')
      return
    }

    try {
      setLoading(true)
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      })
      
      if (error) throw error
      
      setError('Password reset link sent to your email!')
    } catch (err: any) {
      console.error('Password reset error:', err)
      setError('Failed to send password reset email')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Header */}
        <div className="login-header">
          <div className="login-icon">
            <LogIn className="login-icon-svg" />
          </div>
          <h2 className="login-title">
            {isSignUp ? 'Create your account' : 'Welcome back'}
          </h2>
          <p className="login-subtitle">
            {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              type="button"
              className="toggle-auth-btn"
              onClick={handleModeToggle}
              disabled={loading}
            >
              {isSignUp ? 'Sign in' : 'Sign up'}
            </button>
          </p>
        </div>

        {/* Form */}
        <form className="login-form" onSubmit={handleAuth}>
          {/* Email Field */}
          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Email address
            </label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={`form-input ${getFieldError('email') ? 'input-error' : ''}`}
              required
              disabled={loading}
            />
            {getFieldError('email') && (
              <p className="error-message">{getFieldError('email')}</p>
            )}
          </div>

          {/* Password Field */}
          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Password
            </label>
            <div className="password-input-container">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`form-input password-input ${getFieldError('password') ? 'input-error' : ''}`}
                required
                disabled={loading}
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
              >
                {showPassword ? <EyeOff className="password-icon" /> : <Eye className="password-icon" />}
              </button>
            </div>
            {getFieldError('password') && (
              <p className="error-message">{getFieldError('password')}</p>
            )}
          </div>

          {/* Confirm Password Field (Sign Up Only) */}
          {isSignUp && (
            <div className="form-group">
              <label htmlFor="confirmPassword" className="form-label">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`form-input ${getFieldError('confirmPassword') ? 'input-error' : ''}`}
                required
                disabled={loading}
              />
              {getFieldError('confirmPassword') && (
                <p className="error-message">{getFieldError('confirmPassword')}</p>
              )}
            </div>
          )}

          {/* Error/Success Message */}
          {error && (
            <div className={`message ${error.includes('Check your email') || error.includes('Password reset link') ? 'success-message' : 'error-banner'}`}>
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="submit-button"
          >
            {loading ? (
              <div className="button-content">
                <div className="loading-spinner"></div>
                <span>Processing...</span>
              </div>
            ) : (
              <div className="button-content">
                <LogIn className="button-icon" />
                <span>{isSignUp ? 'Create Account' : 'Sign In'}</span>
              </div>
            )}
          </button>

          {/* Google Sign In Button */}
          {/* <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="google-signin-button"
          >
            <div className="button-content">
              <svg className="google-icon" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <span>Continue with Google</span>
            </div>
          </button> */}
        </form>

        {/* Footer */}
        {!isSignUp && (
          <div className="login-footer">
            <button
              type="button"
              className="forgot-password-btn"
              onClick={handleForgotPassword}
              disabled={loading}
            >
              Forgot your password?
            </button>
          </div>
        )}
      </div>
    </div>
  )
}