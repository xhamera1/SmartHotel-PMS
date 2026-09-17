import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import { IconButton, MenuItem, TextField, Tooltip } from '@mui/material'
import { useI18n } from '@/shared/i18n/useI18n'
import type { AppLocale } from '@/shared/i18n/messages'
import { useThemeMode } from '@/shared/theme/useThemeMode'

type AppChromeControlsProps = {
  /** Use inherit on primary AppBar, primary on transparent bars. */
  tone?: 'inherit' | 'primary'
}

export function AppChromeControls({ tone = 'primary' }: AppChromeControlsProps) {
  const { locale, setLocale, t } = useI18n()
  const { mode, toggleMode } = useThemeMode()
  const selectColor = tone === 'inherit' ? 'inherit' : 'primary'

  return (
    <>
      <TextField
        select
        size="small"
        label={t.common.language}
        value={locale}
        onChange={(e) => setLocale(e.target.value as AppLocale)}
        sx={{
          minWidth: 110,
          '& .MuiInputBase-root': { color: tone === 'inherit' ? 'inherit' : undefined },
          '& .MuiInputLabel-root': { color: tone === 'inherit' ? 'inherit' : undefined },
          '& .MuiOutlinedInput-notchedOutline':
            tone === 'inherit' ? { borderColor: 'rgba(255,255,255,0.4)' } : undefined,
        }}
        slotProps={{
          inputLabel: { shrink: true },
          select: { 'aria-label': t.common.language },
        }}
        data-testid="locale-select"
      >
        <MenuItem value="pl">{t.common.polish}</MenuItem>
        <MenuItem value="en">{t.common.english}</MenuItem>
      </TextField>
      <Tooltip title={mode === 'light' ? t.common.darkMode : t.common.lightMode}>
        <IconButton
          color={selectColor}
          onClick={toggleMode}
          aria-label={mode === 'light' ? t.common.darkMode : t.common.lightMode}
          data-testid="theme-mode-toggle"
        >
          {mode === 'light' ? <DarkModeOutlinedIcon /> : <LightModeOutlinedIcon />}
        </IconButton>
      </Tooltip>
    </>
  )
}
