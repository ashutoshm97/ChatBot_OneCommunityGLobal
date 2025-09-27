import { z } from 'zod'


export const UserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  role: z.string(),
  provider: z.string(),
})

export const AuthResponseSchema = z.object({
  valid: z.boolean(),
  user: UserSchema.nullable().optional(),
  error: z.string().nullable().optional(),
})
// Form Schemas
export const LoginFormSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

export const SignUpFormSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

export type User = z.infer<typeof UserSchema>
export type AuthResponse = z.infer<typeof AuthResponseSchema>
export type LoginForm = z.infer<typeof LoginFormSchema>
export type SignUpForm = z.infer<typeof SignUpFormSchema>

export const validateAuthResponse = (data: unknown): AuthResponse => {
  return AuthResponseSchema.parse(data)
}
