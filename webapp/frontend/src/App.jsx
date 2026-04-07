import { useState } from 'react'

function App() {
  const [logoFile, setLogoFile] = useState(null)
  const [imageFiles, setImageFiles] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)

  const handleLogoChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setLogoFile(e.target.files[0])
    }
  }

  const handleImagesChange = (e) => {
    if (e.target.files) {
      setImageFiles(Array.from(e.target.files))
    }
  }

  const handleProcess = async () => {
    if (!logoFile || imageFiles.length === 0) return

    setIsProcessing(true)

    // Using FormData to send multipart/form-data
    const formData = new FormData()
    formData.append('logo', logoFile)
    imageFiles.forEach((file) => {
      formData.append('images', file)
    })

    try {
      // Connect to local FastAPI backend
      const response = await fetch('http://localhost:8000/api/process', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      // Handle the zip file download
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = 'processed_images.zip'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)
    } catch (error) {
      console.error('Error processing images:', error)
      alert('Failed to process images. Start the backend server.')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <>
      <h1>Overlay Engine</h1>
      <p className="subtitle">Batch process your images with AI-powered detection</p>

      <div className="glass-panel">

        {/* Logo Upload Section */}
        <div className="upload-section">
          <h3>1. Select Logo Image</h3>
          <label className="upload-label">
            <div className={`upload-box ${logoFile ? 'has-file' : ''}`}>
              <div className="upload-icon">✦</div>
              {logoFile ? (
                <span className="file-info">{logoFile.name}</span>
              ) : (
                <span>Tap to choose a Logo</span>
              )}
            </div>
            <input
              type="file"
              accept="image/*"
              onChange={handleLogoChange}
            />
          </label>
        </div>

        {/* Multiple Images Upload Section */}
        <div className="upload-section">
          <h3>2. Select Target Images (100+)</h3>
          <label className="upload-label">
            <div className={`upload-box ${imageFiles.length > 0 ? 'has-file' : ''}`}>
              <div className="upload-icon">📸</div>
              {imageFiles.length > 0 ? (
                <span className="file-info">{imageFiles.length} images selected</span>
              ) : (
                <span>Tap to choose images from gallery</span>
              )}
            </div>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleImagesChange}
            />
          </label>
        </div>

        {/* Process Button */}
        {!isProcessing ? (
          <button
            className="process-button"
            onClick={handleProcess}
            disabled={!logoFile || imageFiles.length === 0}
          >
            Overlay & Download ZIP
          </button>
        ) : (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Processing {imageFiles.length} images... sit tight!</p>
          </div>
        )}
      </div>
    </>
  )
}

export default App
