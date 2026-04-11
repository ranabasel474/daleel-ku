import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AcademicBotLogo from "@/components/AcademicBotLogo";

// Splash screen: displays logo and app name, then auto-navigates to /chat after a fade-out.
const Landing = () => {
  const navigate = useNavigate();
  const [fading, setFading] = useState(false);

  useEffect(() => {
    // Two timers so the fade transition (500 ms) completes before navigation unmounts the component.
    const fadeTimer = setTimeout(() => {
      setFading(true);
    }, 1700);

    const navTimer = setTimeout(() => {
      navigate("/chat");
    }, 2210);

    // Prevents state updates on an unmounted component if the user navigates away early.
    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(navTimer);
    };
  }, [navigate]);

  return (
    <div
      className="landing-container transition-opacity duration-500 ease-out"
      style={{ opacity: fading ? 0 : 1 }}
    >
      <AcademicBotLogo className="landing-logo" />
      <h1
        style={{
          fontFamily: "'Somar', sans-serif",
          color: "#F8D81B",
          opacity: 0,
          // Starts hidden; keyframe reveals it after the logo has settled.
          animation: "landingTextIn 0.5s ease-out 0.6s forwards",
        }}
        className="text-4xl font-bold mt-4 text-center tracking-wide"
      >
        DALEEL KU
      </h1>
      <p
        style={{
          fontFamily: "'Somar', sans-serif",
          color: "#F8D81B",
          direction: "rtl",
          opacity: 0,
          // 150 ms after the title to stagger the entrance.
          animation: "landingTextIn 0.5s ease-out 0.75s forwards",
        }}
        className="mt-2 text-center text-base"
      >
        دليلك الأكاديمي لجامعة الكويت
      </p>
    </div>
  );
};

export default Landing;
