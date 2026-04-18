import './AcademicBotLogo.css';

//Props to control logo size, color, animation mode, and accessibility labeling.
interface AcademicBotLogoProps {
  size?: number;
  color?: string;
  animated?: boolean;
  className?: string;
  ariaLabel?: string;
}

// Shows the Daleel KU SVG logo.
export default function AcademicBotLogo({ size, color, animated = true, className: extraClass, ariaLabel }: AcademicBotLogoProps) {
  //Use a static style when animation is off, then add any extra class name.
  const className = `${animated ? 'academic-bot-logo' : 'academic-bot-logo academic-bot-logo--static'}${extraClass ? ` ${extraClass}` : ''}`;
  const style: React.CSSProperties = {};
  if (size) style.width = `${size}px`;
  if (color) style.color = color;

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 4 24 30"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={style}
      //With ariaLabel, screen readers read this SVG as an image; without it, they ignore it as decoration.
      role={ariaLabel ? 'img' : 'presentation'}
      aria-label={ariaLabel}
      aria-hidden={ariaLabel ? undefined : 'true'}
    >
      <g transform="translate(0, 1.5)">
        <path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z" />
        <path d="M22 10v6" />
        <path d="M6 12.5 V18.5 M18 12.5 V18.5" />
      </g>

      <g transform="translate(0, 12)">
        <rect width="16" height="12" x="4" y="8" rx="2" />
        <path d="M2 14h2" />
        <path d="M20 14h2" />
        <path className="right-eye" d="M15 13v2" />
        <path d="M9 13v2" />
      </g>
    </svg>
  );
}