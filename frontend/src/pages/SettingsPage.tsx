import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Save, Download, Upload } from 'lucide-react'
import toast from 'react-hot-toast'
import { UploadResponse, AnalysisSettings, VariableMapping, DataProcessingSettings } from '../types'

const SettingsPage: React.FC = () => {
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [settings, setSettings] = useState<AnalysisSettings>({
    variable_mapping: {
      moderators: [],
      outcomes: [],
      intervention: ''
    },
    data_processing: {
      center_outcomes: false,
      center_moderators: true,
      ordinal_outcomes: [],
      run_sensitivity: false,
      seed: 123
    },
    fdr_alpha: 0.05,
    min_sample_size: 30,
    generate_plots: true,
    max_plots: 20
  })
  const navigate = useNavigate()

  useEffect(() => {
    // ローカルストレージからアップロード結果を取得
    const savedResult = localStorage.getItem('uploadResult')
    if (savedResult) {
      const result = JSON.parse(savedResult)
      setUploadResult(result)
      
      // デフォルト設定を自動設定
      const defaultModerators = result.columns
        .filter((col: any) => col.name.match(/^[B-F]$/))
        .map((col: any) => col.name)
      
      const defaultOutcomes = result.columns
        .filter((col: any) => col.name.match(/^[G-R]$/))
        .map((col: any) => col.name)
      
      const defaultIntervention = result.columns
        .find((col: any) => col.name === 'S')?.name || ''
      
      setSettings(prev => ({
        ...prev,
        variable_mapping: {
          moderators: defaultModerators,
          outcomes: defaultOutcomes,
          intervention: defaultIntervention
        }
      }))
    } else {
      navigate('/')
    }
  }, [navigate])

  const handleVariableMappingChange = (field: keyof VariableMapping, value: string[]) => {
    setSettings(prev => ({
      ...prev,
      variable_mapping: {
        ...prev.variable_mapping,
        [field]: field === 'intervention' ? value[0] || '' : value
      }
    }))
  }

  const handleDataProcessingChange = (field: keyof DataProcessingSettings, value: any) => {
    setSettings(prev => ({
      ...prev,
      data_processing: {
        ...prev.data_processing,
        [field]: value
      }
    }))
  }

  const handleSaveSettings = () => {
    localStorage.setItem('analysisSettings', JSON.stringify(settings))
    toast.success('設定を保存しました')
  }

  const handleLoadSettings = () => {
    const savedSettings = localStorage.getItem('analysisSettings')
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings))
      toast.success('設定を読み込みました')
    } else {
      toast.error('保存された設定が見つかりません')
    }
  }

  const handleExportSettings = () => {
    const dataStr = JSON.stringify(settings, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    const exportFileDefaultName = 'analysis_settings.json'
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  const handleImportSettings = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const importedSettings = JSON.parse(e.target?.result as string)
        setSettings(importedSettings)
        toast.success('設定をインポートしました')
      } catch (error) {
        toast.error('設定ファイルの読み込みに失敗しました')
      }
    }
    reader.readAsText(file)
  }

  const handleNext = () => {
    // バリデーション
    if (settings.variable_mapping.moderators.length === 0) {
      toast.error('モデレーターを1つ以上選択してください')
      return
    }
    if (settings.variable_mapping.outcomes.length === 0) {
      toast.error('アウトカムを1つ以上選択してください')
      return
    }
    if (!settings.variable_mapping.intervention) {
      toast.error('介入フラグを選択してください')
      return
    }

    // 設定を保存
    localStorage.setItem('analysisSettings', JSON.stringify(settings))
    navigate('/analysis')
  }

  if (!uploadResult) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-gray-500">データが読み込まれていません</p>
          <button 
            onClick={() => navigate('/')}
            className="btn-primary mt-4"
          >
            データをアップロード
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">分析設定</h1>
          <p className="text-lg text-gray-600 mt-2">
            変数の役割と分析パラメータを設定してください
          </p>
        </div>
        <div className="flex space-x-2">
          <button onClick={handleLoadSettings} className="btn-secondary">
            <Upload className="h-4 w-4 mr-2" />
            設定読み込み
          </button>
          <button onClick={handleSaveSettings} className="btn-secondary">
            <Save className="h-4 w-4 mr-2" />
            設定保存
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 変数マッピング */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-6">変数の役割設定</h2>
          
          <div className="space-y-6">
            {/* モデレーター選択 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                モデレーター変数 (複数選択可)
              </label>
              <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto">
                {uploadResult.columns.map((col) => (
                  <label key={col.name} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.variable_mapping.moderators.includes(col.name)}
                      onChange={(e) => {
                        const newModerators = e.target.checked
                          ? [...settings.variable_mapping.moderators, col.name]
                          : settings.variable_mapping.moderators.filter(m => m !== col.name)
                        handleVariableMappingChange('moderators', newModerators)
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm">{col.name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* アウトカム選択 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                アウトカム変数 (複数選択可)
              </label>
              <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto">
                {uploadResult.columns.map((col) => (
                  <label key={col.name} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.variable_mapping.outcomes.includes(col.name)}
                      onChange={(e) => {
                        const newOutcomes = e.target.checked
                          ? [...settings.variable_mapping.outcomes, col.name]
                          : settings.variable_mapping.outcomes.filter(o => o !== col.name)
                        handleVariableMappingChange('outcomes', newOutcomes)
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm">{col.name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 介入フラグ選択 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                介入フラグ変数 (単一選択)
              </label>
              <select
                value={settings.variable_mapping.intervention}
                onChange={(e) => handleVariableMappingChange('intervention', [e.target.value])}
                className="input-field"
              >
                <option value="">選択してください</option>
                {uploadResult.columns.map((col) => (
                  <option key={col.name} value={col.name}>
                    {col.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* データ処理設定 */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-6">データ処理設定</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                モデレーターの平均中心化
              </label>
              <input
                type="checkbox"
                checked={settings.data_processing.center_moderators}
                onChange={(e) => handleDataProcessingChange('center_moderators', e.target.checked)}
                className="h-4 w-4 text-primary-600"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                アウトカムの平均中心化
              </label>
              <input
                type="checkbox"
                checked={settings.data_processing.center_outcomes}
                onChange={(e) => handleDataProcessingChange('center_outcomes', e.target.checked)}
                className="h-4 w-4 text-primary-600"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                感度分析の実行
              </label>
              <input
                type="checkbox"
                checked={settings.data_processing.run_sensitivity}
                onChange={(e) => handleDataProcessingChange('run_sensitivity', e.target.checked)}
                className="h-4 w-4 text-primary-600"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                乱数シード
              </label>
              <input
                type="number"
                value={settings.data_processing.seed}
                onChange={(e) => handleDataProcessingChange('seed', parseInt(e.target.value))}
                className="input-field"
              />
            </div>
          </div>
        </div>

        {/* 分析パラメータ */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-6">分析パラメータ</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                FDR補正のα値
              </label>
              <input
                type="number"
                step="0.01"
                min="0.001"
                max="0.5"
                value={settings.fdr_alpha}
                onChange={(e) => setSettings(prev => ({ ...prev, fdr_alpha: parseFloat(e.target.value) }))}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                最小サンプル数
              </label>
              <input
                type="number"
                min="10"
                value={settings.min_sample_size}
                onChange={(e) => setSettings(prev => ({ ...prev, min_sample_size: parseInt(e.target.value) }))}
                className="input-field"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                図の生成
              </label>
              <input
                type="checkbox"
                checked={settings.generate_plots}
                onChange={(e) => setSettings(prev => ({ ...prev, generate_plots: e.target.checked }))}
                className="h-4 w-4 text-primary-600"
              />
            </div>

            {settings.generate_plots && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  最大図生成数
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={settings.max_plots}
                  onChange={(e) => setSettings(prev => ({ ...prev, max_plots: parseInt(e.target.value) }))}
                  className="input-field"
                />
              </div>
            )}
          </div>
        </div>

        {/* 設定のインポート/エクスポート */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-6">設定の管理</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                設定ファイルのインポート
              </label>
              <input
                type="file"
                accept=".json"
                onChange={handleImportSettings}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
              />
            </div>

            <button onClick={handleExportSettings} className="btn-secondary w-full">
              <Download className="h-4 w-4 mr-2" />
              設定をエクスポート
            </button>
          </div>
        </div>
      </div>

      {/* ナビゲーション */}
      <div className="flex justify-between mt-8">
        <button 
          onClick={() => navigate('/')}
          className="btn-secondary"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          戻る
        </button>
        
        <button 
          onClick={handleNext}
          className="btn-primary"
        >
          次へ
          <ArrowRight className="h-4 w-4 ml-2" />
        </button>
      </div>
    </div>
  )
}

export default SettingsPage
