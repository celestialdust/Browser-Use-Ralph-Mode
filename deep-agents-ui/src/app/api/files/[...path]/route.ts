import { NextRequest, NextResponse } from "next/server";
import { readFile, stat } from "fs/promises";
import { existsSync } from "fs";
import path from "path";

// Allowed file extensions for security
const ALLOWED_EXTENSIONS = new Set([
  // Documents
  ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
  // Text
  ".md", ".txt", ".json", ".csv", ".html",
  // Images
  ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"
]);

// MIME type mapping
const MEDIA_TYPE_MAP: Record<string, string> = {
  ".pdf": "application/pdf",
  ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ".doc": "application/msword",
  ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  ".ppt": "application/vnd.ms-powerpoint",
  ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ".xls": "application/vnd.ms-excel",
  ".json": "application/json",
  ".md": "text/markdown; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".csv": "text/csv; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

// Get the agent directory - try multiple locations
function getAgentDir(): string {
  // Check environment variable first
  if (process.env.BROWSER_AGENT_DIR) {
    return process.env.BROWSER_AGENT_DIR;
  }

  // Default: look for .browser-agent in parent directories
  // This assumes deep-agents-ui is sibling to .browser-agent
  const possiblePaths = [
    path.join(process.cwd(), "..", ".browser-agent"),
    path.join(process.cwd(), ".browser-agent"),
    path.join(process.cwd(), "..", "Browser-Use", ".browser-agent"),
  ];

  for (const p of possiblePaths) {
    if (existsSync(p)) {
      return path.resolve(p);
    }
  }

  // Fallback to relative path
  return path.join(process.cwd(), "..", ".browser-agent");
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path: pathSegments } = await params;
    const filePath = pathSegments.join("/");

    // Security: Only allow files from artifacts directory
    if (!filePath.startsWith("artifacts/")) {
      return NextResponse.json(
        { error: "Access denied: Only artifacts are accessible" },
        { status: 403 }
      );
    }

    const agentDir = getAgentDir();
    const fullPath = path.join(agentDir, filePath);
    const resolvedPath = path.resolve(fullPath);
    const resolvedAgentDir = path.resolve(agentDir);

    // Security: Prevent path traversal
    if (!resolvedPath.startsWith(resolvedAgentDir)) {
      return NextResponse.json(
        { error: "Access denied: Path traversal detected" },
        { status: 403 }
      );
    }

    // Check file exists
    if (!existsSync(resolvedPath)) {
      return NextResponse.json(
        { error: "File not found", path: filePath, agentDir },
        { status: 404 }
      );
    }

    // Check it's a file
    const stats = await stat(resolvedPath);
    if (!stats.isFile()) {
      return NextResponse.json(
        { error: "Path is not a file" },
        { status: 400 }
      );
    }

    // Check allowed extensions
    const ext = path.extname(resolvedPath).toLowerCase();
    if (!ALLOWED_EXTENSIONS.has(ext)) {
      return NextResponse.json(
        { error: `File type not allowed: ${ext}` },
        { status: 403 }
      );
    }

    // Read file
    const fileContent = await readFile(resolvedPath);
    const mediaType = MEDIA_TYPE_MAP[ext] || "application/octet-stream";
    const filename = path.basename(resolvedPath);

    return new NextResponse(fileContent, {
      status: 200,
      headers: {
        "Content-Type": mediaType,
        "Content-Disposition": `inline; filename="${filename}"`,
        "Content-Length": stats.size.toString(),
        "Cache-Control": "no-cache",
      },
    });
  } catch (error) {
    console.error("[API Files] Error serving file:", error);
    return NextResponse.json(
      { error: "Internal server error", details: String(error) },
      { status: 500 }
    );
  }
}
