import React, { useEffect } from "react";
import "./ThankYou.css";

export default function ThankYou() {
  // Block back button — push a dummy entry so pressing back stays here
  useEffect(() => {
    // Clear student session so they can't re-enter quiz
    localStorage.removeItem('studentId');
    localStorage.removeItem('studentEntry');

    // Push a dummy state so pressing back hits this handler instead of /quiz
    window.history.pushState(null, '', window.location.href);
    const blockBack = () => {
      window.history.pushState(null, '', window.location.href);
    };
    window.addEventListener('popstate', blockBack);
    return () => window.removeEventListener('popstate', blockBack);
  }, []);


  return (
    <div className="thank-you-page">
      {/* Header section */}
      <header className="header">
        <div className="headerContent">
          <div className="logoGroup">
            <img
              src="https://cdn.builder.io/api/v1/image/assets/TEMP/67c6115c241c209d7b06387f86f8e92ba55fdc9b"
              alt="College Logo"
              className="logo"
            />
            <img
              src="https://cdn.builder.io/api/v1/image/assets/TEMP/5c7a6da01525a739302af9dc78a7647e418853db"
              alt="Institution Logo"
              className="instituteLogo"
            />
            <p className="autonomousText">
              (JCTCET is An Autonomous Institution)
            </p>
          </div>

          <nav className="navigation">
            <a href="#home" className="navLink">
              Home
            </a>
            <a href="#college" className="navLink">
              College
            </a>
          </nav>

          <button className="mobileMenuButton" aria-label="Toggle menu">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
              fill="none"
            >
              <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
              <path d="M4 6l16 0"></path>
              <path d="M4 12l16 0"></path>
              <path d="M4 18l16 0"></path>
            </svg>
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="main-content">
        <div className="thankyou-container">
          <h2 className="thankyou-text">Thankyou</h2>
        </div>
        <div className="cat-image-container">
          <img src="https://static.codia.ai/image/2025-03-17/592a80f8-3175-4266-b880-f95e782df76b.png" alt="Thank you cat" className="cat-image" />
        </div>
      </main>

      {/* Footer section */}
      <footer className="footer">
        <div>
          <h3 className="footerHeading">Contact Us</h3>
          <p className="footerText" href="https://www.jct.ac.in/" onClick={() => window.location.href = 'https://www.jct.ac.in/'}>https://www.jct.ac.in/</p>
          <p className="footerText" onClick={() => {}}>Phone: +91 9361488801</p>
        </div>
        <div>
          <h3 className="footerHeading">Follow us</h3>
          <div className="socialContainer">
            <a href="https://www.facebook.com/jctgroups/" aria-label="Facebook">facebook
            </a>
            <a href="https://www.instagram.com/jct_college/" aria-label="Instagram">instagram
            </a>
          </div>
        </div>
        <div>
          <h3 className="faqText">FAQ</h3>
        </div>
      </footer>
    </div>
  );
}