import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import ProductPage from "./pages/ProductPage";
import AccessPage from "./pages/AccessPage";
import PortfolioForm from "./pages/PortfolioForm";
import PortfolioSuccess from "./pages/PortfolioSuccess";
import AdminLogin from "./pages/admin/AdminLogin";
import AdminDashboard from "./pages/admin/Dashboard";
import AdminProducts from "./pages/admin/Products";
import AdminPortfolios from "./pages/admin/Portfolios";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-noir text-white">
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/product/:id" element={<ProductPage />} />
          <Route path="/access" element={<AccessPage />} />
          <Route path="/portfolio/form" element={<PortfolioForm />} />
          <Route path="/portfolio/success" element={<PortfolioSuccess />} />
          <Route path="/admin" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/admin/products" element={<AdminProducts />} />
          <Route path="/admin/portfolios" element={<AdminPortfolios />} />
        </Routes>
      </div>
      <Toaster position="top-right" richColors />
    </BrowserRouter>
  );
}

export default App;
