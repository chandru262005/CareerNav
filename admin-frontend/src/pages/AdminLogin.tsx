import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAdminAuth } from '../context/AdminAuthContext'
import { adminAuthService } from '../services/admin'
import { Button } from '../components/shared/Button'
import { Input } from '../components/shared/Input'
import { FormField } from '../components/shared/FormField'
import { AlertCircle, Mail, Lock } from 'lucide-react'

export const AdminLogin: React.FC = () => {
  const navigate = useNavigate()
  const { setAdmin, setToken, setError } = useAdminAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setLocalError] = useState('')
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)
    setLocalError('')
    setError(null)

    try {
      const response = await adminAuthService.login({
        email: formData.email,
        password: formData.password,
      })

      if (response.success) {
        // Backend returns token at top-level and admin in `data`
        setToken(response.token)
        setAdmin(response.data)
        navigate('/dashboard')
      }
    } catch (err: any) {
      const message = err.response?.data?.message || 'Login failed. Please try again.'
      const status = err.response?.status

      // If it's a 403 verification error
      if (status === 403 && message.toLowerCase().includes('verify')) {
        setLocalError(message)
      } else {
        setLocalError(message)
      }
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleResendVerification = async () => {
    if (!formData.email) {
      setLocalError('Please enter your email')
      return
    }

    try {
      setIsLoading(true)
      await adminAuthService.resendVerification(formData.email)
      setLocalError('')
      // Redirect to verification sent page
      navigate(`/verification-sent?email=${encodeURIComponent(formData.email)}`)
    } catch (err: any) {
      setLocalError(err.response?.data?.message || 'Failed to resend verification email')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-2xl">A</span>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">CareerNav Admin</h1>
          <p className="text-slate-600">Sign in to your admin account</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg space-y-3">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
            {error.includes('verify') && (
              <Button
                type="button"
                onClick={handleResendVerification}
                variant="outline"
                size="sm"
                className="w-full"
                disabled={isLoading}
              >
                Resend Verification Email
              </Button>
            )}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-slate-200 p-8 space-y-6">
          {/* Email Field */}
          <FormField
            label="Email Address"
            error={formData.email && !formData.email.includes('@') ? 'Invalid email' : ''}
          >
            <div className="relative">
              <Input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                required
              />
              <Mail className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            </div>
          </FormField>

          {/* Password Field */}
          <FormField label="Password">
            <div className="relative">
              <Input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                required
              />
              <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            </div>
          </FormField>

          {/* Submit Button */}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
      </div>
    </div>
  )
}
