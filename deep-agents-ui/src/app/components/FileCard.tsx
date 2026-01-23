"use client";

import React from "react";
import {
  FileText,
  Download,
  FileSpreadsheet,
  Image as ImageIcon,
  Presentation,
  File,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PresentedFile } from "@/app/types/types";
import { cn } from "@/lib/utils";

interface FileCardProps {
  file: PresentedFile;
  onClick: () => void;
}

const fileIcons: Record<string, React.ElementType> = {
  PDF: FileText,
  DOCX: FileText,
  DOC: FileText,
  PPTX: Presentation,
  PPT: Presentation,
  XLSX: FileSpreadsheet,
  XLS: FileSpreadsheet,
  Markdown: FileText,
  Text: FileText,
  JSON: FileText,
  CSV: FileSpreadsheet,
  PNG: ImageIcon,
  JPEG: ImageIcon,
  GIF: ImageIcon,
  SVG: ImageIcon,
  HTML: FileText,
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const FileCard: React.FC<FileCardProps> = ({
  file,
  onClick,
}) => {
  const IconComponent = fileIcons[file.file_type] || File;
  // Use Next.js API route for downloads (same origin)
  const downloadUrl = `/api/files/${file.file_path}`;

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = file.display_name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        "flex items-center gap-4 p-4 rounded-lg border border-border",
        "bg-card hover:bg-accent/50 cursor-pointer transition-colors",
        "group"
      )}
    >
      {/* File icon */}
      <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-muted flex items-center justify-center">
        <IconComponent className="w-6 h-6 text-muted-foreground" />
      </div>

      {/* File info */}
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-sm text-foreground truncate">
          {file.display_name}
        </h4>
        <p className="text-xs text-muted-foreground">
          Document {file.file_type && `· ${file.file_type}`}
          {file.file_size && ` · ${formatFileSize(file.file_size)}`}
        </p>
        {file.description && (
          <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
            {file.description}
          </p>
        )}
      </div>

      {/* Download button */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleDownload}
        className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <Download className="w-4 h-4 mr-2" />
        Download
      </Button>
    </div>
  );
};
