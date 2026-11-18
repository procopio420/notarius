import type { NextConfig } from "next";

const minutaQa = process.env.NOTARIUS_QA_CARTAO_MINUTA === '1';
const localConnections = minutaQa
  ? 'http://127.0.0.1:8012 ws://127.0.0.1:3012'
  : 'http://localhost:8002 http://127.0.0.1:8002 ws://localhost:3002 ws://127.0.0.1:3002';
const nextConfig: NextConfig = {
  ...(minutaQa ? {
    distDir: '.next/cartao-minuta-qa',
    typescript: { tsconfigPath: '.next/tsconfig-cartao-minuta-qa.json' },
  } : {}),
  async headers() {
    if (process.env.NEXT_PUBLIC_PILOTO_LOCAL !== '1') return [];
    return [{ source: '/:path*', headers: [
      { key: 'Cache-Control', value: 'no-store' },
      { key: 'Referrer-Policy', value: 'no-referrer' },
      { key: 'Content-Security-Policy', value: `default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' ${localConnections}; object-src 'none'; frame-src 'none'; base-uri 'self'; form-action 'self'` },
    ] }];
  },
};

export default nextConfig;
