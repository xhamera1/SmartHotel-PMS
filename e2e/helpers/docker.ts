import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

export async function stopPricing(): Promise<void> {
  await execFileAsync('docker', ['stop', 'smarthotel-pricing'])
}

export async function startPricing(): Promise<void> {
  await execFileAsync('docker', ['start', 'smarthotel-pricing'])
  // Poll readiness without fixed sleep loops beyond short backoff
  for (let i = 0; i < 40; i++) {
    try {
      const res = await fetch('http://localhost:8081/health/ready')
      if (res.ok) {
        return
      }
    } catch {
      // not up yet
    }
    await new Promise((r) => setTimeout(r, 1500))
  }
  throw new Error('pricing did not become ready after docker start')
}
