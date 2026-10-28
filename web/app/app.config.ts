export default defineAppConfig({
  ui: {
    colors: {
      primary: 'truffe',
      neutral: 'stone',
    },
    button: {
      slots: {
        base: 'rounded-full font-extrabold',
      },
      variants: {
        size: {
          // White on coral stays readable only in bold at 18 px and more (docs/06, Accessibilité).
          xl: { base: 'min-h-[52px] px-6 text-lg' },
        },
      },
    },
    switch: {
      // 58 × 34 pill with a 28 px knob, coral when on (docs/06, Critères).
      slots: {
        base: 'h-[34px] w-[58px] border-0 data-[state=unchecked]:bg-switch-off',
        thumb:
          'size-7 shadow-[0_1px_3px_rgba(43,36,32,0.3)] data-[state=checked]:translate-x-[24px] data-[state=unchecked]:translate-x-[3px]',
      },
    },
  },
})
