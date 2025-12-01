/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#8aaef8',
          dark: '#566cd3',
        },
        gradientStart: '#9ec2fa',
        gradientEnd: '#6777d2',
      },
      borderRadius: {
        lg: '12px',
      },
    },
  },
  plugins: [],
};