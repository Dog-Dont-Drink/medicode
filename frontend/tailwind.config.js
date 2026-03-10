/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#ECFDF5',
                    100: '#D1FAE5',
                    200: '#A7F3D0',
                    300: '#6EE7B7',
                    400: '#34D399',
                    500: '#059669',
                    600: '#047857',
                    700: '#065F46',
                    800: '#064E3B',
                    900: '#022C22',
                    DEFAULT: '#059669',
                },
                secondary: {
                    50: '#F0FDF4',
                    100: '#DCFCE7',
                    200: '#BBF7D0',
                    300: '#86EFAC',
                    400: '#4ADE80',
                    500: '#16A34A',
                    600: '#15803D',
                    700: '#166534',
                    800: '#14532D',
                    900: '#052E16',
                    DEFAULT: '#16A34A',
                },
                accent: '#10B981',
                cta: '#059669',
                warning: '#F59E0B',
                danger: '#EF4444',
                success: '#22C55E',
            },
            fontFamily: {
                heading: ['Figtree', 'sans-serif'],
                body: ['Noto Sans', 'Noto Sans SC', 'sans-serif'],
                sans: ['Noto Sans', 'Noto Sans SC', 'sans-serif'],
            },
            spacing: {
                '18': '4.5rem',
                '88': '22rem',
                '112': '28rem',
                '128': '32rem',
            },
            boxShadow: {
                'soft': '0 1px 2px rgba(0,0,0,0.05)',
                'card': '0 4px 6px rgba(0,0,0,0.07)',
                'elevated': '0 10px 15px rgba(0,0,0,0.1)',
                'float': '0 20px 25px rgba(0,0,0,0.12)',
            },
            borderRadius: {
                'md': '0.375rem',
                'lg': '0.5rem',
                'xl': '0.5rem',
                '2xl': '0.625rem',
                '3xl': '0.75rem',
            },
            animation: {
                'fade-in': 'fadeIn 0.3s ease-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'slide-down': 'slideDown 0.3s ease-out',
                'scale-in': 'scaleIn 0.2s ease-out',
                'pulse-soft': 'pulseSoft 2s infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                slideDown: {
                    '0%': { opacity: '0', transform: 'translateY(-10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                scaleIn: {
                    '0%': { opacity: '0', transform: 'scale(0.95)' },
                    '100%': { opacity: '1', transform: 'scale(1)' },
                },
                pulseSoft: {
                    '0%, 100%': { opacity: '1' },
                    '50%': { opacity: '0.7' },
                },
            },
        },
    },
    plugins: [],
}
