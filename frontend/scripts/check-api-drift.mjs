import { createHash, timingSafeEqual } from 'node:crypto'
import { readFileSync, unlinkSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const committed = resolve(root, 'src/shared/api/schema.d.ts')
const temp = resolve(root, 'src/shared/api/schema.check.d.ts')
const openapi = resolve(root, '../docs/api/pms-openapi.json')
const cli = resolve(root, 'node_modules/openapi-typescript/bin/cli.js')

const generate = spawnSync(process.execPath, [cli, openapi, '-o', temp], {
    cwd: root,
    encoding: 'utf8',
})

if (generate.status !== 0) {
    console.error(generate.stdout)
    console.error(generate.stderr)
    process.exit(generate.status ?? 1)
}

const a = readFileSync(committed)
const b = readFileSync(temp)
unlinkSync(temp)

const ha = createHash('sha256').update(a).digest()
const hb = createHash('sha256').update(b).digest()

if (ha.length !== hb.length || !timingSafeEqual(ha, hb)) {
    console.error(
        'OpenAPI types drifted. Run `pnpm generate:api` after updating docs/api/pms-openapi.json.',
    )
    process.exit(1)
}

console.log('OpenAPI types are in sync with docs/api/pms-openapi.json')
