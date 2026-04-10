import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { ArrowRight, Star, Check, Clock, Mail, Globe, Sparkles, ChevronRight } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const HERO_BG = "https://static.prod-images.emergentagent.com/jobs/d92c6202-14d7-42b4-8759-6d0ad38d3b87/images/a494079b51d8f07b1ff49bb1f4fbfadc136a99c8cefb265c3b9ad973d7e47f1b.png";
const TEXTURE_BG = "https://static.prod-images.emergentagent.com/jobs/d92c6202-14d7-42b4-8759-6d0ad38d3b87/images/c7da8c345d2d6d233bfbc81d049272ea9736c6b374b2a44d877e340811f03d02.png";
const IMG_BUSINESS_CARD = "https://static.prod-images.emergentagent.com/jobs/d92c6202-14d7-42b4-8759-6d0ad38d3b87/images/16027425fe7f4010eb33e27f710912ad6282ccd6141f0c28a8cc9161d05e3a70.png";
const IMG_DIGITAL_CV = "https://images.unsplash.com/photo-1697292859784-c319e612ea15?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1ODR8MHwxfHNlYXJjaHwxfHxsdXh1cnklMjBzbWFydHBob25lJTIwc2NyZWVuJTIwbW9ja3VwJTIwZGFya3xlbnwwfHx8fDE3NzU4MTU2NTN8MA&ixlib=rb-4.1.0&q=85";
const TESTIMONIAL_1 = "https://images.unsplash.com/photo-1614700308520-bd630ab82471?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MTN8MHwxfHNlYXJjaHwzfHxlbGVnYW50JTIwYWZyaWNhbiUyMHByb2Zlc3Npb25hbCUyMHBvcnRyYWl0fGVufDB8fHx8MTc3NTgxNTY1M3ww&ixlib=rb-4.1.0&q=85";
const TESTIMONIAL_2 = "https://static.prod-images.emergentagent.com/jobs/d92c6202-14d7-42b4-8759-6d0ad38d3b87/images/12321d9f2256a0e34615b9ecc5eccc3b86e2ffe5320220aa1e2e7a3c5f58b87a.png";

const formatPrice = (price, currency = "XOF") => {
  if (currency === "XOF") {
    return `${price.toLocaleString("fr-FR")} FCFA`;
  }
  return `$${price.toFixed(2)}`;
};

