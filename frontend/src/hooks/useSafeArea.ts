"use client";
import { useState, useEffect } from "react";

export function useSafeArea() {
  const [safeArea, setSafeArea] = useState({ top: 0, bottom: 0, left: 0, right: 0 });

  useEffect(() => {
    const getSafeArea = () => {
      const computedStyle = getComputedStyle(document.documentElement);
      return {
        top: parseInt(computedStyle.getPropertyValue("env(safe-area-inset-top)")) || 0,
        bottom: parseInt(computedStyle.getPropertyValue("env(safe-area-inset-bottom)")) || 0,
        left: parseInt(computedStyle.getPropertyValue("env(safe-area-inset-left)")) || 0,
        right: parseInt(computedStyle.getPropertyValue("env(safe-area-inset-right)")) || 0,
      };
    };
    setSafeArea(getSafeArea());
  }, []);

  return safeArea;
}
