"use client";

import React, { useState, useEffect, useCallback } from "react";
import { X, Download, RefreshCw, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PresentedFile } from "@/app/types/types";
import { MarkdownContent } from "./MarkdownContent";

interface FilePreviewPanelProps {
  file: PresentedFile | null;
  onClose: () => void;
}

export const FilePreviewPanel: React.FC<FilePreviewPanelProps> = ({
  file,
  onClose,
}) => {
  const [content, setContent] = useState<string | null>(null);
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [tableData, setTableData] = useState<string[][] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use Next.js API route for serving files (same origin, no CORS issues)
  const fileUrl = file ? `/api/files/${file.file_path}` : null;

  // Convert DOCX to HTML using mammoth
  const convertDocxToHtml = useCallback(async (arrayBuffer: ArrayBuffer) => {
    try {
      const mammoth = await import("mammoth");
      const result = await mammoth.convertToHtml({ arrayBuffer });
      return result.value;
    } catch (err) {
      console.error("Failed to convert DOCX:", err);
      throw new Error("Failed to convert DOCX to preview");
    }
  }, []);

  // Parse XLSX to table data
  const parseXlsx = useCallback(async (arrayBuffer: ArrayBuffer) => {
    try {
      const XLSX = await import("xlsx");
      const workbook = XLSX.read(arrayBuffer, { type: "array" });
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];
      const data = XLSX.utils.sheet_to_json<string[]>(worksheet, { header: 1 });
      return data as string[][];
    } catch (err) {
      console.error("Failed to parse XLSX:", err);
      throw new Error("Failed to parse Excel file");
    }
  }, []);

  useEffect(() => {
    if (!file || !fileUrl) {
      setContent(null);
      setHtmlContent(null);
      setTableData(null);
      return;
    }

    const fetchContent = async () => {
      setIsLoading(true);
      setError(null);
      setContent(null);
      setHtmlContent(null);
      setTableData(null);

      try {
        // Text-based files - fetch as text
        if (["Markdown", "Text", "JSON", "CSV"].includes(file.file_type)) {
          const response = await fetch(fileUrl);
          if (!response.ok) throw new Error("Failed to fetch file");
          const text = await response.text();
          setContent(text);
        }
        // HTML - fetch as text for iframe rendering
        else if (file.file_type === "HTML") {
          const response = await fetch(fileUrl);
          if (!response.ok) throw new Error("Failed to fetch file");
          const text = await response.text();
          setHtmlContent(text);
        }
        // DOCX - convert to HTML using mammoth
        else if (["DOCX", "DOC"].includes(file.file_type)) {
          const response = await fetch(fileUrl);
          if (!response.ok) throw new Error("Failed to fetch file");
          const arrayBuffer = await response.arrayBuffer();
          const html = await convertDocxToHtml(arrayBuffer);
          setHtmlContent(html);
        }
        // XLSX/XLS - parse and render as table
        else if (["XLSX", "XLS"].includes(file.file_type)) {
          const response = await fetch(fileUrl);
          if (!response.ok) throw new Error("Failed to fetch file");
          const arrayBuffer = await response.arrayBuffer();
          const data = await parseXlsx(arrayBuffer);
          setTableData(data);
        }
        // Other files - no content to fetch, will use iframe or fallback
        else {
          setContent(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load file");
      } finally {
        setIsLoading(false);
      }
    };

    fetchContent();
  }, [file, fileUrl, convertDocxToHtml, parseXlsx]);

  if (!file) return null;

  const handleDownload = () => {
    if (!fileUrl) return;
    const link = document.createElement("a");
    link.href = fileUrl;
    link.download = file.display_name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOpenExternal = () => {
    if (fileUrl) window.open(fileUrl, "_blank");
  };

  const renderPreview = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-full">
          <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
          <p className="text-sm">{error}</p>
          <Button variant="outline" size="sm" className="mt-4" onClick={handleOpenExternal}>
            <ExternalLink className="w-4 h-4 mr-2" />
            Open in new tab
          </Button>
        </div>
      );
    }

    // PDF - use iframe with embedded viewer
    if (file.file_type === "PDF" && fileUrl) {
      return (
        <iframe
          src={`${fileUrl}#view=FitH`}
          className="w-full h-full border-0"
          title={file.display_name}
        />
      );
    }

    // Images
    if (["PNG", "JPEG", "GIF", "SVG", "WEBP"].includes(file.file_type) && fileUrl) {
      return (
        <div className="flex items-center justify-center h-full p-4 bg-muted">
          <img
            src={fileUrl}
            alt={file.display_name}
            className="max-w-full max-h-full object-contain"
          />
        </div>
      );
    }

    // Markdown
    if (file.file_type === "Markdown" && content) {
      return (
        <div className="p-6 overflow-auto h-full">
          <MarkdownContent content={content} />
        </div>
      );
    }

    // HTML content (from HTML files or converted DOCX)
    if (htmlContent) {
      return (
        <iframe
          srcDoc={`
            <!DOCTYPE html>
            <html>
              <head>
                <meta charset="utf-8">
                <style>
                  body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    padding: 24px;
                    max-width: 100%;
                    color: #333;
                  }
                  img { max-width: 100%; height: auto; }
                  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
                  th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                  th { background-color: #f5f5f5; }
                  pre { background: #f5f5f5; padding: 12px; overflow-x: auto; border-radius: 4px; }
                  code { background: #f5f5f5; padding: 2px 4px; border-radius: 2px; }
                  h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; margin-bottom: 0.5em; }
                  p { margin: 1em 0; }
                  ul, ol { margin: 1em 0; padding-left: 2em; }
                </style>
              </head>
              <body>${htmlContent}</body>
            </html>
          `}
          className="w-full h-full border-0 bg-white"
          title={file.display_name}
          sandbox="allow-same-origin"
        />
      );
    }

    // Excel/Spreadsheet data as table
    if (tableData && tableData.length > 0) {
      return (
        <div className="overflow-auto h-full p-4">
          <table className="w-full border-collapse text-sm">
            <thead>
              {tableData[0] && (
                <tr>
                  {tableData[0].map((cell, i) => (
                    <th
                      key={i}
                      className="border border-border bg-muted px-3 py-2 text-left font-medium"
                    >
                      {cell ?? ""}
                    </th>
                  ))}
                </tr>
              )}
            </thead>
            <tbody>
              {tableData.slice(1).map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td
                      key={cellIndex}
                      className="border border-border px-3 py-2"
                    >
                      {cell ?? ""}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    // CSV as table
    if (file.file_type === "CSV" && content) {
      const rows = content.split("\n").map(row => row.split(","));
      return (
        <div className="overflow-auto h-full p-4">
          <table className="w-full border-collapse text-sm">
            <thead>
              {rows[0] && (
                <tr>
                  {rows[0].map((cell, i) => (
                    <th
                      key={i}
                      className="border border-border bg-muted px-3 py-2 text-left font-medium"
                    >
                      {cell?.trim() ?? ""}
                    </th>
                  ))}
                </tr>
              )}
            </thead>
            <tbody>
              {rows.slice(1).filter(row => row.some(cell => cell?.trim())).map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td
                      key={cellIndex}
                      className="border border-border px-3 py-2"
                    >
                      {cell?.trim() ?? ""}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    // JSON with syntax highlighting
    if (file.file_type === "JSON" && content) {
      try {
        const formatted = JSON.stringify(JSON.parse(content), null, 2);
        return (
          <pre className="p-6 overflow-auto h-full text-sm font-mono whitespace-pre-wrap bg-muted">
            {formatted}
          </pre>
        );
      } catch {
        // If JSON parsing fails, show as plain text
      }
    }

    // Plain text files
    if (content) {
      return (
        <pre className="p-6 overflow-auto h-full text-sm font-mono whitespace-pre-wrap">
          {content}
        </pre>
      );
    }

    // PPTX - no good client-side preview, suggest download
    if (["PPTX", "PPT"].includes(file.file_type)) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
          <p className="text-sm mb-2">
            PowerPoint preview is not available in browser
          </p>
          <p className="text-xs mb-4 text-center max-w-xs">
            Download the file to view it in Microsoft PowerPoint or compatible application
          </p>
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="w-4 h-4 mr-2" />
            Download {file.file_type}
          </Button>
        </div>
      );
    }

    // Fallback
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
        <p className="text-sm">No preview available for this file type</p>
        <Button variant="outline" size="sm" className="mt-4" onClick={handleDownload}>
          <Download className="w-4 h-4 mr-2" />
          Download
        </Button>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-background border-l border-border">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-card">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <span className="text-sm font-medium truncate">{file.display_name}</span>
          <span className="text-xs text-muted-foreground flex-shrink-0">
            {file.file_type && `· ${file.file_type}`}
          </span>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <Button variant="ghost" size="sm" onClick={handleDownload} title="Download file">
            <Download className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={onClose} title="Close">
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Preview content */}
      <div className="flex-1 overflow-hidden">
        {renderPreview()}
      </div>
    </div>
  );
};
