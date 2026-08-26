import { definePreset } from '@openng/optimus-ui-themes';
import Aura from '@openng/optimus-ui-themes/aura';

/** Primary scale aligned with Flutter `AppColors` (#669CEE). */
const vigiaPrimary = {
  '50': '#F0F5FE',
  '100': '#E0EBFC',
  '200': '#C2D7F9',
  '300': '#A3C3F5',
  '400': '#85AFF2',
  '500': '#669CEE', // base — same as vigia_ui AppColors.primary
  '600': '#527DC0',
  '700': '#3D5E91',
  '800': '#294061',
  '900': '#1A2A42',
  '950': '#0F1826',
};

/**
 * Light surface scale (Aura: 0 = lightest → 950 = darkest).
 * Mapped from Flutter `AppColors.light`.
 */
const lightSurface = {
  '0': '#FFFFFF', // card / content
  '50': '#FFF9F5', // page background
  '100': '#F7F4F0',
  '200': '#E2E7EE', // outlineVariant / primaryContainer
  '300': '#D5DBE4',
  '400': '#9AA3B2', // outline
  '500': '#7A8499', // textSecondary
  '600': '#46526D', // textPrimary
  '700': '#3A455A',
  '800': '#2A3344',
  '900': '#1A1F2A',
  '950': '#12151C',
};

/**
 * Light-only Optimus preset (web matches Flutter `ThemeMode.light`).
 */
export const VigiaTheme = definePreset(Aura, {
  semantic: {
    colorScheme: {
      light: {
        primary: vigiaPrimary,
        surface: lightSurface,
        text: {
          color: '{surface.600}',
          hoverColor: '{surface.700}',
          mutedColor: '{surface.500}',
          hoverMutedColor: '{surface.600}',
        },
        content: {
          background: '{surface.0}',
          hoverBackground: '{surface.50}',
          borderColor: '{surface.200}',
          color: '{text.color}',
          hoverColor: '{text.hover.color}',
        },
        formField: {
          background: '{surface.0}',
          filledBackground: '{surface.200}',
          filledHoverBackground: '{surface.200}',
          filledFocusBackground: '{surface.200}',
          borderColor: '{surface.400}',
          color: '{surface.600}',
        },
      },
    },
  },
});
