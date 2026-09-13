/**
 * SANJEEVNI Design System — Typography Tokens
 * 
 * Clean, readable system fonts matching Inter / SF Pro style.
 * Accessible contrast and comfortable mobile line heights.
 */

export const typography = {
  // Font Sizes
  size: {
    xs: 11,
    sm: 13,
    base: 15,
    md: 17,
    lg: 20,
    xl: 24,
    xxl: 30,
    display: 38,
  },

  // Font Weights
  weight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },

  // Line Heights
  lineHeight: {
    tight: 1.2,
    normal: 1.4,
    relaxed: 1.6,
  },
} as const;
