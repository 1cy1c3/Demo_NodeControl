import React, { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  Card,
  Button,
  Container,
  Row,
  Col,
  Modal,
  Spinner,
} from "react-bootstrap";
import { instanceSetup, createWallet, setupProject } from "../services/auth";
import { QRCodeSVG } from "qrcode.react";

interface Product {
  id: number;
  name: string;
  price: number;
  description: string;
  network: string;
  features: string[];
}

// Dummy product data -> Frontend Database
const products: Product[] = [
  {
    id: 1,
    name: "Elixir",
    price: 4.99,
    description:
      "The Elixir Network is a new primitive, built from the ground up to power liquidity across orderbook exchanges.",
    features: ["99.9% Uptime", "24/7 Support"],
    network: "ethereum",
  },
  {
    id: 2,
    name: "DUMMY",
    price: 499.99,
    description:
      "The Elixir Network is a new primitive, built from the ground up to power liquidity across orderbook exchanges.",
    features: ["99.9% Uptime", "24/7 Support"],
    network: "ethereum",
  },
  {
    id: 3,
    name: "DUMMY",
    price: 499.99,
    description:
      "The Elixir Network is a new primitive, built from the ground up to power liquidity across orderbook exchanges.",
    network: "ethereum",
    features: ["99.9% Uptime", "24/7 Support"],
  },
  {
    id: 4,
    name: "DUMMY",
    price: 499.99,
    description:
      "The Elixir Network is a new primitive, built from the ground up to power liquidity across orderbook exchanges.",
    network: "ethereum",
    features: ["99.9% Uptime", "24/7 Support"],
  },
  {
    id: 5,
    name: "DUMMY",
    price: 499.99,
    description:
      "The Elixir Network is a new primitive, built from the ground up to power liquidity across orderbook exchanges.",
    network: "ethereum",
    features: ["99.9% Uptime", "24/7 Support"],
  },
  {
    id: 6,
    name: "DUMMY",
    price: 499.99,
    description:
      "The Elixir Network is a new primitive, built from the ground up to power liquidity across orderbook exchanges.",
    network: "ethereum",
    features: ["99.9% Uptime", "24/7 Support"],
  },
];

const ProductPage: React.FC = () => {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return document.body.classList.contains("dark-mode");
  });
  const [setupStage, setSetupStage] = useState<
    | "idle"
    | "instanceSetup"
    | "walletCreated"
    | "projectSetup"
    | "complete"
    | "error"
  >("idle");
  const [walletAddress, setWalletAddress] = useState<string>("");

  useEffect(() => {
    const darkModeObserver = new MutationObserver(() => {
      setIsDarkMode(document.body.classList.contains("dark-mode"));
    });

    darkModeObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ["class"],
    });

    return () => darkModeObserver.disconnect();
  }, []);

  const handleProductClick = (product: Product) => {
    setSelectedProduct(product);
  };

  const { userId } = useAuth();

  const handleSubscribe = async (productId: number, productNetwork: string) => {
    if (userId) {
      try {
        setSetupStage("instanceSetup");
        const userProjectId: number = await instanceSetup(userId, productId);

        const pubKey: string = await createWallet(
          productNetwork,
          userProjectId
        );
        setWalletAddress(pubKey);
        setSetupStage("walletCreated");

        setSetupStage("projectSetup");
        await setupProject(userProjectId);

        setSetupStage("complete");
      } catch (error) {
        console.error("Subscription failed:", error);
        setSetupStage("error");
      }
    }
  };

  const handleCloseModal = () => {
    setSelectedProduct(null);
    setSetupStage("idle");
    setWalletAddress("");
  };

  const renderSetupContent = () => {
    switch (setupStage) {
      case "instanceSetup":
        return (
          <div className="text-center">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
            <p className="mt-3">Setting up your instance...</p>
          </div>
        );
      case "walletCreated":
      case "projectSetup":
      case "complete":
        return (
          <div className="text-center">
            <h4>Wallet Created Successfully!</h4>
            <p>Your wallet address:</p>
            <p className="font-monospace">{walletAddress}</p>
            <div className="mt-3">
              {walletAddress && (
                <QRCodeSVG
                  value={walletAddress}
                  size={150}
                  level={"H"}
                  includeMargin={true}
                />
              )}
            </div>
            {setupStage === "projectSetup" && (
              <p className="mt-3">
                Instance setup complete! Please fund your wallet now to activate
                your subscription
              </p>
            )}
            {setupStage === "complete" && (
              <p className="mt-3">
                Setup complete! Your Node is running.
              </p>
            )}
          </div>
        );
      case "error":
        return (
          <div className="text-center text-danger">
            <p>
              An error occurred during the setup process. Please try again
              later.
            </p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <Container
      fluid
      className={`py-5 ${
        isDarkMode ? "bg-dark text-light" : "bg-light text-dark"
      }`}
    >
      <h1
        className={`text-center mb-5 ${
          isDarkMode ? "bg-dark text-light" : "bg-light text-dark"
        }`}
      >
        Our Products
      </h1>
      <Row xs={1} md={2} lg={3} className="g-4">
        {products.map((product) => (
          <Col key={product.id}>
            <Card
              className={`h-100 shadow-sm transition-transform hover-lift ${
                isDarkMode
                  ? "text-light bg-dark border-light"
                  : "text-dark bg-light border-secondary"
              }`}
              style={{ cursor: "pointer" }}
              onClick={() => handleProductClick(product)}
            >
              <Card.Body>
                <Card.Title>{product.name}</Card.Title>
                <Card.Text>{product.description}</Card.Text>
                <h3 className="mb-3">${product.price.toFixed(2)}/month</h3>
                <Button
                  variant={isDarkMode ? "outline-light" : "outline-primary"}
                >
                  Learn More
                </Button>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      <Modal
        show={selectedProduct !== null}
        onHide={handleCloseModal}
        size="lg"
        contentClassName={isDarkMode ? "bg-dark text-light" : ""}
      >
        {selectedProduct && (
          <>
            <Modal.Header closeButton>
              <Modal.Title>{selectedProduct.name}</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              {setupStage === "idle" ? (
                <>
                  <h3 className="mb-3">
                    ${selectedProduct.price.toFixed(2)}/month
                  </h3>
                  <p>{selectedProduct.description}</p>
                  <h5>Features:</h5>
                  <ul>
                    {selectedProduct.features.map((feature, index) => (
                      <li key={index}>{feature}</li>
                    ))}
                  </ul>
                </>
              ) : (
                renderSetupContent()
              )}
            </Modal.Body>
            <Modal.Footer>
              <Button
                variant={isDarkMode ? "secondary" : "secondary"}
                onClick={handleCloseModal}
              >
                Close
              </Button>
              {userId && setupStage === "idle" && (
                <Button
                  variant={isDarkMode ? "light" : "primary"}
                  onClick={() =>
                    handleSubscribe(selectedProduct.id, selectedProduct.network)
                  }
                >
                  Subscribe Now
                </Button>
              )}
            </Modal.Footer>
          </>
        )}
      </Modal>
    </Container>
  );
};

export default ProductPage;
