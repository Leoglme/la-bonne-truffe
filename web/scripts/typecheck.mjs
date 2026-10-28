import { spawnSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import { join } from 'node:path'

/** Type-checks the web app in its own build dir, so a running `nuxt dev` or `tauri dev` keeps its `.nuxt`. */

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

if (output) {
  console.log(output)
}
process.exit(check.status ?? 1)
