export default defineAppConfig({
  ui: {
    colors: {
      primary: 'truffe',
      neutral: 'stone',
    },
    button: {
      slots: {
        base: 'rounded-full font-extrabold focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-coral',
      },
      variants: {
        size: {
          xl: { base: 'min-h-[52px] px-6 text-lg' },
        },
      },
      compoundVariants: [
        {
          color: 'neutral',
          variant: 'outline',
          class: 'bg-card text-ink ring-2 ring-ink hover:bg-card active:bg-card disabled:bg-card disabled:opacity-60',
        },
        {
          color: 'neutral',
          variant: 'outline',
          size: 'md',
          class: 'min-h-12 px-5 text-[15px]',
        },
        {
          color: 'neutral',
          variant: 'outline',
          size: 'lg',
          class: 'min-h-[58px] px-6 text-base',
        },
      ],
    },
    switch: {
      slots: {
        base: 'border-0 focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-coral data-[state=unchecked]:bg-switch-off',
        thumb: 'bg-white shadow-switch-thumb data-[state=unchecked]:translate-x-[3px]',
      },
      variants: {
        size: {
          md: {
            base: 'h-[34px] w-[58px]',
            container: 'h-[34px]',
            thumb: 'size-7 data-[state=checked]:translate-x-[27px]',
          },
        },
      },
    },
  },
})
