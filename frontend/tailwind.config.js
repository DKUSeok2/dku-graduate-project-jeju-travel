/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // 다크모드 활성화
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 제주도 테마 색상
        jeju: {
          orange: {
            50: '#FFF7ED',
            100: '#FFEDD5',
            200: '#FED7AA',
            300: '#FDBA74',
            400: '#FB923C',  // 메인 감귤색
            500: '#F97316',
            600: '#EA580C',
            700: '#C2410C',
            800: '#9A3412',
            900: '#7C2D12',
          },
          blue: {
            50: '#F0F9FF',
            100: '#E0F2FE',
            200: '#BAE6FD',
            300: '#7DD3FC',
            400: '#38BDF8',
            500: '#0EA5E9',  // 메인 바다색
            600: '#0284C7',
            700: '#0369A1',
            800: '#075985',
            900: '#0C4A6E',
          },
          green: {
            50: '#F0FDF4',
            100: '#DCFCE7',
            200: '#BBF7D0',
            300: '#86EFAC',
            400: '#4ADE80',
            500: '#22C55E',  // 자연색
            600: '#16A34A',
            700: '#15803D',
            800: '#166534',
            900: '#14532D',
          }
        }
      },
      fontFamily: {
        'sans': ['Pretendard', 'Apple SD Gothic Neo', 'sans-serif'],
      },
      backgroundImage: {
        'jeju-gradient': 'linear-gradient(135deg, #0EA5E9 0%, #38BDF8 50%, #FB923C 100%)',
        'jeju-wave': "url('/wave-pattern.svg')",
      }
    },
  },
  plugins: [],
}



