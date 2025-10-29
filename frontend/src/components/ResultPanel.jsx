import { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Copy, Download, Sparkles, Loader2, CheckCircle2, ChevronDown } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useTranslation } from 'react-i18next';

export default function ResultPanel({ result, loading, imagePreview, onCopy, onDownload }) {
  const { t } = useTranslation();
  const canvasRef = useRef(null)
  const imgRef = useRef(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)

  // Check if text looks like HTML (model outputs HTML, not markdown)
  const isHTML = result?.text && (
    result.text.includes('<table') || 
    result.text.includes('<tr>') || 
    result.text.includes('<td>') ||
    result.text.includes('<div') ||
    result.text.includes('<p>') ||
    result.text.includes('<h1') ||
    result.text.includes('<h2')
  )

  // Also check if it looks like markdown (for backwards compatibility)
  const isMarkdown = result?.text && !isHTML && (
    result.text.includes('##') || 
    result.text.includes('**') || 
    result.text.includes('```') ||
    result.text.includes('- ') ||
    result.text.includes('|')
  )

  // Draw boxes function
  const drawBoxes = useCallback(() => {
    if (!result?.boxes?.length || !canvasRef.current || !imgRef.current) {
      console.log('❌ Cannot draw - missing:', {
        hasBoxes: !!result?.boxes?.length,
        hasCanvas: !!canvasRef.current,
        hasImgRef: !!imgRef.current
      })
      return
    }

    console.log('🎨 Drawing boxes:', result.boxes)

    const img = imgRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    
    console.log('📐 Image dimensions:', {
      displayWidth: img.offsetWidth,
      displayHeight: img.offsetHeight,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      imageDims: result.image_dims
    })

    // Set canvas size to match displayed image
    canvas.width = img.offsetWidth
    canvas.height = img.offsetHeight
    
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // Calculate scale factors
    const scaleX = img.offsetWidth / (result.image_dims?.w || img.naturalWidth)
    const scaleY = img.offsetHeight / (result.image_dims?.h || img.naturalHeight)
    
    console.log('📏 Scale factors:', { scaleX, scaleY })
    
    // Draw boxes
    result.boxes.forEach((box, idx) => {
      const [x1, y1, x2, y2] = box.box
      const colors = [
        '#00ff00', '#00ffff', '#ff00ff', '#ffff00', '#ff0066'
      ]
      const color = colors[idx % colors.length]
      
      // Scale coordinates
      const sx = x1 * scaleX
      const sy = y1 * scaleY
      const sw = (x2 - x1) * scaleX
      const sh = (y2 - y1) * scaleY
      
      console.log(`📦 Box ${idx} (${box.label}):`, {
        original: [x1, y1, x2, y2],
        scaled: [sx, sy, sx + sw, sy + sh],
        dimensions: { width: sw, height: sh }
      })
      
      // Draw semi-transparent fill
      ctx.fillStyle = color + '33'
      ctx.fillRect(sx, sy, sw, sh)
      
      // Draw thick neon border
      ctx.strokeStyle = color
      ctx.lineWidth = 4
      ctx.shadowColor = color
      ctx.shadowBlur = 10
      ctx.strokeRect(sx, sy, sw, sh)
      ctx.shadowBlur = 0
      
      // Label background
      if (box.label) {
        ctx.font = 'bold 14px Inter'
        const metrics = ctx.measureText(box.label)
        const padding = 8
        const labelHeight = 24
        
        ctx.fillStyle = color
        ctx.fillRect(sx, sy - labelHeight, metrics.width + padding * 2, labelHeight)
        
        // Label text
        ctx.fillStyle = '#000'
        ctx.fillText(box.label, sx + padding, sy - 7)
      }
    })
    
    console.log('✅ Finished drawing', result.boxes.length, 'boxes')
  }, [result])

  // Trigger drawing when image loads
  useEffect(() => {
    if (imageLoaded && result?.boxes?.length) {
      console.log('🚀 Image loaded, drawing boxes now')
      drawBoxes()
    }
  }, [imageLoaded, result, drawBoxes])

  // Reset imageLoaded when result changes
  useEffect(() => {
    setImageLoaded(false)
  }, [result])

  // Redraw on window resize
  useEffect(() => {
    if (!imageLoaded || !result?.boxes?.length) return
    
    const handleResize = () => {
      console.log('📐 Window resized, redrawing')
      drawBoxes()
    }
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [imageLoaded, result, drawBoxes])

  return (
    <div className="glass p-6 rounded-2xl space-y-4 h-full">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-400" />
          <h3 className="font-semibold text-gray-200">{t('results')}</h3>
        </div>
        
        {result && (
          <div className="flex gap-2">
            <motion.button
              onClick={onCopy}
              className="glass glass-hover p-2 rounded-lg"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              title={t('copy_to_clipboard')}
            >
              <Copy className="w-4 h-4" />
            </motion.button>
            <motion.button
              onClick={onDownload}
              className="glass glass-hover p-2 rounded-lg"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              title={t('download')}
            >
              <Download className="w-4 h-4" />
            </motion.button>
          </div>
        )}
      </div>

      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-20 space-y-4"
          >
            <div className="relative">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full"
              />
              <Loader2 className="w-8 h-8 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-purple-400" />
            </div>
            <p className="text-sm text-gray-400 animate-pulse">
              {t('processing_image')}
            </p>
          </motion.div>
        ) : result ? (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {/* Preview with boxes */}
            {imagePreview && result.boxes && result.boxes.length > 0 && (
              <div className="relative rounded-xl overflow-hidden border border-white/10 bg-black">
                <img 
                  ref={imgRef}
                  src={imagePreview} 
                  alt="Result" 
                  className="w-full block" 
                  onLoad={() => {
                    console.log('🖼️ Image loaded, triggering draw')
                    setImageLoaded(true)
                  }}
                />
                <canvas 
                  ref={canvasRef}
                  className="absolute top-0 left-0 w-full h-full pointer-events-none"
                  style={{ display: 'block' }}
                />
              </div>
            )}

            {/* Text result */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 max-h-96 overflow-y-auto">
              {isHTML ? (
                <div 
                  className="prose prose-invert prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: result.text }}
                  style={{
                    color: '#e5e7eb',
                  }}
                />
              ) : isMarkdown ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{result.text}</ReactMarkdown>
                </div>
              ) : (
                <pre className="text-sm text-gray-200 whitespace-pre-wrap font-mono">
                  {result.text}
                </pre>
              )}
            </div>

            {/* Raw Response Viewer */}
            {result.raw_text && (
              <details className="glass rounded-xl overflow-hidden">
                <summary className="px-4 py-3 cursor-pointer flex items-center justify-between hover:bg-white/5 transition-colors">
                  <span className="text-sm font-medium text-gray-300">🔍 {t('raw_model_response')}</span>
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                </summary>
                <div className="px-4 py-3 border-t border-white/10 space-y-2">
                  <p className="text-xs text-gray-400 mb-2">{t('raw_output_description')}</p>
                  <div className="bg-black/30 rounded-lg p-3 max-h-64 overflow-y-auto">
                    <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap break-words select-all">
                      {result.raw_text}
                    </pre>
                  </div>
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => navigator.clipboard.writeText(result.raw_text)}
                      className="text-xs px-3 py-1 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
                    >
                      {t('copy_raw')}
                    </button>
                    <span className="text-xs text-gray-500 py-1">
                      {result.raw_text.length} {t('characters')}
                    </span>
                  </div>
                </div>
              </details>
            )}

            {/* Advanced Settings Dropdown */}
            <details className="glass rounded-xl overflow-hidden">
              <summary className="px-4 py-3 cursor-pointer flex items-center justify-between hover:bg-white/5 transition-colors">
                <span className="text-sm font-medium text-gray-300">⚙️ {t('metadata_and_debug_info')}</span>
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </summary>
              <div className="px-4 py-3 border-t border-white/10 space-y-3">
                {result.metadata && (
                  <div>
                    <p className="text-xs text-gray-400 mb-2">{t('processing_metadata')}</p>
                    <pre className="text-xs text-gray-500 whitespace-pre-wrap">
                      {JSON.stringify(result.metadata, null, 2)}
                    </pre>
                  </div>
                )}
                {result.boxes?.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400 mb-2">{t('parsed_bounding_boxes')} ({result.boxes.length})</p>
                    <div className="bg-black/30 rounded-lg p-2 space-y-1 max-h-32 overflow-y-auto">
                      {result.boxes.map((box, idx) => (
                        <div key={idx} className="text-xs font-mono">
                          <span className="text-cyan-400">{t('box')} {idx + 1}:</span>{' '}
                          <span className="text-purple-400">{box.label}</span>{' '}
                          <span className="text-gray-500">
                            [{box.box.map(n => Math.round(n)).join(', ')}]
                          </span>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      {t('coordinates_scaled')}
                    </p>
                  </div>
                )}
              </div>
            </details>

            {/* Success indicator */}
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="flex items-center justify-center gap-2 text-green-400"
            >
              <CheckCircle2 className="w-5 h-5" />
              <span className="text-sm font-medium">{t('processing_complete')}</span>
            </motion.div>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-20 space-y-4"
          >
            <div className="relative">
              <motion.div
                animate={{ 
                  scale: [1, 1.2, 1],
                  opacity: [0.5, 0.8, 0.5]
                }}
                transition={{ duration: 3, repeat: Infinity }}
                className="w-20 h-20 bg-purple-500/20 rounded-full blur-xl"
              />
              <Sparkles className="w-10 h-10 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-purple-400" />
            </div>
            <div className="text-center">
              <p className="text-lg font-medium text-gray-300">
                {t('ready_to_process')}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {t('upload_and_analyze')}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
