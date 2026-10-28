declare module '#app' {
  interface PageMeta {
    /** A screen pushed over the tabs (litter detail): no tab bar, a back button instead. */
    isPushedScreen?: boolean
    /** Reachable without a session, and with one too: the forgotten password screens. */
    isPublicScreen?: boolean
    /** Reachable without a session only, a signed-in user is sent to the litters: login and signup. */
    isGuestOnlyScreen?: boolean
  }
}

export {}
