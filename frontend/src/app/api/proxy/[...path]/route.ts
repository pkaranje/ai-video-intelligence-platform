import { type NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const HOP_BY_HOP = new Set([
  "connection",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
]);

async function proxy(
  req: NextRequest,
  params: Promise<{ path: string[] }>
): Promise<NextResponse> {
  const { path } = await params;
  const upstream = `${BACKEND_URL}/${path.join("/")}${req.nextUrl.search}`;

  const reqHeaders = new Headers();
  req.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      reqHeaders.set(key, value);
    }
  });

  const hasBody = !["GET", "HEAD"].includes(req.method);
  const init: RequestInit & { duplex?: string } = {
    method: req.method,
    headers: reqHeaders,
    ...(hasBody && { body: req.body, duplex: "half" }),
  };

  const upstreamRes = await fetch(upstream, init);

  const resHeaders = new Headers();
  upstreamRes.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      resHeaders.set(key, value);
    }
  });

  return new NextResponse(upstreamRes.body, {
    status: upstreamRes.status,
    headers: resHeaders,
  });
}

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(req, params);
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(req, params);
}

export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(req, params);
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(req, params);
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(req, params);
}
