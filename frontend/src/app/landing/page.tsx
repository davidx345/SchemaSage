"use client";

import { Button } from "@/components/ui/button";
import { PricingCard } from "@/components/pricing-card";
import { Testimonial } from "@/components/testimonial";
import { FeatureCard } from "@/components/feature-card";
import { FAQ } from "@/components/faq";
import {
  Database,
  Code2,
  Wand2,
  Zap,
  Shield,
  LineChart,
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
  TrendingUp,
  Globe,
  Layers,
} from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

// Animation variants
const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6 }
};

const fadeInLeft = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  transition: { duration: 0.6 }
};

const fadeInRight = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
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
  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    
    // Testimonial rotation
    const testimonialInterval = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);

    // Mouse position tracking for parallax effect
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 2 - 1,
        y: (e.clientY / window.innerHeight) * 2 - 1,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      clearInterval(testimonialInterval);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

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

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Detection",
      description: "Advanced machine learning algorithms analyze your data patterns and automatically infer optimal database schemas.",
      gradient: "from-purple-500 to-pink-500"
    },
    {
      icon: Code2,
      title: "Multi-Language Code Gen",
      description: "Generate TypeScript, Python, SQL, Go, and more with perfect type safety and industry best practices.",
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      icon: Zap,
      title: "Lightning Fast",
      description: "Process thousands of records in seconds. Our optimized engine handles large datasets effortlessly.",
      gradient: "from-yellow-500 to-orange-500"
    },
    {
      icon: Layers,
      title: "Visual Schema Builder",
      description: "Interactive drag-and-drop interface with real-time preview and relationship mapping.",
      gradient: "from-green-500 to-teal-500"
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "Bank-grade encryption, SOC 2 compliant, with role-based access control and audit logging.",
      gradient: "from-red-500 to-pink-500"
    },
    {
      icon: Globe,
      title: "Team Collaboration",
      description: "Real-time collaboration with version control, comments, and approval workflows.",
      gradient: "from-indigo-500 to-purple-500"
    }
  ];

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20"
          animate={{
            x: mousePosition.x * 20,
            y: mousePosition.y * 20,
          }}
          transition={{ type: "spring", damping: 50, stiffness: 100 }}
        />
        <motion.div
          className="absolute top-3/4 right-1/4 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-20"
          animate={{
            x: mousePosition.x * -15,
            y: mousePosition.y * -15,
          }}
          transition={{ type: "spring", damping: 50, stiffness: 100 }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20"
          animate={{
            x: mousePosition.x * 10,
            y: mousePosition.y * 10,
          }}
          transition={{ type: "spring", damping: 50, stiffness: 100 }}
        />
      </div>

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
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <Database className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">SchemaSage</span>
          </motion.div>
            <div className="hidden md:flex items-center space-x-8">
            <Link href="#features" className="hover:text-purple-300 transition-colors">Features</Link>
            <Link href="#pricing" className="hover:text-purple-300 transition-colors">Pricing</Link>
            <Link href="#docs" className="hover:text-purple-300 transition-colors">Docs</Link>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link href="/auth/login">
                <Button className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0">
                  Get Started
                </Button>
              </Link>
            </motion.div>
            {/* TEMPORARY DEVELOPMENT BUTTON - REMOVE IN PRODUCTION */}
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link href="/dashboard">
                <Button variant="outline" className="border-purple-400 text-purple-300 hover:bg-purple-500 hover:text-white">
                  Dashboard (Dev)
                </Button>
              </Link>
            </motion.div>
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
              className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 mb-8 border border-white/20"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              <Sparkles className="w-4 h-4 text-yellow-400" />
              <span className="text-sm font-medium">AI-Powered Schema Generation</span>
              <span className="bg-gradient-to-r from-purple-400 to-pink-400 text-xs px-2 py-1 rounded-full">NEW</span>
            </motion.div>

            <motion.h1
              className="text-5xl md:text-7xl font-bold mb-8 bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent leading-tight"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.8 }}
            >
              Transform Data Into
              <br />
              <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Perfect Schemas
              </span>
            </motion.h1>

            <motion.p
              className="text-xl md:text-2xl text-gray-300 mb-12 leading-relaxed"
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
                  <Button size="lg" className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0 px-8 py-4 text-lg font-semibold">
                    Start Building Free
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </Link>
              </motion.div>
              
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button size="lg" variant="outline" className="border-white/30 text-white hover:bg-white/10 px-8 py-4 text-lg">
                  <Play className="mr-2 w-5 h-5" />
                  Watch Demo
                </Button>
              </motion.div>
            </motion.div>

            <motion.div
              className="flex items-center justify-center gap-8 mt-16 text-sm text-gray-400"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.6 }}
            >
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>Free tier available</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>Enterprise ready</span>
              </div>
            </motion.div>
          </motion.div>
        </div>      </section>

      {/* Stats Section */}
      <section className="relative z-10 py-20">
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
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                className="text-center"
                variants={fadeInUp}
                whileHover={{ scale: 1.05 }}
              >
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl flex items-center justify-center backdrop-blur-sm border border-white/10">
                  <stat.icon className="w-8 h-8 text-purple-300" />
                </div>
                <div className="text-4xl font-bold mb-2 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="text-gray-400">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative z-10 py-32">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            className="text-center mb-20"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent">
              Powerful Features for Modern Development
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Everything you need to build, optimize, and maintain database schemas with confidence.
            </p>
          </motion.div>

          <motion.div
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-8"
            variants={staggerContainer}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
          >
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                className="group p-8 rounded-3xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-white/20 transition-all duration-300"
                variants={fadeInUp}
                whileHover={{ 
                  scale: 1.02,
                  boxShadow: "0 20px 40px rgba(0,0,0,0.3)"
                }}
              >
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold mb-4 text-white group-hover:text-purple-300 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-300 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="relative z-10 py-32 bg-gradient-to-r from-purple-900/20 to-pink-900/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            className="text-center mb-20"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent">
              Loved by Developers Worldwide
            </h2>
            <p className="text-xl text-gray-300">
              Join thousands of developers who trust SchemaSage for their database needs.
            </p>
          </motion.div>

          <div className="relative max-w-4xl mx-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentTestimonial}
                className="text-center p-12 rounded-3xl bg-white/5 backdrop-blur-sm border border-white/10"
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
                <blockquote className="text-2xl md:text-3xl font-medium text-gray-200 mb-8 leading-relaxed">
                  "{testimonials[currentTestimonial].content}"
                </blockquote>
                <div className="flex items-center justify-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-lg">
                    {testimonials[currentTestimonial].avatar}
                  </div>
                  <div className="text-left">
                    <div className="font-semibold text-white text-lg">
                      {testimonials[currentTestimonial].name}
                    </div>
                    <div className="text-gray-400">
                      {testimonials[currentTestimonial].role}
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>

            {/* Testimonial indicators */}
            <div className="flex justify-center gap-2 mt-8">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  className={`w-3 h-3 rounded-full transition-colors ${
                    index === currentTestimonial 
                      ? 'bg-purple-400' 
                      : 'bg-white/20 hover:bg-white/40'
                  }`}
                  onClick={() => setCurrentTestimonial(index)}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="relative z-10 py-32">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            className="text-center mb-20"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-300">
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
              className="p-8 rounded-3xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-white/20 transition-all duration-300"
              variants={fadeInUp}
              whileHover={{ scale: 1.02 }}
            >
              <div className="text-center">
                <h3 className="text-2xl font-bold text-white mb-2">Starter</h3>
                <div className="text-4xl font-bold text-white mb-2">Free</div>
                <p className="text-gray-400 mb-8">Perfect for individuals and small projects</p>
                
                <ul className="space-y-4 mb-8 text-left">
                  {[
                    "3 projects",
                    "Basic schema detection",
                    "Standard templates",
                    "Community support"
                  ].map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <Button className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/20">
                  Get Started Free
                </Button>
              </div>
            </motion.div>

            <motion.div
              className="p-8 rounded-3xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-sm border-2 border-purple-500/50 relative overflow-hidden"
              variants={fadeInUp}
              whileHover={{ scale: 1.02 }}
            >
              <div className="absolute top-4 right-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-3 py-1 rounded-full">
                Most Popular
              </div>
              <div className="text-center">
                <h3 className="text-2xl font-bold text-white mb-2">Pro</h3>
                <div className="text-4xl font-bold text-white mb-2">$29<span className="text-lg text-gray-400">/month</span></div>
                <p className="text-gray-300 mb-8">For professional developers and growing teams</p>
                
                <ul className="space-y-4 mb-8 text-left">
                  {[
                    "Unlimited projects",
                    "Advanced AI detection",
                    "Custom templates",
                    "Priority support",
                    "Team collaboration",
                    "Version control"
                  ].map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <Button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white">
                  Start Pro Trial
                </Button>
              </div>
            </motion.div>

            <motion.div
              className="p-8 rounded-3xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-white/20 transition-all duration-300"
              variants={fadeInUp}
              whileHover={{ scale: 1.02 }}
            >
              <div className="text-center">
                <h3 className="text-2xl font-bold text-white mb-2">Enterprise</h3>
                <div className="text-4xl font-bold text-white mb-2">Custom</div>
                <p className="text-gray-400 mb-8">For large organizations with complex needs</p>
                
                <ul className="space-y-4 mb-8 text-left">
                  {[
                    "Everything in Pro",
                    "Custom deployment",
                    "24/7 dedicated support",
                    "SLA guarantees",
                    "Custom integrations",
                    "Training & onboarding"
                  ].map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <Button className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/20">
                  Contact Sales
                </Button>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative z-10 py-32">
        <div className="max-w-4xl mx-auto text-center px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-6xl font-bold mb-8 bg-gradient-to-r from-white via-purple-200 to-pink-200 bg-clip-text text-transparent">
              Ready to Transform Your Workflow?
            </h2>
            <p className="text-xl md:text-2xl text-gray-300 mb-12 leading-relaxed">
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
                  <Button size="lg" className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0 px-8 py-4 text-lg font-semibold">
                    Start Building Today
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </Link>
              </motion.div>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button size="lg" variant="outline" className="border-white/30 text-white hover:bg-white/10 px-8 py-4 text-lg">
                  <Github className="mr-2 w-5 h-5" />
                  View on GitHub
                </Button>
              </motion.div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            <div>
              <h3 className="font-semibold text-white mb-6">Product</h3>
              <ul className="space-y-3">
                <li><a href="#features" className="text-gray-400 hover:text-purple-300 transition-colors">Features</a></li>
                <li><a href="#pricing" className="text-gray-400 hover:text-purple-300 transition-colors">Pricing</a></li>
                <li><a href="#docs" className="text-gray-400 hover:text-purple-300 transition-colors">Documentation</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">API Reference</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-6">Company</h3>
              <ul className="space-y-3">
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">About</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Blog</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Careers</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Press</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-6">Resources</h3>
              <ul className="space-y-3">
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Community</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Help Center</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Partners</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Status</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-6">Legal</h3>
              <ul className="space-y-3">
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Terms of Service</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Security</a></li>
                <li><a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">Cookie Policy</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-white/10 pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                  <Database className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-white">SchemaSage</span>
              </div>
              
              <p className="text-sm text-gray-400">
                © 2025 SchemaSage. All rights reserved.
              </p>
              
              <div className="flex gap-6">
                <a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">
                  <Twitter className="w-5 h-5" />
                </a>
                <a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">
                  <Github className="w-5 h-5" />
                </a>
                <a href="#" className="text-gray-400 hover:text-purple-300 transition-colors">
                  <Users className="w-5 h-5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}