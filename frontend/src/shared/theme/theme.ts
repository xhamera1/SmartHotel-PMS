import { createTheme, type Theme } from '@mui/material/styles'

const sharedTypography = {
  fontFamily: '"Source Sans 3", "Segoe UI", Helvetica, Arial, sans-serif',
  h1: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
  h2: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
  h3: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
  h4: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
  button: { textTransform: 'none' as const, fontWeight: 600 },
}

/**
 * Compact hotel-ops theme: deep teal + warm sand (not purple / cream-terracotta defaults).
 */
export function createAppTheme(mode: 'light' | 'dark'): Theme {
  const isDark = mode === 'dark'
  return createTheme({
    cssVariables: true,
    palette: {
      mode,
      primary: {
        main: isDark ? '#3D9B9B' : '#0F5C5C',
        dark: isDark ? '#2A7A7A' : '#0A3F3F',
        light: isDark ? '#6BBDBD' : '#2A7A7A',
        contrastText: isDark ? '#0B1515' : '#F7F4EF',
      },
      secondary: {
        main: isDark ? '#E07A45' : '#C45C26',
        contrastText: '#FFFFFF',
      },
      background: {
        default: isDark ? '#121A1A' : '#F3F1EC',
        paper: isDark ? '#1A2424' : '#FFFcf7',
      },
      text: {
        primary: isDark ? '#E8EEF0' : '#1C2424',
        secondary: isDark ? '#A8B5B5' : '#4A5757',
      },
    },
    typography: sharedTypography,
    shape: { borderRadius: 10 },
    components: {
      MuiButtonBase: {
        defaultProps: { disableRipple: false },
        styleOverrides: {
          root: {
            '&:focus-visible': {
              outline: `3px solid ${isDark ? '#E07A45' : '#C45C26'}`,
              outlineOffset: 2,
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            '&:focus-visible': {
              outline: `3px solid ${isDark ? '#E07A45' : '#C45C26'}`,
              outlineOffset: 2,
            },
          },
        },
      },
    },
  })
}
