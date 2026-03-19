"use client";

export default function SearchIllustration() {
  return (
    <svg
      viewBox="0 0 400 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full max-w-md"
    >
      <defs>
        <radialGradient id="searchGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
        </radialGradient>
      </defs>

      <ellipse cx="200" cy="60" rx="180" ry="55" fill="url(#searchGlow)" />

      {/* Magnifying glass */}
      <g className="animate-float">
        <circle cx="80" cy="55" r="25" fill="none" stroke="#3b82f6" strokeWidth="2" opacity="0.6" />
        <circle cx="80" cy="55" r="25" fill="none" stroke="#3b82f6" strokeWidth="1" opacity="0.3">
          <animate attributeName="r" values="25;30;25" dur="3s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.3;0;0.3" dur="3s" repeatCount="indefinite" />
        </circle>
        <line x1="98" y1="73" x2="112" y2="87" stroke="#3b82f6" strokeWidth="3" strokeLinecap="round" opacity="0.6" />
        {/* Search lines inside */}
        <rect x="66" y="46" width="18" height="3" rx="1.5" fill="#3b82f6" opacity="0.3">
          <animate attributeName="width" values="10;18;10" dur="2s" repeatCount="indefinite" />
        </rect>
        <rect x="66" y="53" width="28" height="3" rx="1.5" fill="#3b82f6" opacity="0.3">
          <animate attributeName="width" values="28;16;28" dur="2s" repeatCount="indefinite" />
        </rect>
        <rect x="66" y="60" width="22" height="3" rx="1.5" fill="#3b82f6" opacity="0.3">
          <animate attributeName="width" values="14;22;14" dur="2s" repeatCount="indefinite" />
        </rect>
      </g>

      {/* Scanning dots */}
      <g>
        <circle cx="140" cy="40" r="2" fill="#3b82f6" opacity="0">
          <animate attributeName="opacity" values="0;0.6;0" dur="1.5s" begin="0s" repeatCount="indefinite" />
          <animate attributeName="cx" values="130;150" dur="1.5s" begin="0s" repeatCount="indefinite" />
        </circle>
        <circle cx="140" cy="60" r="2" fill="#22c55e" opacity="0">
          <animate attributeName="opacity" values="0;0.6;0" dur="1.5s" begin="0.3s" repeatCount="indefinite" />
          <animate attributeName="cx" values="130;150" dur="1.5s" begin="0.3s" repeatCount="indefinite" />
        </circle>
        <circle cx="140" cy="80" r="2" fill="#f59e0b" opacity="0">
          <animate attributeName="opacity" values="0;0.6;0" dur="1.5s" begin="0.6s" repeatCount="indefinite" />
          <animate attributeName="cx" values="130;150" dur="1.5s" begin="0.6s" repeatCount="indefinite" />
        </circle>
      </g>

      {/* Result cards stacking */}
      <g>
        {/* Card 1 - back */}
        <rect x="170" y="30" width="100" height="24" rx="5" fill="#1e1e2a" stroke="#2a2a3a" strokeWidth="0.8" opacity="0.5">
          <animate attributeName="opacity" values="0;0.5" dur="0.8s" fill="freeze" />
        </rect>
        <circle cx="184" cy="42" r="5" fill="#22c55e" opacity="0.2" />
        <rect x="194" y="39" width="50" height="3" rx="1.5" fill="#2a2a3a" />

        {/* Card 2 - middle */}
        <rect x="170" y="50" width="100" height="24" rx="5" fill="#1e1e2a" stroke="#2a2a3a" strokeWidth="0.8" opacity="0.7">
          <animate attributeName="opacity" values="0;0.7" dur="0.8s" begin="0.3s" fill="freeze" />
        </rect>
        <circle cx="184" cy="62" r="5" fill="#f59e0b" opacity="0.2" />
        <rect x="194" y="59" width="40" height="3" rx="1.5" fill="#2a2a3a" />

        {/* Card 3 - front (highlighted) */}
        <rect x="170" y="70" width="100" height="24" rx="5" fill="#1e1e2a" stroke="#3b82f6" strokeWidth="1" opacity="0.9">
          <animate attributeName="opacity" values="0;0.9" dur="0.8s" begin="0.6s" fill="freeze" />
        </rect>
        <circle cx="184" cy="82" r="5" fill="#3b82f6" opacity="0.3" />
        <rect x="194" y="79" width="55" height="3" rx="1.5" fill="#3b82f6" opacity="0.3" />
        <path d="M256 79 L260 83 L268 75" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.6">
          <animate attributeName="opacity" values="0;0.6" dur="0.5s" begin="1s" fill="freeze" />
        </path>
      </g>

      {/* Detail panel */}
      <g className="animate-float-delayed">
        <rect x="290" y="20" width="90" height="80" rx="8" fill="#1e1e2a" stroke="#2a2a3a" strokeWidth="1" />
        {/* Status badge */}
        <rect x="302" y="32" width="45" height="14" rx="7" fill="#22c55e" opacity="0.15" />
        <circle cx="311" cy="39" r="3" fill="#22c55e" opacity="0.6">
          <animate attributeName="opacity" values="0.4;0.8;0.4" dur="2s" repeatCount="indefinite" />
        </circle>
        <rect x="318" y="37" width="24" height="3" rx="1.5" fill="#22c55e" opacity="0.4" />
        {/* Detail lines */}
        <rect x="302" y="54" width="66" height="3" rx="1.5" fill="#2a2a3a" />
        <rect x="302" y="63" width="50" height="3" rx="1.5" fill="#2a2a3a" opacity="0.7" />
        <rect x="302" y="72" width="58" height="3" rx="1.5" fill="#2a2a3a" opacity="0.5" />
        {/* Progress bar */}
        <rect x="302" y="82" width="66" height="4" rx="2" fill="#2a2a3a" />
        <rect x="302" y="82" width="0" height="4" rx="2" fill="#22c55e" opacity="0.6">
          <animate attributeName="width" values="0;44;44" dur="2s" repeatCount="indefinite" />
        </rect>
      </g>
    </svg>
  );
}
