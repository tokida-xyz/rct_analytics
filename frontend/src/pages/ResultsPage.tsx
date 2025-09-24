import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, Eye, Filter, ArrowLeft, BarChart3, FileText, Image } from 'lucide-react'
import toast from 'react-hot-toast'
import { getAnalysisResult, downloadCsv, downloadLogs, downloadFigure, getFigureList } from '../services/api'
import { AnalysisResult, InteractionResult } from '../types'

const ResultsPage: React.FC = () => {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [filteredResults, setFilteredResults] = useState<InteractionResult[]>([])
  const [filter, setFilter] = useState({
    significant: false,
    moderator: '',
    outcome: ''
  })
  const [selectedModerator, setSelectedModerator] = useState<string>('')
  const [figures, setFigures] = useState<string[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    loadResults()
  }, [])

  useEffect(() => {
    if (result) {
      applyFilters()
    }
  }, [result, filter])

  const loadResults = async () => {
    try {
      const uploadResult = JSON.parse(localStorage.getItem('uploadResult') || '{}')
      if (!uploadResult.job_id) {
        navigate('/')
        return
      }

      const analysisResult = await getAnalysisResult(uploadResult.job_id)
      setResult(analysisResult)
      
      // 図のリストを取得
      const figureList = await getFigureList(uploadResult.job_id)
      setFigures(figureList.figures?.map((f: any) => f.name) || [])
    } catch (error: any) {
      toast.error(`結果の読み込みエラー: ${error.response?.data?.detail || error.message}`)
      navigate('/analysis')
    }
  }

  const applyFilters = () => {
    if (!result) return

    let filtered = result.results

    if (filter.significant) {
      filtered = filtered.filter(r => r.q_interaction < 0.05)
    }

    if (filter.moderator) {
      filtered = filtered.filter(r => r.moderator === filter.moderator)
    }

    if (filter.outcome) {
      filtered = filtered.filter(r => r.outcome === filter.outcome)
    }

    setFilteredResults(filtered)
  }

  const handleDownloadCsv = async () => {
    try {
      const uploadResult = JSON.parse(localStorage.getItem('uploadResult') || '{}')
      const blob = await downloadCsv(uploadResult.job_id)
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `interaction_summary_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.success('CSVファイルをダウンロードしました')
    } catch (error: any) {
      toast.error(`ダウンロードエラー: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleDownloadLogs = async () => {
    try {
      const uploadResult = JSON.parse(localStorage.getItem('uploadResult') || '{}')
      const blob = await downloadLogs(uploadResult.job_id)
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `analysis_log_${new Date().toISOString().split('T')[0]}.txt`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.success('ログファイルをダウンロードしました')
    } catch (error: any) {
      toast.error(`ダウンロードエラー: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleDownloadFigure = async (figureName: string) => {
    try {
      const uploadResult = JSON.parse(localStorage.getItem('uploadResult') || '{}')
      const blob = await downloadFigure(uploadResult.job_id, figureName)
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = figureName
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      toast.success('図をダウンロードしました')
    } catch (error: any) {
      toast.error(`ダウンロードエラー: ${error.response?.data?.detail || error.message}`)
    }
  }

  const getSignificanceColor = (qValue: number) => {
    if (qValue < 0.001) return 'text-red-600 font-bold'
    if (qValue < 0.01) return 'text-red-500 font-semibold'
    if (qValue < 0.05) return 'text-orange-500 font-medium'
    return 'text-gray-500'
  }

  const getSignificanceText = (qValue: number) => {
    if (qValue < 0.001) return '***'
    if (qValue < 0.01) return '**'
    if (qValue < 0.05) return '*'
    return 'ns'
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-gray-500">結果が読み込まれていません</p>
          <button 
            onClick={() => navigate('/analysis')}
            className="btn-primary mt-4"
          >
            分析に戻る
          </button>
        </div>
      </div>
    )
  }

  const moderators = [...new Set(result.results.map(r => r.moderator))].sort()
  const outcomes = [...new Set(result.results.map(r => r.outcome))].sort()
  const significantResults = result.results.filter(r => r.q_interaction < 0.05)

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">分析結果</h1>
          <p className="text-lg text-gray-600 mt-2">
            交互作用検定の結果を確認・ダウンロードできます
          </p>
        </div>
        <div className="flex space-x-2">
          <button onClick={handleDownloadCsv} className="btn-secondary">
            <FileText className="h-4 w-4 mr-2" />
            CSV
          </button>
          <button onClick={handleDownloadLogs} className="btn-secondary">
            <Download className="h-4 w-4 mr-2" />
            ログ
          </button>
        </div>
      </div>

      {/* サマリー */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="card text-center">
          <div className="text-2xl font-bold text-primary-600">{result.results.length}</div>
          <div className="text-sm text-gray-600">総検定数</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600">{significantResults.length}</div>
          <div className="text-sm text-gray-600">有意な結果</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-600">{moderators.length}</div>
          <div className="text-sm text-gray-600">モデレーター数</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-purple-600">{outcomes.length}</div>
          <div className="text-sm text-gray-600">アウトカム数</div>
        </div>
      </div>

      {/* フィルター */}
      <div className="card mb-8">
        <h2 className="text-xl font-semibold mb-4">フィルター</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="significant"
              checked={filter.significant}
              onChange={(e) => setFilter(prev => ({ ...prev, significant: e.target.checked }))}
              className="mr-2"
            />
            <label htmlFor="significant" className="text-sm font-medium text-gray-700">
              有意な結果のみ
            </label>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">モデレーター</label>
            <select
              value={filter.moderator}
              onChange={(e) => setFilter(prev => ({ ...prev, moderator: e.target.value }))}
              className="input-field"
            >
              <option value="">すべて</option>
              {moderators.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">アウトカム</label>
            <select
              value={filter.outcome}
              onChange={(e) => setFilter(prev => ({ ...prev, outcome: e.target.value }))}
              className="input-field"
            >
              <option value="">すべて</option>
              {outcomes.map(o => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => setFilter({ significant: false, moderator: '', outcome: '' })}
              className="btn-secondary w-full"
            >
              <Filter className="h-4 w-4 mr-2" />
              リセット
            </button>
          </div>
        </div>
      </div>

      {/* 結果テーブル */}
      <div className="card mb-8">
        <h2 className="text-xl font-semibold mb-4">
          検定結果 ({filteredResults.length}件)
        </h2>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  モデレーター
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  アウトカム
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  n
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  β (交互作用)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  p値
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  q値
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  部分η²
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  単純傾斜 (Low)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  単純傾斜 (High)
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredResults.map((row, index) => (
                <tr key={index} className={row.q_interaction < 0.05 ? 'bg-green-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {row.moderator}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.outcome}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.n_used}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.beta_interaction.toFixed(3)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.p_interaction.toFixed(3)}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm ${getSignificanceColor(row.q_interaction)}`}>
                    {row.q_interaction.toFixed(3)} {getSignificanceText(row.q_interaction)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.partial_eta2.toFixed(3)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.simple_slope_low.slope.toFixed(3)} (p={row.simple_slope_low.p_value.toFixed(3)})
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.simple_slope_high.slope.toFixed(3)} (p={row.simple_slope_high.p_value.toFixed(3)})
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 図の表示 */}
      {figures.length > 0 && (
        <div className="card mb-8">
          <h2 className="text-xl font-semibold mb-4">生成された図</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {figures.map((figure, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900">{figure}</span>
                  <button
                    onClick={() => handleDownloadFigure(figure)}
                    className="text-primary-600 hover:text-primary-700"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </div>
                <div className="text-xs text-gray-500">
                  {figure.includes('simple_slopes') ? '単純傾斜プロット' : '棒グラフ'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 注記 */}
      {result.notes.length > 0 && (
        <div className="card mb-8">
          <h2 className="text-xl font-semibold mb-4">注記</h2>
          <ul className="space-y-2">
            {result.notes.map((note, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start">
                <span className="mr-2">•</span>
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ナビゲーション */}
      <div className="flex justify-between">
        <button 
          onClick={() => navigate('/analysis')}
          className="btn-secondary"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          分析に戻る
        </button>
        
        <button 
          onClick={() => navigate('/')}
          className="btn-primary"
        >
          新しい分析を開始
        </button>
      </div>
    </div>
  )
}

export default ResultsPage
