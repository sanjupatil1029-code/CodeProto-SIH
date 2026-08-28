/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#243B7A",
          dark: "#182A5C",
          light: "#33499A",
        },
        indigo: {
          DEFAULT: "#4F46A5",
          light: "#6D63C4",
        },
        saffron: {
          DEFAULT: "#E8892D",
          dark: "#C96F1B",
          light: "#F5A855",
        },
        mist: "#F6F8FC",
        lavender: "#E9E7FF",
        success: {
          DEFAULT: "#16805C",
          light: "#DDF3EA",
        },
        warn: {
          DEFAULT: "#B45309",
          light: "#FEF3E2",
        },
        danger: {
          DEFAULT: "#C0392B",
          light: "#FDECEA",
        },
        ink: "#151B33",
        slate: {
          soft: "#5B6482",
        },
      },
      fontFamily: {
        display: ["'Sora'", "system-ui", "sans-serif"],
        body: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(21,27,51,0.04), 0 8px 24px -8px rgba(36,59,122,0.12)",
        cardHover: "0 4px 10px rgba(21,27,51,0.06), 0 16px 32px -12px rgba(36,59,122,0.18)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at 1px 1px, rgba(36,59,122,0.08) 1px, transparent 0)",
      },
    },
  },
  plugins: [],
};
