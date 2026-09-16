import { createTheme } from '@mui/material/styles'

/**
 * Compact hotel-ops theme: deep teal + warm sand (not purple / cream-terracotta defaults).
 */
export const appTheme = createTheme({
  cssVariables: true,
  palette: {
    mode: 'light',
    primary: {
      main: '#0F5C5C',
      dark: '#0A3F3F',
      light: '#2A7A7A',
      contrastText: '#F7F4EF',
    },
    secondary: {
      main: '#C45C26',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F3F1EC',
      paper: '#FFFcf7',
    },
    text: {
      primary: '#1C2424',
      secondary: '#4A5757',
    },
  },
  typography: {
    fontFamily: '"Source Sans 3", "Segoe UI", Helvetica, Arial, sans-serif',
    h1: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
    h2: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
    h3: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
    h4: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 10 },
})
