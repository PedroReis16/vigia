import { definePreset } from '@openng/optimus-ui-themes';
import Aura from '@openng/optimus-ui-themes/aura';

export const VigiaTheme = definePreset(Aura, {
  semantic: {
    colorScheme: {
      light: {
        primary: {
          '50': '#F1F2FA',
          '100': '#E1E4F5',
          '200': '#C3C9EB',
          '300': '#A4AEE0',
          '400': '#6879C1',
          '500': '#111D63', // base
          '600': '#0F1957',
          '700': '#0D154B',
          '800': '#0B113F',
          '900': '#080D33',
          '950': '#050A26',
        },
      },
      dark: {
        primary: {
          '50': '#eff9ff',
          '100': '#def2ff',
          '200': '#b6e7ff',
          '300': '#75d7ff',
          '400': '#2cc3ff',
          '500': '#00b1ff',
          '600': '#0089d4',
          '700': '#006dab',
          '800': '#005c8d',
          '900': '#064d74',
          '950': '#04304d',
        },
      },
    },
  },
});
