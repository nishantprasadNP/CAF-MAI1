import { useState } from 'react'
import axios from 'axios'

const sectionStyle = {
  padding: '12px',
  border: '1px solid #d1d5db',
  margin: '12px 0',
}

function extractColumnsFromCsvText(csvText) {
  const firstLine = csvText.split(/\r?\n/).find((line) => line.trim() !== '')
  if (!firstLine) {
    return []
  }

  return firstLine
    .split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/)
    .map((column) => column.trim().replace(/^"|"$/g, ''))
    .filter((column) => column.length > 0)
}

function App() {
  const [file, setFile] = useState(null)
  const [csvColumns, setCsvColumns] = useState([])
  const [targetColumn, setTargetColumn] = useState('')
  const [biasColumns, setBiasColumns] = useState([])
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleFileChange = async (event) => {
    const selectedFile = event.target.files?.[0] || null
    setFile(selectedFile)
    setData(null)
    setError('')

    if (!selectedFile) {
      setCsvColumns([])
      setTargetColumn('')
      setBiasColumns([])
      return
    }

    try {
      const csvText = await selectedFile.text()
      const columns = extractColumnsFromCsvText(csvText)
      setCsvColumns(columns)
      setTargetColumn(columns[columns.length - 1] || '')
      setBiasColumns([])
    } catch {
      setCsvColumns([])
      setTargetColumn('')
      setBiasColumns([])
      setError('Failed to read CSV file.')
    }
  }

  const handleBiasColumnsChange = (event) => {
    const selectedValues = Array.from(event.target.selectedOptions).map((option) => option.value)
    setBiasColumns(selectedValues)
  }

  const handleTargetColumnChange = (event) => {
    const selectedTarget = event.target.value
    setTargetColumn(selectedTarget)
    setBiasColumns((prev) => prev.filter((column) => column !== selectedTarget))
  }

  const handleProcessData = async () => {
    if (!file) {
      setError('Please select a CSV file.')
      return
    }
    if (!targetColumn) {
      setError('Please select a target column.')
      return
    }

    setLoading(true)
    setError('')
    setData(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('target_column', targetColumn)
      formData.append('bias_columns', JSON.stringify(biasColumns))

      const response = await axios.post('http://127.0.0.1:8000/process-data', formData)
      setData(response.data)
    } catch (requestError) {
      const detail = requestError?.response?.data?.detail
      setError(detail || 'Failed to process data.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '16px' }}>
      <h1>CSV Data Processor</h1>

      <div style={{ marginBottom: '16px' }}>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
        />
        <div style={{ marginTop: '12px' }}>
          <label>
            Target Column:{' '}
            <select value={targetColumn} onChange={handleTargetColumnChange}>
              <option value="">Select target column</option>
              {csvColumns.map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div style={{ marginTop: '12px' }}>
          <label>
            Bias Columns:
            <br />
            <select multiple value={biasColumns} onChange={handleBiasColumnsChange}>
              {csvColumns
                .filter((column) => column !== targetColumn)
                .map((column) => (
                  <option key={column} value={column}>
                    {column}
                  </option>
                ))}
            </select>
          </label>
        </div>
        <div style={{ marginTop: '12px' }}>
        <button onClick={handleProcessData} disabled={loading}>
          Process Data
        </button>
        </div>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p>{error}</p>}

      {data && (
        <div style={{ marginTop: '8px' }}>
          <div style={sectionStyle}>
            <h2>X</h2>
            <pre>{JSON.stringify(data.X, null, 2)}</pre>
          </div>

          <div style={sectionStyle}>
            <h2>Y</h2>
            <pre>{JSON.stringify(data.Y, null, 2)}</pre>
          </div>

          <div style={sectionStyle}>
            <h2>B_user</h2>
            <pre>{JSON.stringify(data.B_user, null, 2)}</pre>
          </div>

          <div style={sectionStyle}>
            <h2>B_suggested</h2>
            <pre>{JSON.stringify(data.B_suggested, null, 2)}</pre>
          </div>

          <div style={sectionStyle}>
            <h2>B_hidden</h2>
            <pre>{JSON.stringify(data.B_hidden, null, 2)}</pre>
          </div>

          <div style={sectionStyle}>
            <h2>metadata</h2>
            <pre>{JSON.stringify(data.metadata, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
