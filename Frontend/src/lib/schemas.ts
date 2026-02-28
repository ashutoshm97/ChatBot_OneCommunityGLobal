import { z } from 'zod'

// --- User & Auth ---
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

// --- Form schemas ---
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
  path: ['confirmPassword'],
})

// --- Upload / file responses (e.g. /upload/file, /upload/files) ---
export const UploadResponseSchema = z.object({
  message: z.string(),
  document_id: z.union([z.string(), z.array(z.string())]),
  status: z.string().optional(),
  chunks_created: z.number().optional(),
})

export const FileListResponseSchema = z.object({
  files: z.array(z.object({
    id: z.string().optional(),
    name: z.string().optional(),
    url: z.string().optional(),
  })).optional(),
  count: z.number().optional(),
}).passthrough()

// --- RAG documents API ---
export const DocumentMetadataSchema = z.record(z.unknown()).and(
  z.object({
    title: z.string().optional(),
    source: z.string().optional(),
    filename: z.string().optional(),
  }).partial()
)

export const DocumentRecordSchema = z.object({
  id: z.string(),
  text: z.string(),
  metadata: DocumentMetadataSchema.optional().default({}),
  document_type: z.enum(['text', 'video']),
  created_at: z.string(),
  updated_at: z.string(),
})

export const DocumentListResponseSchema = z.object({
  documents: z.array(DocumentRecordSchema),
  count: z.number(),
  skip: z.number(),
  limit: z.number(),
})

export const DocumentUploadResponseSchema = z.object({
  message: z.string(),
  document_id: z.union([z.string(), z.array(z.string())]),
  status: z.string().optional(),
  chunks_created: z.number().optional(),
  document_ids: z.array(z.string()).optional(),
  transcription_preview: z.string().optional(),
})

// --- Types ---
export type User = z.infer<typeof UserSchema>
export type AuthResponse = z.infer<typeof AuthResponseSchema>
export type LoginForm = z.infer<typeof LoginFormSchema>
export type SignUpForm = z.infer<typeof SignUpFormSchema>
export type DocumentRecord = z.infer<typeof DocumentRecordSchema>
export type DocumentListResponse = z.infer<typeof DocumentListResponseSchema>
export type DocumentUploadResponse = z.infer<typeof DocumentUploadResponseSchema>

// --- Validators ---
export const validateAuthResponse = (data: unknown): AuthResponse => {
  return AuthResponseSchema.parse(data)
}

export const validateDocumentListResponse = (data: unknown): DocumentListResponse => {
  return DocumentListResponseSchema.parse(data)
}

export const validateDocumentUploadResponse = (data: unknown): DocumentUploadResponse => {
  return DocumentUploadResponseSchema.parse(data)
}
