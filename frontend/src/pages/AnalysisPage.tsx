import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Pause, RotateCcw, ArrowLeft, ArrowRight, CheckCircle, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { runAnalysis, getJobStatus, cancelJob } from '../services/api'
import { AnalysisSettings, JobStatus, AnalysisStatus } from '../types'

const AnalysisPage: React.FC = () => {
  const [settings, setSettings] = useState<AnalysisSettings | null>(null)
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    // ローカルストレージから設定を取得
    const savedSettings = localStorage.getItem('analysisSettings')
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings))
    } else {
      navigate('/settings')
    }
  }, [navigate])

  useEffect(() => {
    let interval: number | null = null

    if (isRunning && jobStatus?.job_id) {
      interval = setInterval(async () => {
        try {
          const status = await getJobStatus(jobStatus.job_id)
          setJobStatus(status)
          setProgress(status.progress * 100)

          if (status.status === 'completed') {
            setIsRunning(false)
            toast.success('分析が完了しました')
            navigate('/results')
          } else if (status.status === 'failed') {
            setIsRunning(false)
            toast.error('分析中にエラーが発生しました')
          }
        } catch (error) {
          console.error('ステータス取得エラー:', error)
        }
      }, 2000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isRunning, jobStatus?.job_id, navigate])

  const handleStartAnalysis = async () => {
    if (!settings) return

    try {
      setIsRunning(true)
      setProgress(0)
      
      const uploadResult = JSON.parse(localStorage.getItem('uploadResult') || '{}')
      const request = {
        job_id: uploadResult.job_id,
        settings: settings
      }

      const result = await runAnalysis(request)
      setJobStatus(result)
      toast.success('分析を開始しました')
    } catch (error: any) {
      setIsRunning(false)
      toast.error(`分析開始エラー: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleCancelAnalysis = async () => {
    if (!jobStatus?.job_id) return

    try {
      await cancelJob(jobStatus.job_id)
      setIsRunning(false)
      toast.success('分析をキャンセルしました')
    } catch (error: any) {
      toast.error(`キャンセルエラー: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleReset = () => {
    setJobStatus(null)
    setIsRunning(false)
    setProgress(0)
  }

  const getStatusIcon = (status: AnalysisStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'running':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
      default:
        return <div className="h-5 w-5"></div>
    }
  }

  const getStatusText = (status: AnalysisStatus) => {
    switch (status) {
      case 'pending':
        return '待機中'
      case 'running':
        return '実行中'
      case 'completed':
        return '完了'
      case 'failed':
        return '失敗'
      default:
        return '不明'
    }
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-gray-500">設定が読み込まれていません</p>
          <button 
            onClick={() => navigate('/settings')}
            className="btn-primary mt-4"
          >
            設定に戻る
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          交互作用検定の実行
        </h1>
        <p className="text-lg text-gray-600">
          設定されたパラメータで分析を実行します
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 分析設定の確認 */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-6">分析設定</h2>
          
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">変数設定</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <p><strong>モデレーター:</strong> {settings.variable_mapping.moderators.join(', ')}</p>
                <p><strong>アウトカム:</strong> {settings.variable_mapping.outcomes.join(', ')}</p>
                <p><strong>介入フラグ:</strong> {settings.variable_mapping.intervention}</p>
              </div>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">分析パラメータ</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <p><strong>FDR α値:</strong> {settings.fdr_alpha}</p>
                <p><strong>最小サンプル数:</strong> {settings.min_sample_size}</p>
                <p><strong>図の生成:</strong> {settings.generate_plots ? '有効' : '無効'}</p>
                {settings.generate_plots && (
                  <p><strong>最大図数:</strong> {settings.max_plots}</p>
                )}
              </div>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">データ処理</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <p><strong>モデレーター中心化:</strong> {settings.data_processing.center_moderators ? '有効' : '無効'}</p>
                <p><strong>アウトカム中心化:</strong> {settings.data_processing.center_outcomes ? '有効' : '無効'}</p>
                <p><strong>感度分析:</strong> {settings.data_processing.run_sensitivity ? '有効' : '無効'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* 分析実行コントロール */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-6">分析実行</h2>
          
          <div className="space-y-6">
            {/* 実行ボタン */}
            <div className="text-center">
              {!isRunning ? (
                <button
                  onClick={handleStartAnalysis}
                  className="btn-primary text-lg px-8 py-3"
                >
                  <Play className="h-5 w-5 mr-2" />
                  分析を開始
                </button>
              ) : (
                <button
                  onClick={handleCancelAnalysis}
                  className="bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-8 rounded-lg transition-colors duration-200"
                >
                  <Pause className="h-5 w-5 mr-2" />
                  分析をキャンセル
                </button>
              )}
            </div>

            {/* 進捗表示 */}
            {jobStatus && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">進捗状況</span>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(jobStatus.status)}
                    <span className="text-sm text-gray-600">
                      {getStatusText(jobStatus.status)}
                    </span>
                  </div>
                </div>

                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>

                <p className="text-sm text-gray-600 text-center">
                  {Math.round(progress)}%
                </p>

                {jobStatus.message && (
                  <p className="text-sm text-gray-600 text-center">
                    {jobStatus.message}
                  </p>
                )}
              </div>
            )}

            {/* リセットボタン */}
            {jobStatus && (
              <div className="text-center">
                <button
                  onClick={handleReset}
                  className="btn-secondary"
                >
                  <RotateCcw className="h-4 w-4 mr-2" />
                  リセット
                </button>
              </div>
            )}
          </div>
        </div>

        {/* 分析の詳細情報 */}
        <div className="lg:col-span-2">
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">分析の詳細</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">実行される検定</h3>
                <div className="text-sm text-gray-600">
                  <p>モデレーター数: {settings.variable_mapping.moderators.length}</p>
                  <p>アウトカム数: {settings.variable_mapping.outcomes.length}</p>
                  <p>総検定数: {settings.variable_mapping.moderators.length * settings.variable_mapping.outcomes.length}</p>
                </div>
              </div>

              <div>
                <h3 className="font-medium text-gray-900 mb-2">統計手法</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>• 線形回帰（交互作用項含む）</p>
                  <p>• 単純傾斜分析（±1SD）</p>
                  <p>• 多重比較補正（FDR）</p>
                  <p>• 効果量（部分η²）</p>
                  {settings.data_processing.run_sensitivity && (
                    <p>• 感度分析（順序ロジット）</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ナビゲーション */}
      <div className="flex justify-between mt-8">
        <button 
          onClick={() => navigate('/settings')}
          className="btn-secondary"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          設定に戻る
        </button>
        
        {jobStatus?.status === 'completed' && (
          <button 
            onClick={() => navigate('/results')}
            className="btn-primary"
          >
            結果を表示
            <ArrowRight className="h-4 w-4 ml-2" />
          </button>
        )}
      </div>
    </div>
  )
}

export default AnalysisPage
