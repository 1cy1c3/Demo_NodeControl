import React from "react";

const HomePage: React.FC = () => {
  return (
    <div className="container-fluid p-0" style={{ paddingBottom: 0 }}>
      {/* Hero Section */}
      <section
        className="text-center d-flex align-items-center justify-content-center"
        style={{
          backgroundImage: 'url("/banner-homepage.png")',
          backgroundSize: "cover",
          backgroundPosition: "center",
          height: "800px",
          color: "white",
        }}
      >
        <div className="container">
          <h1 className="display-2 text-light">
            Effortless Blockchain Node Hosting
          </h1>
          <p className="lead mb-4 text-light">
            No technical skills? No problem. Deploy and manage nodes seamlessly.
          </p>
          <a href="/products" className="btn btn-secondary btn-lg">
            Get Started
          </a>
        </div>
      </section>

      {/* Features Section */}
      <section className="container py-5">
        <div className="row text-center py-5">
          {[
            {
              src: "automation.svg",
              alt: "Node Automation",
              title: "Automated Node Deployment",
              description:
                "Set up blockchain nodes in seconds with our streamlined process.",
            },
            {
              src: "security-shield.png",
              alt: "Secure",
              title: "Secure & Reliable",
              description:
                "We prioritize security and uptime so you don't have to worry about downtime.",
            },
            {
              src: "scalability.png",
              alt: "Scalability",
              title: "Scalability on Demand",
              description:
                "Easily scale up your node infrastructure as your project grows.",
            },
          ].map((feature, index) => (
            <div key={index} className="col-md-4 mb-4">
              <div className="d-flex flex-column align-items-center">
                <div
                  className="image-container mb-3"
                  style={{
                    width: "300px",
                    height: "300px",
                    overflow: "hidden",
                  }}
                >
                  <img
                    src={feature.src}
                    alt={feature.alt}
                    className="img-fluid"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                    }}
                  />
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Why Choose Us Section */}
      <section className="text-center py-5 bg-light dark:bg-dark">
        <h2 className="mb-4">Why Choose Our Platform?</h2>
        <p className="lead mb-5">
          Simplifying blockchain node hosting for everyone.
        </p>
        <div className="row justify-content-center">
          <div className="col-md-8">
            <ul className="list-unstyled text-start">
              <li className="mb-4">✔ User-friendly, no coding required</li>
              <li className="mb-4">✔ Supports multiple blockchain protocols</li>
              <li className="mb-4">
                ✔ 24/7 monitoring with real-time analytics
              </li>
              <li className="mb-4">
                ✔ Competitive pricing with flexible plans
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Join Section */}
      <section
        className="text-center py-5 bg-light"
        style={{ marginBottom: "0", paddingBottom: "0" }}
      >
        <div className="container">
          <h2 className="display-4 mb-4">
            Join the Decentralization Revolution
          </h2>
          <p className="lead mb-5">
            Start hosting blockchain nodes today, with just a few clicks.
          </p>
          <a href="/login" className="btn btn-outline-secondary btn-lg">
            Sign Up Now
          </a>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
