/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{ts,tsx,html}"],
  theme: {
    extend: {
      colors: {
        stellar: {
          50: "#fef7ee",
          100: "#fdedd3",
          200: "#fad7a5",
          300: "#f6b96d",
          400: "#f19132",
          500: "#ee750f",
          600: "#df5b09",
          700: "#b9430b",
          800: "#933510",
          900: "#772e10",
        },
      },
    },
  },
  plugins: [],
};
