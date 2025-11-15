import { useCallback } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { Upload, Image as ImageIcon, X, FileText } from 'lucide-react'

export default function ImageUpload({ onImageSelect, preview, fileType = 'image' }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles?.[0]) {
      onImageSelect(acceptedFiles[0])
    }
  }, [onImageSelect])

  const isPDF = fileType === 'pdf'

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: isPDF ? {
      'application/pdf': ['.pdf']
    } : {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp']
    },
    multiple: false
  })

  return (
    <div className="glass p-6 rounded-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-200">
          {isPDF ? 'Upload PDF' : 'Upload Image'}
        </h3>
        {isPDF ? (
          <FileText className="w-5 h-5 text-purple-400" />
        ) : (
          <ImageIcon className="w-5 h-5 text-purple-400" />
        )}
      </div>

      {!preview ? (
        <motion.div
          {...getRootProps()}
          className={`
            relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
            transition-all duration-300
            ${isDragActive 
              ? 'border-purple-500 bg-purple-500/10' 
              : 'border-white/20 bg-white/5 hover:border-white/40 hover:bg-white/10'
            }
          `}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <input {...getInputProps()} />
          
          <div className="space-y-4">
            <motion.div
              animate={{ 
                y: isDragActive ? -10 : 0,
                scale: isDragActive ? 1.1 : 1 
              }}
              className="flex justify-center"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-2xl blur-xl opacity-50" />
                <div className="relative bg-gradient-to-br from-purple-600 to-cyan-500 p-4 rounded-2xl">
                  <Upload className="w-8 h-8" />
                </div>
              </div>
            </motion.div>
            
            <div>
              <p className="text-lg font-medium text-gray-200">
                {isDragActive
                  ? 'Drop it like it\'s hot! 🔥'
                  : isPDF
                    ? 'Drag & drop your PDF'
                    : 'Drag & drop your image'
                }
              </p>
              <p className="text-sm text-gray-400 mt-1">
                {isPDF
                  ? 'or click to browse • PDF files up to 100MB'
                  : 'or click to browse • PNG, JPG, WEBP up to 10MB'
                }
              </p>
            </div>
          </div>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative group rounded-2xl overflow-hidden"
        >
          {isPDF ? (
            <div className="flex items-center justify-center p-12 bg-white/5 border border-white/10 rounded-2xl">
              <div className="text-center">
                <FileText className="w-16 h-16 mx-auto mb-3 text-purple-400" />
                <p className="text-sm text-gray-300 font-medium">PDF Ready</p>
                <p className="text-xs text-gray-500 mt-1">{preview?.name || 'Document loaded'}</p>
              </div>
            </div>
          ) : (
            <img
              src={preview}
              alt="Preview"
              className="w-full rounded-2xl border border-white/10"
            />
          )}
          <div className="absolute top-3 right-3 flex gap-2">
            <motion.button
              onClick={(e) => {
                e.stopPropagation()
                onImageSelect(null)
              }}
              className="bg-red-500/90 backdrop-blur-sm px-3 py-2 rounded-full opacity-100 hover:bg-red-600 transition-colors flex items-center gap-2 shadow-lg"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              title={isPDF ? "Remove PDF" : "Remove image"}
            >
              <X className="w-4 h-4" />
              <span className="text-sm font-medium">Remove</span>
            </motion.button>
          </div>
        </motion.div>
      )}
    </div>
  )
}
