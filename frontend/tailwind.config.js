/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          bg: "#0b0f1a",     // fundal închis
          card: "#101729",   // card
          text: "#e6eefb",   // text principal
          sub: "#9fb0d1"     // text secundar
        },
        brand: {
          cyan: "#22d3ee",
          fuchsia: "#d946ef",
          emerald: "#34d399",
          yellow: "#fde047"
        }
      },
      boxShadow: {
        glow: "0 10px 30px rgba(34, 211, 238, 0.25)",     // cyan glow
        card: "0 10px 30px rgba(2, 6, 23, 0.35)"
      },
      borderRadius: {
        xl2: "1.25rem"
      }
    },
  },
  plugins: [],
};
