/** Packaged desktop app only: look for a newer release at startup; the update modal offers to install it. */
export default defineNuxtPlugin((): void => {
  const { isProdDesktop }: ReturnType<typeof useDesktopRuntime> = useDesktopRuntime()
  if (!isProdDesktop.value) {
    return
  }
  useDesktopUpdateStore().checkForUpdate()
})
