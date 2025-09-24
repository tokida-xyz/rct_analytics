import axios from 'axios'
import { 
  UploadResponse, 
  AnalysisRequest, 
  JobStatus, 
  AnalysisResult,
  AnalysisSettings 
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

// ファイルアップロード
export const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  
  return response.data
}

// データプレビュー取得
export const getDataPreview = async (jobId: string, rows: number = 50) => {
  const response = await api.get(`/api/upload/${jobId}/preview?rows=${rows}`)
  return response.data
}

// 分析実行
export const runAnalysis = async (request: AnalysisRequest): Promise<JobStatus> => {
  const response = await api.post('/api/run', request)
  return response.data
}

// ジョブステータス取得
export const getJobStatus = async (jobId: string): Promise<JobStatus> => {
  const response = await api.get(`/api/run/${jobId}/status`)
  return response.data
}

// ジョブキャンセル
export const cancelJob = async (jobId: string) => {
  const response = await api.post(`/api/run/${jobId}/cancel`)
  return response.data
}

// 分析結果取得
export const getAnalysisResult = async (jobId: string): Promise<AnalysisResult> => {
  const response = await api.get(`/api/result/${jobId}`)
  return response.data
}

// CSVダウンロード
export const downloadCsv = async (jobId: string): Promise<Blob> => {
  const response = await api.get(`/api/download/${jobId}/csv`, {
    responseType: 'blob',
  })
  return response.data
}

// ログダウンロード
export const downloadLogs = async (jobId: string): Promise<Blob> => {
  const response = await api.get(`/api/download/${jobId}/logs`, {
    responseType: 'blob',
  })
  return response.data
}

// 図ダウンロード
export const downloadFigure = async (jobId: string, figureName: string): Promise<Blob> => {
  const response = await api.get(`/api/download/${jobId}/figs/${figureName}`, {
    responseType: 'blob',
  })
  return response.data
}

// 図リスト取得
export const getFigureList = async (jobId: string) => {
  const response = await api.get(`/api/result/${jobId}/figures`)
  return response.data
}

export default api
