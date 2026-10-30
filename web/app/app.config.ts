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
    modal: {
      slots: {
        content: 'divide-line bg-card',
        title: 'font-display text-xl text-ink',
        description: 'text-[15px] text-ink-muted',
      },
      variants: {
        fullscreen: {
          false: { content: 'rounded-card-compact shadow-card ring-0' },
        },
      },
    },
    formField: {
      slots: {
        labelWrapper: 'flex items-baseline justify-between gap-3',
        label: 'text-sm font-extrabold text-ink-secondary md:text-[15px]',
        hint: 'text-[13px] text-ink-muted md:text-sm',
      },
      variants: {
        orientation: {
          vertical: { container: 'mt-1.5 md:mt-2' },
        },
      },
    },
    select: {
      slots: {
        base: 'min-h-[52px] rounded-2xl font-bold shadow-card focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-coral',
        content: 'rounded-2xl bg-card shadow-floating',
        item: 'font-bold',
      },
      variants: {
        size: {
          xl: { base: 'px-[18px] text-base' },
        },
        variant: {
          outline: 'bg-card text-ink ring-2 ring-card',
        },
      },
    },
    input: {
      slots: {
        base: 'rounded-2xl font-bold shadow-card placeholder:font-semibold placeholder:text-ink-muted focus-visible:outline-offset-0 md:rounded-tile-compact',
      },
      variants: {
        size: {
          xl: {
            base: 'h-[52px] px-[18px] text-base md:h-[58px] md:px-5 md:text-[17px] lg:h-[54px] lg:px-[18px] lg:text-base',
            trailing: 'pe-1.5 md:pe-[9px] lg:pe-1.5',
          },
        },
        variant: {
          outline: 'bg-card text-ink ring-2 ring-card',
        },
      },
      compoundVariants: [
        { trailing: true, size: 'xl', class: 'pe-14 md:pe-[60px] lg:pe-14' },
        {
          color: 'primary',
          variant: 'outline',
          class: 'outline-coral-pastel focus-visible:outline-4 focus-visible:ring-coral',
        },
        {
          color: 'error',
          variant: 'outline',
          class: 'outline-coral-pastel focus-visible:outline-4 focus-visible:ring-coral',
        },
        { color: 'error', highlight: true, class: 'ring-2 ring-coral' },
      ],
    },
  },
})
