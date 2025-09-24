import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { uploadFile } from '../services/api'
import { UploadResponse } from '../types'

const UploadPage: React.FC = () => {
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const navigate = useNavigate()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setUploading(true)
    try {
      const result = await uploadFile(file)
      setUploadResult(result)
      toast.success('ファイルのアップロードが完了しました')
      
      // ローカルストレージに保存
      localStorage.setItem('uploadResult', JSON.stringify(result))
      
      // 設定ページに遷移
      navigate('/settings')
    } catch (error: any) {
      toast.error(`アップロードエラー: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploading(false)
    }
  }, [navigate])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          データファイルのアップロード
        </h1>
        <p className="text-lg text-gray-600">
          CSVまたはExcelファイルをアップロードして、交互作用検定を開始しましょう
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* アップロードエリア */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">ファイルアップロード</h2>
          
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <input {...getInputProps()} />
            
            {uploading ? (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
                <p className="text-gray-600">アップロード中...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Upload className="h-12 w-12 text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-900 mb-2">
                  {isDragActive ? 'ファイルをここにドロップ' : 'ファイルをドラッグ&ドロップ'}
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  または、クリックしてファイルを選択
                </p>
                <p className="text-xs text-gray-400">
                  対応形式: CSV, XLSX, XLS (最大50MB)
                </p>
              </div>
            )}
          </div>
        </div>

        {/* アップロード結果 */}
        {uploadResult && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">アップロード結果</h2>
            
            <div className="space-y-4">
              <div className="flex items-center text-green-600">
                <CheckCircle className="h-5 w-5 mr-2" />
                <span className="font-medium">アップロード完了</span>
              </div>
              
              <div>
                <p className="text-sm text-gray-600">ファイル名:</p>
                <p className="font-medium">{uploadResult.filename}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-600">ジョブID:</p>
                <p className="font-mono text-sm">{uploadResult.job_id}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-600">検出された列数:</p>
                <p className="font-medium">{uploadResult.columns.length}列</p>
              </div>
            </div>
          </div>
        )}

        {/* サポート情報 */}
        <div className="lg:col-span-2">
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">データ形式について</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">推奨データ形式</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• 1行目はヘッダー（列名）</li>
                  <li>• 1行 = 1回答者</li>
                  <li>• 欠損値は空欄またはNA</li>
                  <li>• 文字エンコーディング: UTF-8</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium text-gray-900 mb-2">列の役割</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• <strong>モデレーター</strong>: B〜F列（複数選択可）</li>
                  <li>• <strong>アウトカム</strong>: G〜R列（複数選択可）</li>
                  <li>• <strong>介入フラグ</strong>: S列（0/1の値）</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UploadPage
