/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/app/index.html", "./src/app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0b0d12",
          soft: "#12151c",
          line: "#1e2230",
        },
        fog: "#8a92a6",
        bone: "#f4f4ef",
        accent: "#c9a24b",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
