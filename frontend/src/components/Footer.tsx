import React, { useState, useEffect } from "react";

const Footer: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    // Check for the dark-mode class on the body to determine the initial state
    setIsDarkMode(document.body.classList.contains("dark-mode"));

    // Add an event listener to update the state when the dark-mode class changes
    const observer = new MutationObserver(() => {
      setIsDarkMode(document.body.classList.contains("dark-mode"));
    });
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ["class"],
    });

    return () => observer.disconnect();
  }, []);

  const footerStyle = {
    backgroundColor: isDarkMode ? "#000000" : "#ffffff",
    color: isDarkMode ? "#ffffff" : "#000000",
    padding: "1rem 0",
    marginTop: "0",
  };

  return (
    <footer style={footerStyle}>
      <div className="text-center">© 2024 My App</div>
    </footer>
  );
};

export default Footer;
