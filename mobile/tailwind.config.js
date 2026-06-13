/** @type {import('tailwindcss').Config} */
// The "Bright Trail" palette + Fraunces/Inter type, mirroring the web tokens
// (see ../docs/design/design-system.md). Keep these in sync with the web.
module.exports = {
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./src/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        primary: "#E84A27",
        "primary-dark": "#C73C1E",
        accent: "#F6A623",
        "accent-dark": "#D98911",
        "wagon-wood": "#6F4A2E",
        sage: "#7E9466",
        base: "#FCF4E8",
        surface: "#FFFFFF",
        ink: "#2B2118",
        "ink-muted": "#6B5D50",
        border: "#EADFCB",
        "status-here": "#2E7D54",
        "status-soon": "#F2A900",
        "status-soon-strong": "#8A5300",
        "status-away": "#9A8C7D",
        error: "#D7382B",
      },
      fontFamily: {
        display: ["Fraunces_700Bold"],
        "display-semibold": ["Fraunces_600SemiBold"],
        sans: ["Inter_400Regular"],
        "sans-medium": ["Inter_500Medium"],
        "sans-semibold": ["Inter_600SemiBold"],
      },
    },
  },
  plugins: [],
};
