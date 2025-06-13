// import React from "react";
import aAif from "@/assets/azure-aif.png";

export function Footer() {
  return (
    <footer className="bg-muted mt-8">
      <div className="container mx-auto px-4 py-2 text-center text-sm text-muted-foreground">
        <p className="inline">&copy; 2025 </p>
        <p className="inline">&nbsp;running on </p>
        <img src={aAif} alt="Logo" className="w-[18px] inline" />
        <p className="inline">&nbsp;ver. 20250613.1</p>
      </div>
    </footer>
  );
}
