import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AcademicBotLogo from "@/components/AcademicBotLogo";

//Short introductory animation that navigates to the main chat interface.
const Landing = () => {
  const navigate = useNavigate();
  const [fading, setFading] = useState(false);

  useEffect(() => {
    //Two timers so the 500 ms fade finishes before navigation removes the component
    const fadeTimer = setTimeout(() => {
      setFading(true);
    }, 1700);

    const navTimer = setTimeout(() => {
      navigate("/chat");
    }, 2210);

    //Cancels both timers if the user navigates away before the intro finishes
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
          //Delayed 0.6s so the logo settles before the title appears
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
          //150ms after the title so the subtitle appears in sequence
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
