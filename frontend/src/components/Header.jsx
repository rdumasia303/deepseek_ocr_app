import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Languages, Sun, Moon } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const Header = () => {
  const { t, i18n } = useTranslation();
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [theme, setTheme] = useState('light');

  const languages = [
    { code: 'zh', name: '中文', flag: '🇨🇳' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
  ];

  const currentLang = languages.find(lang => lang.code === i18n.language) || languages[0];

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    document.documentElement.classList.toggle('dark', savedTheme === 'dark');
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  const handleLanguageChange = (code) => {
    i18n.changeLanguage(code);
    setLangDropdownOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 glass border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo & Title */}
          <motion.div 
            className="flex items-center gap-3"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-xl blur-lg opacity-75" />
              <div className="relative bg-gradient-to-br from-purple-600 to-cyan-500 p-2 rounded-xl">
                <Sparkles className="w-6 h-6" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">DeepSeek OCR</h1>
              <p className="text-xs text-gray-400">{t('nextGenVisionAI')}</p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            {/* Theme Switch */}
            <button
              onClick={toggleTheme}
              className="p-2.5 rounded-lg bg-white/5 hover:bg-white/10 transition-all border border-white/10 group"
            >
              {theme === 'light' ? (
                <Sun className="w-5 h-5 text-purple-400 group-hover:text-purple-300 transition-colors" />
              ) : (
                <Moon className="w-5 h-5 text-cyan-400 group-hover:text-cyan-300 transition-colors" />
              )}
            </button>

            {/* Language Switch */}
            <div className="relative">
              <button
                onClick={() => setLangDropdownOpen(!langDropdownOpen)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-all border border-white/10"
              >
                <Languages className="w-4 h-4" />
                <span className="text-sm font-medium">{currentLang.flag} {currentLang.name}</span>
              </button>

              {langDropdownOpen && (
                <div className="absolute right-0 mt-2 w-40 glass border border-white/10 rounded-lg overflow-hidden shadow-xl">
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => handleLanguageChange(lang.code)}
                      className={`w-full flex items-center gap-2 px-4 py-2 text-sm transition-all ${
                        i18n.language === lang.code
                          ? 'bg-gradient-to-r from-purple-500/20 to-cyan-500/20 text-white'
                          : 'text-gray-300 hover:bg-white/5'
                      }`}
                    >
                      <span>{lang.flag}</span>
                      <span>{lang.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </header>
  );
};

export default Header;