import { exec as cbExec } from 'child_process'
import * as fs from 'fs'
import * as path from 'path'
import { promisify } from 'util'

const app = process && process.type === 'renderer' ? require('@electron/remote').app : require('electron').app
const athena = app.isPackaged ? path.join(process.resourcesPath, 'athena') : path.resolve(process.cwd(), '..', 'athena')
const exec = promisify(cbExec)
const symlinkPath = '/usr/local/bin/athena'

export function installed() {
  return fs.existsSync(symlinkPath) && fs.readlinkSync(symlinkPath) === athena
}

export async function install() {
  const command = `do shell script "mkdir -p ${path.dirname(
    symlinkPath
  )} && ln -F -s \\"${athena}\\" \\"${symlinkPath}\\"" with administrator privileges`

  await exec(`osascript -e '${command}'`)
}
