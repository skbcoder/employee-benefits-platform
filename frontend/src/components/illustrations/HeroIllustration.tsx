"use client";

export default function HeroIllustration() {
  return (
    <svg
      viewBox="0 0 480 260"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mx-auto w-full max-w-lg"
    >
      {/* Background glow */}
      <defs>
        <radialGradient id="glow1" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#22c55e" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="glow2" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="cardGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1e1e2a" />
          <stop offset="100%" stopColor="#111118" />
        </linearGradient>
        <linearGradient id="shieldGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#22c55e" />
          <stop offset="100%" stopColor="#16a34a" />
        </linearGradient>
      </defs>

      <ellipse cx="240" cy="130" rx="200" ry="120" fill="url(#glow1)" />
      <ellipse cx="160" cy="140" rx="100" ry="80" fill="url(#glow2)" />

      {/* Document card left */}
      <g className="animate-float-slow">
        <rect x="60" y="60" width="120" height="150" rx="12" fill="url(#cardGrad)" stroke="#2a2a3a" strokeWidth="1.5" />
        {/* Header bar */}
        <rect x="76" y="80" width="60" height="6" rx="3" fill="#3b82f6" opacity="0.6" />
        {/* Lines */}
        <rect x="76" y="100" width="88" height="4" rx="2" fill="#2a2a3a" />
        <rect x="76" y="112" width="70" height="4" rx="2" fill="#2a2a3a" />
        <rect x="76" y="124" width="80" height="4" rx="2" fill="#2a2a3a" />
        {/* Checkbox rows */}
        <rect x="76" y="144" width="10" height="10" rx="2" fill="#22c55e" opacity="0.3" />
        <rect x="92" y="146" width="50" height="4" rx="2" fill="#2a2a3a" />
        <rect x="76" y="160" width="10" height="10" rx="2" fill="#22c55e" opacity="0.3" />
        <rect x="92" y="162" width="40" height="4" rx="2" fill="#2a2a3a" />
        {/* Checkmarks */}
        <path d="M79 149l2 2 4-4" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <animate attributeName="opacity" values="0;1;1" dur="2s" repeatCount="indefinite" />
        </path>
        <path d="M79 165l2 2 4-4" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <animate attributeName="opacity" values="0;0;1" dur="2s" repeatCount="indefinite" />
        </path>
      </g>

      {/* Center shield / protection icon */}
      <g className="animate-float">
        <path
          d="M240 55 L275 72 L275 115 Q275 145 240 160 Q205 145 205 115 L205 72 Z"
          fill="url(#shieldGrad)"
          opacity="0.15"
          stroke="#22c55e"
          strokeWidth="1.5"
        />
        <path
          d="M240 70 L265 82 L265 112 Q265 135 240 147 Q215 135 215 112 L215 82 Z"
          fill="none"
          stroke="#22c55e"
          strokeWidth="1"
          opacity="0.4"
        />
        {/* Shield checkmark */}
        <path d="M228 108l8 8 16-16" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <animate attributeName="stroke-dasharray" values="0 40;40 0" dur="1.5s" fill="freeze" />
        </path>
        {/* Pulse ring */}
        <circle cx="240" cy="108" r="30" fill="none" stroke="#22c55e" strokeWidth="1" opacity="0">
          <animate attributeName="r" values="25;45" dur="2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.4;0" dur="2s" repeatCount="indefinite" />
        </circle>
      </g>

      {/* Right side - status/processing card */}
      <g className="animate-float-delayed">
        <rect x="300" y="70" width="130" height="130" rx="12" fill="url(#cardGrad)" stroke="#2a2a3a" strokeWidth="1.5" />
        {/* User avatar */}
        <circle cx="332" cy="96" r="12" fill="#3b82f6" opacity="0.2" stroke="#3b82f6" strokeWidth="1" />
        <circle cx="332" cy="93" r="4" fill="#3b82f6" opacity="0.5" />
        <path d="M324 102 Q332 106 340 102" stroke="#3b82f6" strokeWidth="1" fill="none" opacity="0.5" />
        {/* Name line */}
        <rect x="352" y="90" width="60" height="5" rx="2.5" fill="#2a2a3a" />
        <rect x="352" y="100" width="40" height="4" rx="2" fill="#2a2a3a" opacity="0.5" />
        {/* Status steps */}
        <circle cx="325" cy="130" r="6" fill="#22c55e" opacity="0.8">
          <animate attributeName="opacity" values="0.4;0.8;0.4" dur="3s" repeatCount="indefinite" />
        </circle>
        <rect x="336" y="128" width="76" height="4" rx="2" fill="#22c55e" opacity="0.3" />
        <circle cx="325" cy="150" r="6" fill="#f59e0b" opacity="0.6">
          <animate attributeName="opacity" values="0.3;0.7;0.3" dur="3s" begin="1s" repeatCount="indefinite" />
        </circle>
        <rect x="336" y="148" width="60" height="4" rx="2" fill="#f59e0b" opacity="0.2" />
        <circle cx="325" cy="170" r="6" fill="#6b7280" opacity="0.3" />
        <rect x="336" y="168" width="50" height="4" rx="2" fill="#2a2a3a" opacity="0.5" />
      </g>

      {/* Connecting flow arrows */}
      <g opacity="0.4">
        <path d="M185 135 Q210 120 210 108" fill="none" stroke="#3b82f6" strokeWidth="1" strokeDasharray="4 3">
          <animate attributeName="stroke-dashoffset" values="14;0" dur="1.5s" repeatCount="indefinite" />
        </path>
        <path d="M270 108 Q270 120 295 135" fill="none" stroke="#22c55e" strokeWidth="1" strokeDasharray="4 3">
          <animate attributeName="stroke-dashoffset" values="14;0" dur="1.5s" repeatCount="indefinite" />
        </path>
      </g>

      {/* Floating particles */}
      <circle cx="100" cy="45" r="2" fill="#22c55e" opacity="0.3">
        <animate attributeName="cy" values="45;38;45" dur="4s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.3;0.6;0.3" dur="4s" repeatCount="indefinite" />
      </circle>
      <circle cx="380" cy="55" r="1.5" fill="#3b82f6" opacity="0.3">
        <animate attributeName="cy" values="55;48;55" dur="3s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.2;0.5;0.2" dur="3s" repeatCount="indefinite" />
      </circle>
      <circle cx="420" cy="180" r="2" fill="#22c55e" opacity="0.2">
        <animate attributeName="cy" values="180;172;180" dur="5s" repeatCount="indefinite" />
      </circle>
      <circle cx="50" cy="200" r="1.5" fill="#f59e0b" opacity="0.2">
        <animate attributeName="cy" values="200;194;200" dur="3.5s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}
