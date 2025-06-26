"use client";

import { Button } from "@/components/ui/button";
import {
  Database,
  Code2,
  Zap,
  Shield,
  ArrowRight,
  Sparkles,
  Brain,
  Clock,
  Users,
  CheckCircle,
  Play,
  Star,
  Github,
  Twitter,
  Award,
  Globe,
  Layers,
} from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ModeToggle } from "@/components/mode-toggle";

// Animation variants
const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6 }
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

export default function LandingPage() {
  const testimonials = [
    {
      name: "Sarah Chen",
      role: "Lead Developer at TechCorp",
      content: "SchemaSage saved us weeks of work. The AI-powered schema detection is incredibly accurate.",
      avatar: "SC",
      rating: 5
    },
    {
      name: "Marcus Johnson",
      role: "Data Architect at DataFlow",
      content: "The code generation feature is a game-changer. Perfect TypeScript interfaces every time.",
      avatar: "MJ",
      rating: 5
    },
    {
      name: "Emily Rodriguez",
      role: "Full Stack Engineer",
      content: "Finally, a tool that understands complex data relationships. The ER diagrams are beautiful!",
      avatar: "ER",
      rating: 5
    }
  ];
  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    
    // Testimonial rotation
    const testimonialInterval = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);

    return () => {
      clearInterval(testimonialInterval);
    };
  }, [testimonials.length]);

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Detection",
      description: "Advanced machine learning algorithms analyze your data patterns and automatically infer optimal database schemas.",
      gradient: "from-slate-500 to-blue-500"
    },
    {
      icon: Code2,
      title: "Multi-Language Code Gen",
      description: "Generate TypeScript, Python, SQL, Go, and more with perfect type safety and industry best practices.",
      gradient: "from-blue-500 to-teal-500"
    },
    {
      icon: Zap,
      title: "Lightning Fast",
      description: "Process thousands of records in seconds. Our optimized engine handles large datasets effortlessly.",
      gradient: "from-teal-500 to-slate-500"
    },
    {
      icon: Layers,
      title: "Visual Schema Builder",
      description: "Interactive drag-and-drop interface with real-time preview and relationship mapping.",
      gradient: "from-slate-600 to-teal-600"
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "Bank-grade encryption, SOC 2 compliant, with role-based access control and audit logging.",
      gradient: "from-blue-600 to-slate-600"
    },
    {
      icon: Globe,
      title: "Team Collaboration",
      description: "Real-time collaboration with version control, comments, and approval workflows.",
      gradient: "from-teal-600 to-blue-600"
    }
  ];

  const howItWorks = [
    {
      icon: <Database className="w-8 h-8 text-blue-500" />,
      title: "Connect & Upload",
      desc: "Securely connect your databases or upload your schema/data files."
    },
    {
      icon: <Brain className="w-8 h-8 text-teal-500" />,
      title: "AI Analysis",
      desc: "Our AI analyzes, profiles, and visualizes your data instantly."
    },
    {
      icon: <Layers className="w-8 h-8 text-blue-400" />,
      title: "Explore & Clean",
      desc: "Visualize relationships, lineage, and get cleaning suggestions."
    },
    {
      icon: <Zap className="w-8 h-8 text-yellow-400" />,
      title: "Automate & Integrate",
      desc: "Enable integrations, automate workflows, and export results."
    }
  ];

  const expandedFeatures = [
    {
      icon: <Sparkles className="w-7 h-7 text-yellow-400" />,
      title: "AI Schema Intelligence",
      desc: "Smart detection, relationship inference, and context-aware suggestions."
    },
    {
      icon: <Layers className="w-7 h-7 text-blue-400" />,
      title: "Data Lineage & Impact",
      desc: "Interactive lineage explorer and impact analysis for every schema change."
    },
    {
      icon: <Code2 className="w-7 h-7 text-teal-400" />,
      title: "Auto-Documentation",
      desc: "AI-powered, business-aware docs with Markdown export."
    },
    {
      icon: <Shield className="w-7 h-7 text-blue-600" />,
      title: "Data Cleaning",
      desc: "AI-driven cleaning suggestions, preview, and one-click fixes."
    },
    {
      icon: <Zap className="w-7 h-7 text-yellow-400" />,
      title: "Integration Marketplace",
      desc: "Webhooks, Slack, BI tools, cloud storage, and custom API connectors."
    },
    {
      icon: <Users className="w-7 h-7 text-blue-500" />,
      title: "Admin Dashboard & Security",
      desc: "Role-based access, audit logs, and enterprise-grade controls."
    }
  ];

  const logos = [
    "https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a6/Logo_NIKE.svg",
    "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg",
    "https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg"
  ];

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white overflow-hidden">
      {/* Removed animated/rotating background blobs for clean layout */}
      {/* Navigation */}
      <motion.nav 
        className="relative z-50 p-6"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <motion.div 
            className="flex items-center space-x-2"
            whileHover={{ scale: 1.05 }}
          >
            <div className="w-8 h-8 bg-gradient-to-r from-slate-500 to-blue-500 rounded-lg flex items-center justify-center">
              <Database className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">SchemaSage</span>
          </motion.div>
          <div className="hidden md:flex items-center space-x-8">
            <Link href="#features" className="hover:text-blue-700 dark:hover:text-blue-300 transition-colors font-medium">Features</Link>
            <Link href="#pricing" className="hover:text-blue-700 dark:hover:text-blue-300 transition-colors font-medium">Pricing</Link>
            <Link href="#docs" className="hover:text-blue-700 dark:hover:text-blue-300 transition-colors font-medium">Docs</Link>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link href="/auth/login">
                <Button className="bg-gradient-to-r from-slate-600 to-blue-600 hover:from-slate-700 hover:to-blue-700 text-white border-0 font-semibold shadow-md">
                  Get Started
                </Button>
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link href="/dashboard">
                <Button variant="outline" className="border-blue-400 text-blue-700 dark:text-blue-300 hover:bg-blue-500 hover:text-white font-semibold">
                  Dashboard (Dev)
                </Button>
              </Link>
            </motion.div>
            <ModeToggle />
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="relative z-10 pt-20 pb-32 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.div
            className="text-center max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: isVisible ? 1 : 0, y: isVisible ? 0 : 20 }}
            transition={{ duration: 0.8 }}
          >
            <motion.div
              className="inline-flex items-center gap-2 bg-blue-50 dark:bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 mb-8 border border-blue-200 dark:border-white/20"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              <Sparkles className="w-4 h-4 text-yellow-400" />
              <span className="text-sm font-medium text-blue-700 dark:text-white">AI-Powered Schema Generation</span>
              <span className="bg-gradient-to-r from-blue-400 to-teal-400 text-xs px-2 py-1 rounded-full text-white">NEW</span>
            </motion.div>
            <motion.h1
              className="text-5xl md:text-7xl font-extrabold mb-8 bg-gradient-to-r from-blue-700 via-blue-500 to-teal-500 bg-clip-text text-transparent dark:from-white dark:via-blue-200 dark:to-teal-200 leading-tight"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.8 }}
            >
              Transform Data Into
              <br />
              <span className="bg-gradient-to-r from-blue-500 to-teal-400 bg-clip-text text-transparent dark:from-blue-400 dark:to-teal-400">
                Perfect Schemas
              </span>
            </motion.h1>
            <motion.p
              className="text-xl md:text-2xl text-slate-700 dark:text-gray-300 mb-12 leading-relaxed font-medium"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.8 }}
            >
              SchemaSage uses advanced AI to automatically detect, visualize, and generate 
              database schemas from your data. Save weeks of manual work with intelligent
              schema inference and beautiful code generation.
            </motion.p>
            <motion.div
              className="flex flex-col sm:flex-row gap-4 justify-center items-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.8 }}
            >
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Link href="/auth/login">
                  <Button size="lg" className="bg-gradient-to-r from-blue-700 to-teal-500 hover:from-blue-800 hover:to-teal-600 text-white border-0 px-8 py-4 text-lg font-bold shadow-lg">
                    Start Building Free
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </Link>
              </motion.div>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button size="lg" variant="outline" className="border-blue-300 text-blue-700 dark:text-white hover:bg-blue-50 dark:hover:bg-white/10 px-8 py-4 text-lg font-semibold">
                  <Play className="mr-2 w-5 h-5" />
                  Watch Demo
                </Button>
              </motion.div>
            </motion.div>
            <motion.div
              className="flex items-center justify-center gap-8 mt-16 text-sm text-slate-600 dark:text-gray-400"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.6 }}
            >
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500 dark:text-green-400" />
                <span>Free tier available</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500 dark:text-green-400" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500 dark:text-green-400" />
                <span>Enterprise ready</span>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative z-10 py-20 border-t border-slate-200 dark:border-white/10 bg-white dark:bg-transparent">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-8"
            variants={staggerContainer}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
          >
            {[
              { label: "Active Developers", value: "50K+", icon: Users },
              { label: "Schemas Generated", value: "2M+", icon: Database },
              { label: "Hours Saved", value: "100K+", icon: Clock },
              { label: "Enterprise Clients", value: "500+", icon: Award },
            ].map((stat) => (
              <motion.div
                key={stat.label}
                className="text-center"
                variants={fadeInUp}
                whileHover={{ scale: 1.05 }}
              >
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-100 to-blue-300 dark:from-slate-500/20 dark:to-blue-500/20 rounded-2xl flex items-center justify-center backdrop-blur-sm border border-blue-200 dark:border-white/10">
                  <stat.icon className="w-8 h-8 text-blue-500 dark:text-blue-300" />
                </div>
                <div className="text-4xl font-extrabold mb-2 text-blue-700 dark:bg-gradient-to-r dark:from-white dark:to-gray-300 dark:bg-clip-text dark:text-transparent">
                  {stat.value}
                </div>
                <div className="text-slate-700 dark:text-gray-400 font-medium">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Expanded Features Section */}
      <section id="features" className="py-20 bg-white dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">Why SchemaSage?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {expandedFeatures.map((f, i) => (
              <motion.div key={f.title} className="bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-800 dark:to-slate-900 rounded-xl p-8 shadow-lg flex flex-col items-center text-center hover:scale-105 transition-transform"
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 * i }}>
                <div className="mb-4">{f.icon}</div>
                <div className="font-bold text-lg mb-2">{f.title}</div>
                <div className="text-slate-600 dark:text-slate-300">{f.desc}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Screenshots/Demo Section */}
      <section className="py-20 bg-gradient-to-br from-blue-50 to-teal-50 dark:from-slate-800 dark:to-slate-900">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">See SchemaSage in Action</h2>
          <div className="flex flex-col md:flex-row items-center justify-center gap-8">
            <img src="/dashboard-screenshot.png" alt="Dashboard Screenshot" className="rounded-xl shadow-xl w-full md:w-1/2 border-4 border-blue-200 dark:border-slate-700" />
            <img src="/lineage-screenshot.png" alt="Lineage Explorer Screenshot" className="rounded-xl shadow-xl w-full md:w-1/2 border-4 border-blue-200 dark:border-slate-700" />
          </div>
          <div className="text-center mt-8">
            <Link href="/auth/login">
              <Button className="bg-gradient-to-r from-blue-600 to-teal-500 text-white px-8 py-3 text-lg font-semibold shadow-lg hover:scale-105 transition-transform">Try Live Demo</Button>
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-white dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {howItWorks.map((step, i) => (
              <motion.div key={step.title} className="flex flex-col items-center text-center p-6 rounded-xl bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-800 dark:to-slate-900 shadow-lg"
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 * i }}>
                <div className="mb-4">{step.icon}</div>
                <div className="font-bold text-lg mb-2">{step.title}</div>
                <div className="text-slate-600 dark:text-slate-300">{step.desc}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="relative z-10 py-32 bg-slate-100 dark:bg-slate-900/20 border-t border-slate-200 dark:border-white/10">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            className="text-center mb-20"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-extrabold mb-6 bg-gradient-to-r from-blue-700 via-blue-500 to-teal-500 bg-clip-text text-transparent dark:from-white dark:via-blue-200 dark:to-teal-200">
              &quot;Loved by Developers Worldwide&quot;
            </h2>
            <p className="text-xl text-slate-700 dark:text-gray-300 max-w-3xl mx-auto font-medium">
              Join thousands of developers who trust SchemaSage for their database needs.
            </p>
          </motion.div>
          <div className="relative max-w-4xl mx-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentTestimonial}
                className="text-center p-12 rounded-3xl bg-white dark:bg-white/5 shadow-lg dark:shadow-none border border-slate-200 dark:border-white/10"
                initial={{ opacity: 0, x: 100 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -100 }}
                transition={{ duration: 0.5 }}
              >
                <div className="flex justify-center mb-6">
                  {[...Array(testimonials[currentTestimonial].rating)].map((_, i) => (
                    <Star key={i} className="w-6 h-6 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <blockquote className="text-2xl md:text-3xl font-semibold text-slate-800 dark:text-gray-200 mb-8 leading-relaxed">
                  &quot;{testimonials[currentTestimonial].content}&quot;
                </blockquote>
                <div className="flex items-center justify-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-r from-blue-400 to-teal-400 flex items-center justify-center text-white font-bold text-lg">
                    {testimonials[currentTestimonial].avatar}
                  </div>
                  <div className="text-left">
                    <div className="font-semibold text-slate-900 dark:text-white text-lg">
                      {testimonials[currentTestimonial].name}
                    </div>
                    <div className="text-slate-600 dark:text-gray-400">
                      {testimonials[currentTestimonial].role}
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
            <div className="flex justify-center gap-2 mt-8">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  className={`w-3 h-3 rounded-full transition-colors ${index === currentTestimonial ? 'bg-blue-400' : 'bg-slate-300 dark:bg-white/20 hover:bg-blue-300 dark:hover:bg-white/40'}`}
                  onClick={() => setCurrentTestimonial(index)}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="relative z-10 py-32 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-white/10">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            className="text-center mb-20"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-extrabold mb-6 bg-gradient-to-r from-blue-700 via-blue-500 to-teal-500 bg-clip-text text-transparent dark:from-white dark:via-blue-200 dark:to-teal-200">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-slate-700 dark:text-gray-300 max-w-3xl mx-auto font-medium">
              Choose the perfect plan for your needs. Upgrade or downgrade at any time.
            </p>
          </motion.div>
          <motion.div
            className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto"
            variants={staggerContainer}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
          >
            <motion.div
              className="p-8 rounded-3xl bg-white dark:bg-white/5 shadow-lg dark:shadow-none border border-slate-200 dark:border-white/10 hover:border-blue-400 dark:hover:border-white/20 transition-all duration-300"
              variants={fadeInUp}
              whileHover={{ scale: 1.02 }}
            >
              <div className="text-center">
                <h3 className="text-2xl font-bold text-blue-700 dark:text-white mb-2">Starter</h3>
                <div className="text-4xl font-extrabold text-blue-700 dark:text-white mb-2">Free</div>
                <p className="text-slate-700 dark:text-gray-400 mb-8">Perfect for individuals and small projects</p>
                <ul className="space-y-4 mb-8 text-left">
                  {["3 projects","Basic schema detection","Standard templates","Community support"].map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-500 dark:text-green-400 flex-shrink-0" />
                      <span className="text-slate-700 dark:text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button className="w-full bg-gradient-to-r from-blue-700 to-teal-500 hover:from-blue-800 hover:to-teal-600 text-white font-bold">
                  Get Started Free
                </Button>
              </div>
            </motion.div>
            <motion.div
              className="p-8 rounded-3xl bg-gradient-to-br from-blue-100 to-teal-100 dark:from-blue-500/20 dark:to-teal-500/20 shadow-lg dark:shadow-none border-2 border-blue-500/50 relative overflow-hidden"
              variants={fadeInUp}
              whileHover={{ scale: 1.02 }}
            >
              <div className="absolute top-4 right-4 bg-gradient-to-r from-blue-500 to-teal-500 text-white text-xs px-3 py-1 rounded-full">
                Most Popular
              </div>
              <div className="text-center">
                <h3 className="text-2xl font-bold text-blue-700 dark:text-white mb-2">Pro</h3>
                <div className="text-4xl font-extrabold text-blue-700 dark:text-white mb-2">$29<span className="text-lg text-slate-600 dark:text-gray-400">/month</span></div>
                <p className="text-slate-700 dark:text-gray-400 mb-8">For professional developers and growing teams</p>
                <ul className="space-y-4 mb-8 text-left">
                  {["Unlimited projects","Advanced AI detection","Custom templates","Priority support","Team collaboration","Version control"].map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-500 dark:text-green-400 flex-shrink-0" />
                      <span className="text-slate-700 dark:text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button className="w-full bg-gradient-to-r from-blue-700 to-teal-500 hover:from-blue-800 hover:to-teal-600 text-white font-bold">
                  Start Pro Trial
                </Button>
              </div>
            </motion.div>
            <motion.div
              className="p-8 rounded-3xl bg-white dark:bg-white/5 shadow-lg dark:shadow-none border border-slate-200 dark:border-white/10 hover:border-blue-400 dark:hover:border-white/20 transition-all duration-300"
              variants={fadeInUp}
              whileHover={{ scale: 1.02 }}
            >
              <div className="text-center">
                <h3 className="text-2xl font-bold text-blue-700 dark:text-white mb-2">Enterprise</h3>
                <div className="text-4xl font-extrabold text-blue-700 dark:text-white mb-2">Custom</div>
                <p className="text-slate-700 dark:text-gray-400 mb-8">For large organizations with complex needs</p>
                <ul className="space-y-4 mb-8 text-left">
                  {["Everything in Pro","Custom deployment","24/7 dedicated support","SLA guarantees","Custom integrations","Training & onboarding"].map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-500 dark:text-green-400 flex-shrink-0" />
                      <span className="text-slate-700 dark:text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button className="w-full bg-gradient-to-r from-blue-700 to-teal-500 hover:from-blue-800 hover:to-teal-600 text-white font-bold">
                  Contact Sales
                </Button>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative z-10 py-32 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-white/10">
        <div className="max-w-4xl mx-auto text-center px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-6xl font-extrabold mb-8 bg-gradient-to-r from-blue-700 via-blue-500 to-teal-500 bg-clip-text text-transparent dark:from-white dark:via-blue-200 dark:to-teal-200">
              Ready to Transform Your Workflow?
            </h2>
            <p className="text-xl md:text-2xl text-slate-700 dark:text-gray-300 mb-12 leading-relaxed font-medium">
              Join thousands of developers who are building better databases with SchemaSage.
            </p>
            <motion.div
              className="flex flex-col sm:flex-row gap-4 justify-center"
              whileInView={{ opacity: 1, y: 0 }}
              initial={{ opacity: 0, y: 20 }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Link href="/auth/login">
                  <Button size="lg" className="bg-gradient-to-r from-blue-700 to-teal-500 hover:from-blue-800 hover:to-teal-600 text-white border-0 px-8 py-4 text-lg font-bold shadow-lg">
                    Start Building Today
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </Link>
              </motion.div>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button size="lg" variant="outline" className="border-blue-300 text-blue-700 dark:text-white hover:bg-blue-50 dark:hover:bg-white/10 px-8 py-4 text-lg font-semibold">
                  <Github className="mr-2 w-5 h-5" />
                  View on GitHub
                </Button>
              </motion.div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Database className="w-6 h-6 text-blue-400" />
            <span className="font-bold text-lg">SchemaSage</span>
          </div>
          <div className="flex gap-6 text-slate-400 text-sm">
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <a href="mailto:support@schemasage.com">Contact</a>
          </div>
          <div className="flex gap-4">
            <a href="https://github.com/your-org/schemasage" target="_blank" rel="noopener noreferrer"><Github className="w-5 h-5 hover:text-blue-400" /></a>
            <a href="https://twitter.com/schemasage" target="_blank" rel="noopener noreferrer"><Twitter className="w-5 h-5 hover:text-blue-400" /></a>
          </div>
          <div className="text-xs text-slate-500 mt-4 md:mt-0">© {new Date().getFullYear()} SchemaSage. All rights reserved.</div>
        </div>
      </footer>
    </div>
  );
}