export default function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const res = await axios.get(`${API}/products`);
      setProducts(res.data);
    } catch (err) {
      console.error("Error fetching products:", err);
    } finally {
      setLoading(false);
    }
  };

  const portfolioProducts = products.filter(p => p.is_service);
  const digitalProducts = products.filter(p => !p.is_service);

  return (
    <main className="min-h-screen bg-noir" data-testid="home-page">
      {/* ===== HERO SECTION ===== */}
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0">
          <img src={HERO_BG} alt="" className="w-full h-full object-cover object-top" />
          <div className="absolute inset-0 bg-gradient-to-r from-noir via-noir/80 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-noir via-transparent to-noir/40" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 lg:px-12 py-32">
          <div className="max-w-2xl">
            <div className="flex items-center gap-2 mb-8 opacity-0 animate-fade-up">
              <div className="h-px w-8 bg-champagne" />
              <span className="text-sm font-body font-medium tracking-[0.2em] uppercase text-champagne">
                Nouveau en Afrique Francophone
              </span>
            </div>

            <h1
              className="text-5xl sm:text-6xl tracking-tight leading-none font-heading font-semibold text-white mb-6 opacity-0 animate-fade-up stagger-1"
              data-testid="hero-heading"
            >
              Sublimez votre
              <br />
              <span className="text-champagne italic">Presence Digitale</span>
            </h1>

            <p className="text-lg text-zinc-400 leading-relaxed mb-10 max-w-lg opacity-0 animate-fade-up stagger-2">
              Portfolios sur-mesure, CV digitaux et identite visuelle en ligne.
              Faites de votre profil professionnel une oeuvre d'art.
            </p>

            <div className="flex flex-wrap gap-4 opacity-0 animate-fade-up stagger-3">
              <a
                href="#services"
                className="btn-gold inline-flex items-center gap-2 px-8 py-4 text-sm font-semibold tracking-wide"
                data-testid="hero-cta"
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById("services")?.scrollIntoView({ behavior: "smooth" });
                }}
              >
                Decouvrir nos offres
                <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
              </a>
              <Link
                to="/access"
                className="btn-outline-luxury inline-flex items-center gap-2 px-8 py-4 text-sm tracking-wide"
              >
                J'ai deja un code
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ===== SERVICES BENTO GRID ===== */}
      <section id="services" className="relative py-24 lg:py-32">
        <div className="absolute inset-0 opacity-30">
          <img src={TEXTURE_BG} alt="" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-noir/70" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 lg:px-12">
          <div className="mb-16">
            <p className="text-sm font-body font-medium tracking-[0.2em] uppercase text-champagne mb-4">
              Services Premium
            </p>
            <h2 className="text-3xl sm:text-4xl tracking-tight font-heading text-white">
              Digitalisation Professionnelle
            </h2>
            <p className="text-zinc-400 mt-4 max-w-xl text-base leading-relaxed">
              Des solutions sur-mesure pour transformer votre image professionnelle en ligne.
            </p>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className={`luxury-card p-8 ${i === 1 ? 'md:col-span-7' : 'md:col-span-5'}`}>
                  <div className="animate-pulse space-y-4">
                    <div className="h-40 bg-white/5 rounded" />
                    <div className="h-6 bg-white/5 rounded w-3/4" />
                    <div className="h-4 bg-white/5 rounded w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
              {portfolioProducts.map((product, idx) => {
                const isVip = product.name.toLowerCase().includes("vip");
                const colSpan = idx === 0 ? 'md:col-span-7' : idx === 1 ? 'md:col-span-5' : isVip ? 'md:col-span-12' : 'md:col-span-6';

                return (
                  <Link
                    key={product.id}
                    to={`/product/${product.id}`}
                    className={`group relative overflow-hidden ${colSpan} ${
                      isVip ? 'gold-border gold-glow' : 'luxury-card'
                    } ${!isVip ? 'luxury-card' : 'bg-surface transition-all duration-500 hover:-translate-y-1'}`}
                    data-testid={`portfolio-card-${product.id}`}
                  >
                    {isVip && (
                      <div className="absolute top-4 right-4 z-10 flex items-center gap-1.5 px-3 py-1 bg-champagne text-noir text-xs font-bold tracking-wider uppercase">
                        <Star className="w-3 h-3" fill="currentColor" strokeWidth={0} />
                        VIP
                      </div>
                    )}

                    <div className="flex flex-col md:flex-row">
                      <div className={`relative overflow-hidden ${isVip ? 'md:w-1/2' : 'w-full'}`}>
                        <img
                          src={product.image_url || IMG_DIGITAL_CV}
                          alt={product.name}
                          className="w-full h-56 md:h-full object-cover group-hover:scale-[1.02] transition-transform duration-700"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-surface/60 to-transparent" />
                      </div>

                      <div className={`p-8 flex flex-col justify-between ${isVip ? 'md:w-1/2' : ''}`}>
                        <div>
                          <h3 className="text-2xl font-heading font-semibold text-white mb-3 group-hover:text-champagne transition-colors">
                            {product.name}
                          </h3>
                          <p className="text-sm text-zinc-400 leading-relaxed mb-6">
                            {product.description}
                          </p>
                          {product.features && product.features.length > 0 && (
                            <ul className="space-y-2 mb-6">
                              {product.features.map((f, i) => (
                                <li key={i} className="flex items-center gap-2 text-sm text-zinc-300">
                                  <Check className="w-4 h-4 text-champagne flex-shrink-0" strokeWidth={1.5} />
                                  {f}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                        <div className="flex items-center justify-between mt-4">
                          <span className="text-2xl font-heading font-bold text-champagne">
                            {formatPrice(product.price, product.currency)}
                          </span>
                          <span className="text-sm text-zinc-400 group-hover:text-champagne transition-colors flex items-center gap-1">
                            Commander <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
                          </span>
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section className="py-24 border-y border-white/5">
        <div className="max-w-5xl mx-auto px-6 lg:px-12">
          <div className="text-center mb-16">
            <p className="text-sm font-body tracking-[0.2em] uppercase text-champagne mb-4">Processus</p>
            <h2 className="text-3xl sm:text-4xl tracking-tight font-heading text-white">
              Comment ca marche ?
            </h2>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: 1, icon: Globe, title: "Choisissez", desc: "Selectionnez la formule adaptee a vos besoins" },
              { step: 2, icon: Mail, title: "Remplissez", desc: "Completez le formulaire avec vos informations" },
              { step: 3, icon: Sparkles, title: "On cree", desc: "Notre equipe design votre presence digitale" },
              { step: 4, icon: Clock, title: "Recevez", desc: "Votre site est livre sous 48-72h par email" },
            ].map((item) => (
              <div key={item.step} className="text-center group">
                <div className="relative mx-auto mb-6">
                  <div className="w-16 h-16 border border-white/10 flex items-center justify-center mx-auto group-hover:border-champagne/30 transition-colors">
                    <item.icon className="w-6 h-6 text-champagne" strokeWidth={1.5} />
                  </div>
                  <div className="absolute -top-2 -right-2 w-6 h-6 bg-champagne text-noir text-xs font-bold flex items-center justify-center">
                    {item.step}
                  </div>
                </div>
                <h3 className="font-heading text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-sm text-zinc-500 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== TESTIMONIALS ===== */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="mb-16">
            <p className="text-sm font-body tracking-[0.2em] uppercase text-champagne mb-4">Temoignages</p>
            <h2 className="text-3xl sm:text-4xl tracking-tight font-heading text-white">
              Ils nous font confiance
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {[
              {
                name: "Kouame Olivier",
                role: "Consultant en Management",
                text: "Mon portfolio m'a permis de decrocher 3 nouveaux clients en un mois. L'investissement en valait largement la peine.",
                img: TESTIMONIAL_1
              },
              {
                name: "Ama Konan",
                role: "Directrice Marketing",
                text: "Un travail exceptionnel. Mon profil en ligne reflete enfin le niveau de professionnalisme que je veux montrer.",
                img: TESTIMONIAL_2
              }
            ].map((t, i) => (
              <div key={i} className="luxury-card p-8 flex gap-6">
                <img src={t.img} alt={t.name} className="w-16 h-16 object-cover rounded-full flex-shrink-0 border border-white/10" />
                <div>
                  <div className="flex gap-1 mb-3">
                    {[1, 2, 3, 4, 5].map(s => (
                      <Star key={s} className="w-4 h-4 text-champagne" fill="currentColor" strokeWidth={0} />
                    ))}
                  </div>
                  <p className="text-zinc-300 text-sm leading-relaxed italic mb-4">"{t.text}"</p>
                  <p className="text-white font-semibold text-sm">{t.name}</p>
                  <p className="text-zinc-500 text-xs">{t.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== DIGITAL PRODUCTS ===== */}
      {digitalProducts.length > 0 && (
        <section id="products" className="py-24 border-t border-white/5">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="mb-16">
              <p className="text-sm font-body tracking-[0.2em] uppercase text-champagne mb-4">Ressources</p>
              <h2 className="text-3xl sm:text-4xl tracking-tight font-heading text-white">
                Produits Numeriques
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {digitalProducts.map((product) => (
                <Link
                  key={product.id}
                  to={`/product/${product.id}`}
                  className="group luxury-card overflow-hidden"
                  data-testid={`product-card-${product.id}`}
                >
                  <div className="relative overflow-hidden">
                    <img
                      src={product.image_url || IMG_DIGITAL_CV}
                      alt={product.name}
                      className="w-full h-48 object-cover group-hover:scale-[1.02] transition-transform duration-700"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-surface to-transparent" />
                    <div className="absolute bottom-3 left-3">
                      <span className="text-xs font-body font-medium tracking-wider uppercase text-champagne bg-noir/70 px-2 py-1">
                        {product.category === "ebook" ? "E-book" : product.category === "template" ? "Template" : product.category}
                      </span>
                    </div>
                  </div>
                  <div className="p-6">
                    <h3 className="font-heading text-xl font-semibold text-white mb-2 group-hover:text-champagne transition-colors">
                      {product.name}
                    </h3>
                    <p className="text-sm text-zinc-500 mb-4 line-clamp-2 leading-relaxed">
                      {product.description}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-xl font-heading font-bold text-champagne">
                        {formatPrice(product.price, product.currency)}
                      </span>
                      <span className="text-xs text-zinc-500 group-hover:text-champagne transition-colors flex items-center gap-1">
                        Acheter <ChevronRight className="w-3 h-3" strokeWidth={1.5} />
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ===== FOOTER ===== */}
      <footer className="border-t border-white/5 py-12">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-champagne flex items-center justify-center">
                <Sparkles className="w-3 h-3 text-noir" strokeWidth={1.5} />
              </div>
              <span className="font-heading text-lg text-white">NumStore</span>
            </div>
            <p className="text-xs text-zinc-600">
              NumStore — Produits Numeriques & Digitalisation Professionnelle
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
