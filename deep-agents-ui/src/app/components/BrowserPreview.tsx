"use client";

import React, { useState, useEffect, useRef } from "react";
import { Monitor, Wifi, WifiOff, Maximize2, Minimize2 } from "lucide-react";

interface BrowserPreviewProps {
  streamUrl: string | null;
  isActive?: boolean;
}

interface FrameMessage {
  type: "frame";
  data: string; // base64-encoded JPEG
  metadata: {
    deviceWidth: number;
    deviceHeight: number;
    pageScaleFactor: number;
    offsetTop: number;
    scrollOffsetX: number;
    scrollOffsetY: number;
  };
}

interface StatusMessage {
  type: "status";
  connected: boolean;
  screencasting: boolean;
  viewportWidth: number;
  viewportHeight: number;
}

type WebSocketMessage = FrameMessage | StatusMessage;

export function BrowserPreview({ streamUrl, isActive }: BrowserPreviewProps) {
  const [imageSrc, setImageSrc] = useState<string>("");
  const [connectionStatus, setConnectionStatus] = useState<{
    connected: boolean;
    screencasting: boolean;
  }>({ connected: false, screencasting: false });
  const [viewport, setViewport] = useState<{
    width: number;
    height: number;
  }>({ width: 0, height: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!streamUrl || !isActive) {
      return;
    }

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(streamUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("Browser stream connected:", streamUrl);
          setConnectionStatus((prev) => ({ ...prev, connected: true }));
        };

        ws.onmessage = (event) => {
          try {
            const msg: WebSocketMessage = JSON.parse(event.data);

            if (msg.type === "frame") {
              // Update image with base64 data
              setImageSrc(`data:image/jpeg;base64,${msg.data}`);
              // Update viewport dimensions from metadata
              if (msg.metadata) {
                setViewport({
                  width: msg.metadata.deviceWidth,
                  height: msg.metadata.deviceHeight,
                });
              }
            } else if (msg.type === "status") {
              setConnectionStatus({
                connected: msg.connected,
                screencasting: msg.screencasting,
              });
              if (msg.viewportWidth && msg.viewportHeight) {
                setViewport({
                  width: msg.viewportWidth,
                  height: msg.viewportHeight,
                });
              }
            }
          } catch (error) {
            console.error("Failed to parse WebSocket message:", error);
          }
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
        };

        ws.onclose = () => {
          console.log("Browser stream disconnected");
          setConnectionStatus({ connected: false, screencasting: false });

          // Attempt to reconnect after 2 seconds if still active
          if (isActive && streamUrl) {
            reconnectTimeoutRef.current = setTimeout(() => {
              console.log("Attempting to reconnect...");
              connectWebSocket();
            }, 2000);
          }
        };
      } catch (error) {
        console.error("Failed to connect to browser stream:", error);
      }
    };

    connectWebSocket();

    // Cleanup on unmount or when streamUrl changes
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [streamUrl, isActive]);

  if (!isActive || !streamUrl) {
    return null;
  }

  return (
    <div className={`browser-preview ${isFullscreen ? "fixed inset-0 z-50" : ""}`}>
      <div className="browser-preview-header">
        <div className="browser-preview-status">
          <Monitor className="w-4 h-4" />
          <span>Browser Preview</span>
          {connectionStatus.connected ? (
            <>
              <div className="status-dot" title="Connected" />
              <Wifi className="w-4 h-4 text-green-600" />
              {viewport.width > 0 && (
                <span className="text-xs">
                  {viewport.width} × {viewport.height}
                </span>
              )}
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-red-600" />
              <span className="text-xs">Disconnected</span>
            </>
          )}
        </div>
        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
          title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
        >
          {isFullscreen ? (
            <Minimize2 className="w-4 h-4" />
          ) : (
            <Maximize2 className="w-4 h-4" />
          )}
        </button>
      </div>
      {imageSrc ? (
        <img
          src={imageSrc}
          alt="Browser viewport"
          className="browser-preview-image"
        />
      ) : (
        <div className="flex items-center justify-center h-64 text-gray-500">
          {connectionStatus.connected
            ? "Waiting for frames..."
            : "Connecting to browser..."}
        </div>
      )}
    </div>
  );
}
