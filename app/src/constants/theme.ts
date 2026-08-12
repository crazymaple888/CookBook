import { Platform } from 'react-native';

export const Colors = {
  light: {
    text: '#1f2421',
    background: '#faf8f5',
    backgroundElement: '#f1eee9',
    backgroundSelected: '#e5e0d8',
    textSecondary: '#6d756f',
    primary: '#2f5d50',
    primarySoft: '#e8efe9',
    success: '#4c7a5e',
    warning: '#c99a3d',
    card: '#ffffff',
    border: '#ece8e2',
  },
  dark: {
    text: '#ece9e4',
    background: '#161a18',
    backgroundElement: '#212623',
    backgroundSelected: '#2b322e',
    textSecondary: '#a9b2ac',
    primary: '#4f7f6f',
    primarySoft: '#22352e',
    success: '#5d9a72',
    warning: '#d4ab55',
    card: '#1d211e',
    border: '#2b302d',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
  ios: {
    sans: 'system-ui',
    serif: 'ui-serif',
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    mono: 'monospace',
  },
});

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

export const MaxContentWidth = 800;
