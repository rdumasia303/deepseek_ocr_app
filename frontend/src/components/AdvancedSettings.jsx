import { motion } from 'framer-motion'
import { Sliders } from 'lucide-react'
import { useTranslation } from 'react-i18next';

export default function AdvancedSettings({ settings, onSettingsChange, includeCaption, onIncludeCaptionChange }) {
  const { t } = useTranslation();

  const handleChange = (key, value) => {
    onSettingsChange({
      ...settings,
      [key]: value
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="glass p-6 rounded-2xl space-y-4"
    >
      <div className="flex items-center gap-2">
        <Sliders className="w-5 h-5 text-purple-400" />
        <h3 className="font-semibold text-gray-800 dark:text-gray-200">{t('advanced_settings')}</h3> {/* Adjusted text color for both modes */}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-xs text-gray-600 dark:text-gray-400">{t('base_size')}</label> {/* Adjusted text color */}
          <input
            type="number"
            value={settings.base_size}
            onChange={(e) => handleChange('base_size', parseInt(e.target.value))}
            className="w-full bg-white/5 dark:bg-white/10 border border-white/10 dark:border-white/20 rounded-xl px-3 py-2 text-sm text-gray-900 dark:text-gray-300 focus:outline-none focus:border-purple-500"
          />
        </div>

        <div className="space-y-2">
          <label className="text-xs text-gray-600 dark:text-gray-400">{t('image_size')}</label> {/* Adjusted text color */}
          <input
            type="number"
            value={settings.image_size}
            onChange={(e) => handleChange('image_size', parseInt(e.target.value))}
            className="w-full bg-white/5 dark:bg-white/10 border border-white/10 dark:border-white/20 rounded-xl px-3 py-2 text-sm text-gray-900 dark:text-gray-300 focus:outline-none focus:border-purple-500"
          />
        </div>

        <div className="space-y-2">
          <label className="text-xs text-gray-600 dark:text-gray-400">{t('crop_mode')}</label> {/* Adjusted text color */}
          <select
            value={settings.crop_mode ? 'true' : 'false'}
            onChange={(e) => handleChange('crop_mode', e.target.value === 'true')}
            className="w-full bg-white/5 dark:bg-white/10 border border-white/10 dark:border-white/20 rounded-xl px-3 py-2 text-sm text-gray-900 dark:text-gray-300 focus:outline-none focus:border-purple-500"
          >
            <option value="true">{t('enabled')}</option>
            <option value="false">{t('disabled')}</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="text-xs text-gray-600 dark:text-gray-400">{t('test_compress')}</label> {/* Adjusted text color */}
          <select
            value={settings.test_compress ? 'true' : 'false'}
            onChange={(e) => handleChange('test_compress', e.target.value === 'true')}
            className="w-full bg-white/5 dark:bg-white/10 border border-white/10 dark:border-white/20 rounded-xl px-3 py-2 text-sm text-gray-900 dark:text-gray-300 focus:outline-none focus:border-purple-500"
          >
            <option value="false">{t('disabled')}</option>
            <option value="true">{t('enabled')}</option>
          </select>
        </div>
      </div>

      <div className="pt-2 border-t border-white/10 dark:border-white/20">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={includeCaption}
            onChange={(e) => onIncludeCaptionChange(e.target.checked)}
            className="accent-purple-500"
          />
          <span className="text-sm text-gray-800 dark:text-gray-300">{t('include_image_caption')}</span> {/* Adjusted text color */}
        </label>
      </div>
    </motion.div>
  )
}
