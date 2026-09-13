/**
 * SANJEEVNI Design System — Color Tokens
 * 
 * Calm, trustworthy, clinical wellness palette.
 * Primary: Soft Turquoise / Deep Teal
 * Surface: Pure White / Cool Off-White with subtle borders
 * Text: Deep Teal / Charcoal Slate
 * NO-MOCK-DATA honest status colors
 */

export const colors = {
  // Brand Teal Accents
  primary: '#0D9488',          // Teal 600 - Main interactive accent
  primaryHover: '#0F766E',     // Teal 700 - Pressed state
  primaryLight: '#14B8A6',     // Teal 500 - Secondary highlight
  primaryDark: '#115E59',      // Teal 800 - Deep brand accents
  primaryTint: '#F0FDFA',      // Teal 50  - Card/container tint
  primarySubtle: '#CCFBF1',    // Teal 100 - Badges & ring background

  // Background & Surface
  background: '#F8FAFC',       // Slate 50  - Main screen background
  surface: '#FFFFFF',          // Pure White - Primary cards
  surfaceMuted: '#F1F5F9',     // Slate 100 - Secondary surfaces
  surfaceSubtle: '#F8FAFC',    // Slate 50  - Input backgrounds

  // Borders & Dividers
  border: '#E2E8F0',           // Slate 200 - Card borders
  borderSubtle: '#F1F5F9',     // Slate 100 - Light dividers
  borderTeal: '#99F6E4',       // Teal 200  - Focused / active borders

  // Typography
  textPrimary: '#0F172A',      // Slate 900 - Headings & key metrics
  textSecondary: '#475569',    // Slate 600 - Body & descriptions
  textMuted: '#94A3B8',        // Slate 400 - Secondary labels & placeholders
  textTeal: '#0F766E',         // Teal 700  - Emphasized wellness text
  textOnPrimary: '#FFFFFF',    // White text on primary buttons

  // Physiological Stress Level Badges
  stressLow: '#0D9488',        // Teal 600  - Baseline / Low Stress
  stressLowBg: '#CCFBF1',      // Teal 100
  stressModerate: '#F59E0B',   // Amber 500 - Moderate Stress
  stressModerateBg: '#FEF3C7', // Amber 100
  stressHigh: '#E11D48',       // Rose 600  - High Stress
  stressHighBg: '#FFE4E6',     // Rose 100

  // Hardware & Data Status
  statusConnected: '#10B981',     // Emerald 500
  statusConnectedBg: '#D1FAE5',
  statusDisconnected: '#EF4444',  // Red 500
  statusDisconnectedBg: '#FEE2E2',
  statusWaiting: '#F59E0B',        // Amber 500
  statusWaitingBg: '#FEF3C7',
  statusNoData: '#94A3B8',         // Slate 400
  statusNoDataBg: '#F1F5F9',

  // Wellness Category Accents
  yogaAccent: '#0284C7',       // Sky 600
  yogaBg: '#E0F2FE',
  breathingAccent: '#0D9488',  // Teal 600
  breathingBg: '#CCFBF1',
  nutritionAccent: '#16A34A',  // Green 600
  nutritionBg: '#DCFCE7',
  aiAccent: '#6366F1',         // Indigo 500
  aiBg: '#EEF2FF',
} as const;

export type ColorToken = keyof typeof colors;
