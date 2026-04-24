---
name: Noir Premium
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#d0c5af'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#99907c'
  outline-variant: '#4d4635'
  surface-tint: '#e9c349'
  primary: '#f2ca50'
  on-primary: '#3c2f00'
  primary-container: '#d4af37'
  on-primary-container: '#554300'
  inverse-primary: '#735c00'
  secondary: '#c2c6d8'
  on-secondary: '#2b303e'
  secondary-container: '#424655'
  on-secondary-container: '#b0b5c6'
  tertiary: '#ffbfb8'
  on-tertiary: '#690007'
  tertiary-container: '#ff968c'
  on-tertiary-container: '#90000e'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe088'
  primary-fixed-dim: '#e9c349'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#574500'
  secondary-fixed: '#dee2f4'
  secondary-fixed-dim: '#c2c6d8'
  on-secondary-fixed: '#161b28'
  on-secondary-fixed-variant: '#424655'
  tertiary-fixed: '#ffdad6'
  tertiary-fixed-dim: '#ffb4ac'
  on-tertiary-fixed: '#410003'
  on-tertiary-fixed-variant: '#92030f'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-xl:
    fontFamily: Noto Serif
    fontSize: 64px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Noto Serif
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Noto Serif
    fontSize: 32px
    fontWeight: '500'
    lineHeight: '1.3'
    letterSpacing: 0em
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0.01em
  body-md:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0.01em
  label-md:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Manrope
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.03em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
---

## Brand & Style

The brand personality of this design system is one of exclusivity, dramatic flair, and understated luxury. It is designed for an audience that values the "experience" of cinema as much as the film itself—connoisseurs who appreciate high-end aesthetics and a frictionless, immersive journey.

The design style is a sophisticated blend of **Glassmorphism** and **High-Contrast Minimalism**. It uses deep, dark layers to create a sense of vast architectural space, reminiscent of a dimly lit luxury theater lobby. Visual interest is driven by light play—using translucent surfaces, subtle gold glows, and sharp typography to guide the user’s eye through the darkness. The emotional response should be one of "hushed excitement" and "prestige."

## Colors

This design system operates exclusively in a dark mode environment to maintain a cinematic atmosphere. 

- **Primary (Warm Amber/Gold):** Used sparingly for primary calls to action, active states, and premium signifiers. It represents the "spotlight."
- **Secondary (Deep Navy):** Acts as a subtle cooling agent against the deep charcoal, used for secondary containers and surface elevations to provide depth.
- **Neutral (Deep Charcoal):** The foundation of the system. It provides the infinite canvas that allows content and imagery to pop.
- **Accent (Restrained Red):** Reserved for critical alerts, error states, or specific "now playing" highlights. It is a deep, velvety red that maintains the noir aesthetic without appearing jarring.

## Typography

The typographic strategy relies on the tension between the classic and the contemporary. 

**Noto Serif** is used for all major headings and editorial moments. Its refined serifs evoke traditional film credits and literary prestige. High-level headlines should use tighter letter spacing to feel more "locked in" and cinematic.

**Manrope** provides a clean, functional counterpoint for all UI elements, navigation, and body copy. It ensures high legibility against dark backgrounds. Labels and metadata should leverage the medium and semi-bold weights of Manrope, often using slight tracking (letter spacing) and uppercase styling for a sophisticated, architectural feel.

## Layout & Spacing

The design system utilizes a **Fixed Grid** model for desktop to create a centered, theatrical viewing experience, while transitioning to a fluid model for mobile devices. 

A 12-column grid is standard for desktop layouts, with generous margins to allow the content to "breathe" like a gallery piece. Spacing is governed by a strict 8px base unit. Larger increments (48px, 64px, 80px) are encouraged between major sections to prevent the UI from feeling cluttered, reinforcing the premium, high-end nature of the service.

## Elevation & Depth

Depth is achieved through **Glassmorphism** and layering rather than traditional drop shadows. Surfaces closer to the user are more translucent and have a lighter background blur (Backdrop Filter: 12px to 20px).

- **Surface 0 (Base):** Deep Charcoal (#121212).
- **Surface 1 (Cards/Panels):** Semi-transparent Deep Navy (#1A1F2C at 60% opacity) with a subtle 1px border (#FFFFFF at 10% opacity).
- **Overlays:** High blur with a very subtle inner glow in Gold (#D4AF37 at 5% opacity) to suggest a light source from above.

Shadows, when used, are extremely soft and tinted with the Secondary Navy color to avoid a "dirty" look on the dark background.

## Shapes

The shape language is "Soft" yet structured. A primary radius of 4px (0.25rem) is used for buttons and small components, providing a sharp, professional edge. Larger cards and containers use an 8px (0.5rem) or 12px (0.75rem) radius to feel more approachable. 

The goal is to avoid overly rounded or "bubbly" shapes, which can detract from the serious, luxury aesthetic. Elements should feel like finely cut stones or polished glass.

## Components

### Buttons
- **Primary:** High-contrast with a subtle linear gradient (Amber to Deep Gold). Text is black or very dark charcoal for maximum legibility.
- **Secondary:** Ghost style with a 1px Gold border and transparent background.
- **Tertiary:** Text-only with an underline effect on hover.

### Cards
Cards are the centerpiece of the "Glassy" look. They must feature a `backdrop-filter: blur()` and a very thin, low-opacity border. Images within cards should have a subtle vignette to blend into the dark UI.

### Status Badges
Badges use the Restrained Red for "Sold Out" or "Alert" states and the Gold for "Premium" or "Featured" states. They are small, pill-shaped, and use the `label-sm` typography.

### Seat Map
- **Available:** Subtle outline in Navy with no fill.
- **Selected:** Solid Gold fill with a slight outer glow.
- **Occupied:** Low-opacity Charcoal fill (virtually blending into the background).
- **Premium:** Thicker Gold outline with a subtle interior gradient.
- **Accessible:** Standard icon indicator, rendered in a neutral off-white for clarity.

### Input Fields
Inputs are dark with 1px borders that "illuminate" to Gold when focused. The cursor should also be themed in Gold.