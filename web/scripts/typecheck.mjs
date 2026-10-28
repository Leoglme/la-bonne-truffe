import { spawnSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import { join } from 'node:path'

/**
 * Type-checks the app against types generated in a dedicated build dir.
 *
 * `vue-tsc --build` on the root tsconfig reads `.nuxt`, which belongs to whichever dev
 * server is running. The Tauri dev server prepares `.nuxt` in desktop mode — without the
 * sitemap module — so the `site`/`sitemap` keys of `nuxt.config.ts` stop type-checking and
 * the gate goes red as long as it runs; regenerating `.nuxt` instead breaks the live
 * server (its Vite manifest disappears). Generating the full web types into
 * `.nuxt-typecheck` keeps the gate green and the dev server untouched.
 */

const BUILD_DIRECTORY = '.nuxt-typecheck'

const prepare = spawnSync('npx nuxt prepare', {
  encoding: 'utf8',
  shell: true,
  env: { ...process.env, NUXT_TYPECHECK_BUILD_DIR: BUILD_DIRECTORY, NUXT_DESKTOP_BUILD: '' },
})

if (prepare.status !== 0) {
  console.error(`${prepare.stdout ?? ''}${prepare.stderr ?? ''}`)
  console.error('nuxt prepare failed — typecheck aborted.')
  process.exit(prepare.status ?? 1)
}

// The root tsconfig points at `.nuxt`; mirror it inside the dedicated build dir.
writeFileSync(
  join(BUILD_DIRECTORY, 'tsconfig.typecheck-node.json'),
  JSON.stringify({ extends: './tsconfig.node.json', compilerOptions: { types: ['node'] } }, null, 2),
)
writeFileSync(
  join(BUILD_DIRECTORY, 'tsconfig.typecheck.json'),
  JSON.stringify(
    {
      files: [],
      references: [
        { path: './tsconfig.app.json' },
        { path: './tsconfig.server.json' },
        { path: './tsconfig.shared.json' },
        { path: './tsconfig.typecheck-node.json' },
      ],
    },
    null,
    2,
  ),
)

const check = spawnSync(`npx vue-tsc --build --force ${BUILD_DIRECTORY}/tsconfig.typecheck.json`, {
  encoding: 'utf8',
  shell: true,
})

const output = `${check.stdout ?? ''}${check.stderr ?? ''}`.trim()
if (output) console.log(output)
process.exit(check.status ?? 1)
