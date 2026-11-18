import http from 'node:http'
import https from 'node:https'
import { readFileSync } from 'node:fs'
import { isIPv4 } from 'node:net'
import { join } from 'node:path'

const [address, prefixText, folder] = process.argv.slice(2)
const prefix = Number(prefixText)
if (!isIPv4(address) || !Number.isInteger(prefix) || prefix < 8 || prefix > 30 || !folder) {
  throw new Error('Endereço e prefixo IPv4 da rede local inválidos.')
}
const tlsPort = 3443
const installPort = 3080
const origin = `https://${address}:${tlsPort}`
const ipv4 = value => value.split('.').reduce((result, octet) => result * 256 + Number(octet), 0)
const subnet = value => Math.floor(ipv4(value) / 2 ** (32 - prefix))
const localSubnet = subnet(address)

function fromLocalNetwork(request, port) {
  const remote = request.socket.remoteAddress
  return isIPv4(remote) && subnet(remote) === localSubnet && request.headers.host === `${address}:${port}`
}

function reply(response, status, message = '') {
  response.writeHead(status, { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' })
  response.end(message)
}

function forward(request, response) {
  if (!fromLocalNetwork(request, tlsPort) || (request.headers.origin && request.headers.origin !== origin)) {
    return reply(response, 403)
  }
  const url = URL.parse(request.url, origin)
  if (!url || url.origin !== origin || !request.url.startsWith('/')) return reply(response, 400)
  const path = url.pathname
  const api = /^\/api\/v1\/(?:auth\/(?:login|logout|me)\/|atendimentos\/(?:[a-z0-9-]+\/)*)$/.test(path)
  const page = path === '/' || path === '/login' || path === '/favicon.ico'
    || /^\/atendimentos(?:\/[a-f0-9-]{36})?\/?$/.test(path)
    || (path.startsWith('/_next/static/') && !path.endsWith('.map'))
  if (!api && (!page || !['GET', 'HEAD'].includes(request.method))) return reply(response, 404)

  const port = api ? 8002 : 3002
  const headers = { ...request.headers, host: `localhost:${port}` }
  for (const name of ['connection', 'forwarded', 'x-forwarded-host', 'x-forwarded-for', 'x-forwarded-port',
    'x-forwarded-proto', 'x-real-ip', 'x-tenant-id', 'upgrade']) delete headers[name]

  const upstream = http.request({ hostname: '127.0.0.1', port, path: `${path}${url.search}`,
    method: request.method, headers, timeout: path.endsWith('/minuta-assistida/') ? 185000 : 120000 }, result => {
    const resultHeaders = { ...result.headers, 'cache-control': 'no-store' }
    delete resultHeaders.connection
    if (resultHeaders.location?.startsWith(`http://localhost:${port}/`)) {
      resultHeaders.location = resultHeaders.location.replace(`http://localhost:${port}`, origin)
    }
    response.writeHead(result.statusCode, resultHeaders)
    result.pipe(response)
  })
  upstream.on('timeout', () => upstream.destroy())
  upstream.on('error', () => {
    if (response.headersSent) response.destroy()
    else reply(response, 502, 'O Notarius local não respondeu.')
  })
  request.on('aborted', () => upstream.destroy())
  response.on('close', () => { if (!response.writableFinished) upstream.destroy() })
  request.pipe(upstream)
}

const tls = https.createServer({
  key: readFileSync(join(folder, 'servidor.key')),
  cert: readFileSync(join(folder, 'servidor.pem')),
  minVersion: 'TLSv1.2',
}, forward)
const profile = readFileSync(join(folder, 'notarius.mobileconfig'))
const install = http.createServer((request, response) => {
  if (!fromLocalNetwork(request, installPort)) return reply(response, 403)
  if (request.method !== 'GET' || request.url !== '/notarius.mobileconfig') return reply(response, 404)
  response.writeHead(200, { 'Content-Type': 'application/x-apple-aspen-config',
    'Content-Disposition': 'attachment; filename="notarius.mobileconfig"', 'Cache-Control': 'no-store' })
  response.end(profile)
})

for (const server of [tls, install]) {
  server.on('error', error => {
    console.error(error.message)
    process.exitCode = 1
    for (const listener of [tls, install]) listener.close()
  })
}
tls.listen(tlsPort, address)
install.listen(installPort, address)
