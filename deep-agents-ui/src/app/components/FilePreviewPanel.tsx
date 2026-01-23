"use client";

import React, { useState, useEffect } from "react";
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
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use Next.js API route for serving files (same origin, no CORS issues)
  const fileUrl = file ? `/api/files/${file.file_path}` : null;

  useEffect(() => {
    if (!file || !fileUrl) {
      setContent(null);
      return;
    }

    const fetchContent = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // For text-based files, fetch content directly
        if (["Markdown", "Text", "JSON", "CSV", "HTML"].includes(file.file_type)) {
          const response = await fetch(fileUrl);
          if (!response.ok) throw new Error("Failed to fetch file");
          const text = await response.text();
          setContent(text);
        } else {
          // For other files, we'll use iframe or specific viewers
          setContent(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load file");
      } finally {
        setIsLoading(false);
      }
    };

    fetchContent();
  }, [file, fileUrl]);

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
    if (["PNG", "JPEG", "GIF", "SVG"].includes(file.file_type) && fileUrl) {
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

    // Text-based files
    if (content) {
      return (
        <pre className="p-6 overflow-auto h-full text-sm font-mono whitespace-pre-wrap">
          {content}
        </pre>
      );
    }

    // Office documents - suggest download
    if (["DOCX", "DOC", "PPTX", "PPT", "XLSX", "XLS"].includes(file.file_type)) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
          <p className="text-sm mb-4">
            Preview not available for {file.file_type} files
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
            <Button variant="outline" size="sm" onClick={handleOpenExternal}>
              <ExternalLink className="w-4 h-4 mr-2" />
              Open
            </Button>
          </div>
        </div>
      );
    }

    // Fallback
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
        <p className="text-sm">No preview available</p>
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
