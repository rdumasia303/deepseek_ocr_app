import { motion } from 'framer-motion'
import { FileText, Eye, Search, Wand2 } from 'lucide-react'
import { useTranslation } from 'react-i18next';

const modes = [
  { id: 'plain_ocr', name: 'Plain OCR', icon: FileText, color: 'from-blue-500 to-cyan-500', desc: 'Extract raw text', needsInput: false },
  { id: 'describe', name: 'Describe', icon: Eye, color: 'from-violet-500 to-purple-500', desc: 'Image description', needsInput: false },
  { id: 'find_ref', name: 'Find', icon: Search, color: 'from-yellow-500 to-orange-500', desc: 'Locate specific terms', needsInput: 'findTerm' },
  { id: 'freeform', name: 'Freeform', icon: Wand2, color: 'from-fuchsia-500 to-pink-500', desc: 'Custom prompt', needsInput: 'prompt' },
]

export default function ModeSelector({ 
  mode, 
  onModeChange, 
  prompt, 
  onPromptChange,
  findTerm,
  onFindTermChange
}) {
  const selectedMode = modes.find(m => m.id === mode)
  const needsInput = selectedMode?.needsInput
  const { t } = useTranslation();
  

  return (
    <div className="glass p-4 rounded-2xl space-y-3">
      <h3 className="text-sm font-semibold text-gray-200">{t('mode')}</h3>

      <div className="grid grid-cols-4 gap-2">
        {modes.map((m) => {
          const Icon = m.icon
          const isSelected = mode === m.id
          
          return (
            <motion.button
              key={m.id}
              onClick={() => onModeChange(m.id)}
              className={`
                relative p-2 rounded-xl text-center transition-all
                ${isSelected 
                  ? 'glass border-white/20 shadow-lg' 
                  : 'bg-white/5 border border-white/10 hover:border-white/20'
                }
              `}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {isSelected && (
                <motion.div
                  layoutId="selected-mode"
                  className={`absolute inset-0 bg-gradient-to-br ${m.color} opacity-10 rounded-xl`}
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              
              <div className="relative space-y-1">
                <div className={`
                  w-8 h-8 mx-auto rounded-lg flex items-center justify-center
                  ${isSelected 
                    ? `bg-gradient-to-br ${m.color}` 
                    : 'bg-white/10'
                  }
                `}>
                  <Icon className="w-4 h-4" />
                </div>
                <p className={`text-xs font-medium ${isSelected ? 'text-white' : 'text-gray-300'}`}>
                  {t(m.id)}
                </p>
              </div>
            </motion.button>
          )
        })}
      </div>

      {needsInput === 'findTerm' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          <input
            type="text"
            value={findTerm}
            onChange={(e) => onFindTermChange(e.target.value)}
            placeholder={t('enter_find_term')}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-purple-500 transition-colors"
          />
        </motion.div>
      )}

      {needsInput === 'prompt' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          <textarea
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            placeholder={t('enter_custom_prompt')}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-purple-500 transition-colors resize-none"
            rows={2}
          />
        </motion.div>
      )}
    </div>
  )
}
