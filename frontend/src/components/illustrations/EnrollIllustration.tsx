"use client";

export default function EnrollIllustration() {
  return (
    <svg
      viewBox="0 0 400 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full max-w-md"
    >
      <defs>
        <radialGradient id="enrollGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#22c55e" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
        </radialGradient>
      </defs>

      <ellipse cx="200" cy="60" rx="180" ry="55" fill="url(#enrollGlow)" />

      {/* Form icon */}
      <rect x="30" y="15" width="70" height="90" rx="8" fill="#1e1e2a" stroke="#2a2a3a" strokeWidth="1" />
      <rect x="42" y="30" width="30" height="4" rx="2" fill="#3b82f6" opacity="0.5" />
      <rect x="42" y="42" width="46" height="3" rx="1.5" fill="#2a2a3a" />
      <rect x="42" y="52" width="38" height="3" rx="1.5" fill="#2a2a3a" />
      <rect x="42" y="62" width="42" height="3" rx="1.5" fill="#2a2a3a" />
      {/* Pen writing animation */}
      <g>
        <path d="M80 75 L88 67 L92 71 L84 79 Z" fill="#22c55e" opacity="0.7">
          <animate attributeName="opacity" values="0.5;0.8;0.5" dur="2s" repeatCount="indefinite" />
        </path>
        <line x1="42" y1="78" x2="75" y2="78" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" opacity="0.4">
          <animate attributeName="x2" values="42;75" dur="2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0;0.4;0.4" dur="2s" repeatCount="indefinite" />
        </line>
      </g>

      {/* Arrow */}
      <g opacity="0.5">
        <line x1="115" y1="60" x2="150" y2="60" stroke="#22c55e" strokeWidth="1.5" strokeDasharray="4 3">
          <animate attributeName="stroke-dashoffset" values="14;0" dur="1s" repeatCount="indefinite" />
        </line>
        <path d="M148 55 L156 60 L148 65" stroke="#22c55e" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      </g>

      {/* Benefits cards fan */}
      <g className="animate-float-slow">
        <rect x="165" y="25" width="60" height="35" rx="6" fill="#1e1e2a" stroke="#22c55e" strokeWidth="0.8" opacity="0.7" transform="rotate(-5 195 42)" />
        <text x="178" y="47" fill="#22c55e" fontSize="8" fontFamily="system-ui" opacity="0.7">Medical</text>
      </g>
      <g className="animate-float">
        <rect x="175" y="35" width="60" height="35" rx="6" fill="#1e1e2a" stroke="#3b82f6" strokeWidth="0.8" opacity="0.8" />
        <text x="190" y="57" fill="#3b82f6" fontSize="8" fontFamily="system-ui" opacity="0.7">Dental</text>
      </g>
      <g className="animate-float-delayed">
        <rect x="185" y="45" width="60" height="35" rx="6" fill="#1e1e2a" stroke="#f59e0b" strokeWidth="0.8" opacity="0.7" transform="rotate(5 215 62)" />
        <text x="200" y="67" fill="#f59e0b" fontSize="8" fontFamily="system-ui" opacity="0.7">Vision</text>
      </g>

      {/* Arrow */}
      <g opacity="0.5">
        <line x1="260" y1="60" x2="295" y2="60" stroke="#22c55e" strokeWidth="1.5" strokeDasharray="4 3">
          <animate attributeName="stroke-dashoffset" values="14;0" dur="1s" repeatCount="indefinite" />
        </line>
        <path d="M293 55 L301 60 L293 65" stroke="#22c55e" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      </g>

      {/* Submit button / success */}
      <g>
        <rect x="310" y="35" width="65" height="50" rx="10" fill="#22c55e" opacity="0.12" stroke="#22c55e" strokeWidth="1" />
        <circle cx="342" cy="55" r="14" fill="none" stroke="#22c55e" strokeWidth="1.5">
          <animate attributeName="r" values="12;16;12" dur="3s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.6;0.3;0.6" dur="3s" repeatCount="indefinite" />
        </circle>
        <path d="M334 55 L340 61 L352 49" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <animate attributeName="stroke-dasharray" values="0 30;30 0" dur="1.5s" fill="freeze" />
        </path>
      </g>
    </svg>
  );
}
