"use client";

import { Button } from "@/components/ui/button";
import { Database, Shield, Code2, Users, ArrowRight, Play, CheckCircle, Github, Layers, Zap, Globe, Brain } from "lucide-react";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { useTheme } from "next-themes";
import { motion, useScroll, useTransform, useSpring } from "framer-motion";

const testimonials = [
	{
		name: "Sarah Chen",
		role: "Lead Developer at TechCorp",
		content: "SchemaSage saved us weeks of work. The AI-powered schema detection is incredibly accurate.",
		color: "bg-gradient-to-br from-blue-500 to-teal-400"
	},
	{
		name: "Marcus Johnson",
		role: "Data Architect at DataFlow",
		content: "The code generation feature is a game-changer. Perfect TypeScript interfaces every time.",
		color: "bg-gradient-to-br from-teal-500 to-blue-400"
	},
	{
		name: "Emily Rodriguez",
		role: "Full Stack Engineer",
		content: "Finally, a tool that understands complex data relationships. The ER diagrams are beautiful!",
		color: "bg-gradient-to-br from-yellow-500 to-pink-400"
	},
];

const integrations = [
	{ name: "Postgres", logo: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg" },
	{ name: "MySQL", logo: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mysql/mysql-original.svg" },
	{ name: "MongoDB", logo: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mongodb/mongodb-original.svg" },
	{ name: "Slack", logo: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/slack/slack-original.svg" },
	{ name: "GitHub", logo: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" },
	{ name: "Notion", logo: "https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png" }
];

const faqs = [
	{ q: "Is my data secure?", a: "Yes. All processing is local or encrypted, and we never store your data." },
	{ q: "Can I export code?", a: "Yes. You can export TypeScript, Python, SQL, and Markdown docs instantly." },
	{ q: "Is there a free tier?", a: "Absolutely! Start building for free, no credit card required." },
	{ q: "What databases do you support?", a: "Postgres, MySQL, MongoDB, and more coming soon." },
];

export default function LandingPage() {
	const { setTheme } = useTheme();
	useEffect(() => {
		setTheme("dark");
	}, [setTheme]);
	const [playgroundCode, setPlaygroundCode] = useState("// Paste your data or schema here...\n{");
	const [playgroundResult, setPlaygroundResult] = useState("// AI-generated schema will appear here");
	const heroRef = useRef(null);
	const featuresRef = useRef(null);
	const testimonialsRef = useRef(null);
	const { scrollY } = useScroll();

	// Even gentler parallax for hero image
	const rawHeroY = useTransform(scrollY, [0, 300], [0, -12], { clamp: true });
	const heroY = useSpring(rawHeroY, { stiffness: 70, damping: 28 });
	// Gentle fade/scale for features
	const rawFeaturesOpacity = useTransform(scrollY, [120, 400], [1, 0.88], { clamp: true });
	const featuresOpacity = useSpring(rawFeaturesOpacity, { stiffness: 60, damping: 18 });
	const rawFeaturesScale = useTransform(scrollY, [120, 400], [1, 0.985], { clamp: true });
	const featuresScale = useSpring(rawFeaturesScale, { stiffness: 60, damping: 18 });
	// Gentle fade for testimonials
	const rawTestimonialsOpacity = useTransform(scrollY, [400, 700], [1, 0.88], { clamp: true });
	const testimonialsOpacity = useSpring(rawTestimonialsOpacity, { stiffness: 60, damping: 18 });

	function handlePlaygroundRun() {
		setPlaygroundResult("{\n  id: 'string',\n  name: 'string',\n  createdAt: 'Date',\n  ...\n}");
	}

	return (
		<div className="relative min-h-screen flex flex-col items-center justify-between px-4 py-0" style={{ fontFamily: 'Inter, sans-serif' }}>
			{/* Animated SVG background */}
			<svg className="absolute inset-0 w-full h-full -z-10" style={{ pointerEvents: 'none' }} aria-hidden fill="none">
				<defs>
					<radialGradient id="bg1" cx="50%" cy="0%" r="100%" gradientTransform="rotate(45)"><stop stopColor="#3A86FF" stopOpacity="0.10" /><stop offset="1" stopColor="#0a0a0a" stopOpacity="0" /></radialGradient>
				</defs>
				<rect width="100%" height="100%" fill="#0a0a0a" />
				<circle cx="80%" cy="10%" r="300" fill="url(#bg1)" />
				<circle cx="20%" cy="90%" r="200" fill="#06D6A018" />
			</svg>

			{/* NAVIGATION */}
			<nav className="w-full max-w-7xl mx-auto flex items-center justify-between py-8">
				<div className="flex items-center gap-3">
					<span className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-white/10 border border-white/10">
						<Database className="w-6 h-6 text-white" />
					</span>
					<span className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">SchemaSage</span>
				</div>
				<div className="hidden md:flex gap-8 text-white/80 text-base font-medium">
					<Link href="#features" className="hover:text-white transition">Features</Link>
					<Link href="#testimonials" className="hover:text-white transition">Testimonials</Link>
					<Link href="#faq" className="hover:text-white transition">FAQ</Link>
				</div>
				<Link href="/auth/login">
					<Button className="px-6 py-2 font-semibold text-base bg-white/10 border border-white/20 backdrop-blur-md hover:bg-white/20 transition rounded-xl shadow-lg">Get Started</Button>
				</Link>
			</nav>

			{/* HERO with demo poster and very gentle parallax */}
			<motion.section ref={heroRef} style={{ y: heroY }} className="w-full flex flex-col items-center justify-center text-center py-20">
				<motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="text-5xl md:text-7xl font-extrabold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent drop-shadow-lg">
					AI-Powered Database Design
				</motion.h1>
				<motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.8 }} className="max-w-2xl mx-auto text-lg md:text-2xl text-white/80 mb-10 font-medium">
					Instantly generate, visualize, and manage world-class database schemas with the power of AI. Save weeks of work, avoid costly mistakes, and impress your team and investors.
				</motion.p>
				<motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4, duration: 0.8 }} className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
					<Link href="/auth/login">
						<Button size="lg" className="px-8 py-4 text-lg font-bold bg-gradient-to-r from-blue-600 to-teal-500 text-white border-0 shadow-xl rounded-2xl">Start Free <ArrowRight className="ml-2 w-5 h-5" /></Button>
					</Link>
					<a href="#features">
						<Button size="lg" variant="outline" className="px-8 py-4 text-lg font-semibold border-white/30 text-white/80 bg-white/5 hover:bg-white/10 rounded-2xl">Learn More</Button>
					</a>
				</motion.div>
				{/* Static demo image with reduced parallax */}
				<motion.div style={{ y: heroY, willChange: 'transform' }} className="w-full flex justify-center">
					<img src="/demo-poster.png" alt="SchemaSage Dashboard Demo" className="rounded-2xl shadow-2xl border border-white/10 w-full max-w-3xl object-cover" />
				</motion.div>
			</motion.section>

			{/* INTERACTIVE PLAYGROUND */}
			<motion.section initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8 }} className="w-full max-w-3xl mx-auto py-16">
				<h2 className="text-2xl md:text-3xl font-bold text-center mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">Try SchemaSage Instantly</h2>
				<div className="rounded-2xl bg-white/5 border border-white/10 shadow-xl backdrop-blur-md p-8 flex flex-col md:flex-row gap-6" style={{ backdropFilter: 'blur(18px) saturate(1.2)' }}>
					<textarea value={playgroundCode} onChange={e => setPlaygroundCode(e.target.value)} rows={7} className="flex-1 bg-black/40 text-white p-4 rounded-lg font-mono resize-none border border-white/10" />
					<div className="flex flex-col gap-2 flex-1">
						<Button onClick={handlePlaygroundRun} className="mb-2 bg-gradient-to-r from-blue-600 to-teal-500 text-white font-bold">Generate Schema</Button>
						<pre className="flex-1 bg-black/60 text-green-200 p-4 rounded-lg font-mono overflow-x-auto border border-white/10">{playgroundResult}</pre>
					</div>
				</div>
			</motion.section>

			{/* FEATURES with gentle fade/scale on scroll */}
			<motion.section ref={featuresRef} style={{ opacity: featuresOpacity, scale: featuresScale }} id="features" initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8 }} className="w-full max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 py-20">
				<div className="rounded-2xl p-8 flex flex-col items-center text-center shadow-xl border border-white/10 bg-white/5 backdrop-blur-md" style={{ backdropFilter: 'blur(18px) saturate(1.2)' }}>
					<Brain className="w-8 h-8 mb-3 text-blue-300" />
					<h3 className="text-xl font-bold mb-2 text-white">AI Schema Generation</h3>
					<p className="text-white/80">Upload your data or connect a database, and get a perfect schema in seconds—no manual modeling required.</p>
				</div>
				<div className="rounded-2xl p-8 flex flex-col items-center text-center shadow-xl border border-white/10 bg-white/5 backdrop-blur-md" style={{ backdropFilter: 'blur(18px) saturate(1.2)' }}>
					<Code2 className="w-8 h-8 mb-3 text-teal-300" />
					<h3 className="text-xl font-bold mb-2 text-white">Instant Code & Docs</h3>
					<p className="text-white/80">Generate TypeScript, Python, SQL, and Markdown docs—ready to use, always up to date, and beautifully formatted.</p>
				</div>
				<div className="rounded-2xl p-8 flex flex-col items-center text-center shadow-xl border border-white/10 bg-white/5 backdrop-blur-md" style={{ backdropFilter: 'blur(18px) saturate(1.2)' }}>
					<Shield className="w-8 h-8 mb-3 text-blue-300" />
					<h3 className="text-xl font-bold mb-2 text-white">Enterprise-Grade Security</h3>
					<p className="text-white/80">Your data is encrypted, never leaves your control, and is protected by best-in-class security practices.</p>
				</div>
			</motion.section>

			{/* HOW IT WORKS */}
			<motion.section initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8 }} className="w-full max-w-4xl mx-auto py-20">
				<h2 className="text-3xl md:text-4xl font-bold text-center mb-12 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">How It Works</h2>
				<div className="grid grid-cols-1 md:grid-cols-3 gap-8">
					<div className="rounded-2xl p-8 flex flex-col items-center text-center border border-white/10 bg-white/5 backdrop-blur-md" style={{ backdropFilter: 'blur(14px) saturate(1.1)' }}>
						<Database className="w-8 h-8 mb-3 text-blue-200" />
						<h3 className="text-lg font-bold mb-2 text-white">Connect</h3>
						<p className="text-white/80">Connect your database or upload your data file securely.</p>
					</div>
					<div className="rounded-2xl p-8 flex flex-col items-center text-center border border-white/10 bg-white/5 backdrop-blur-md" style={{ backdropFilter: 'blur(14px) saturate(1.1)' }}>
						<Brain className="w-8 h-8 mb-3 text-blue-200" />
						<h3 className="text-lg font-bold mb-2 text-white">Generate</h3>
						<p className="text-white/80">AI instantly analyzes and generates your schema and docs.</p>
					</div>
					<div className="rounded-2xl p-8 flex flex-col items-center text-center border border-white/10 bg-white/5 backdrop-blur-md" style={{ backdropFilter: 'blur(14px) saturate(1.1)' }}>
						<Code2 className="w-8 h-8 mb-3 text-teal-200" />
						<h3 className="text-lg font-bold mb-2 text-white">Export & Use</h3>
						<p className="text-white/80">Export code, docs, and diagrams. Integrate with your stack.</p>
					</div>
				</div>
			</motion.section>

			{/* TESTIMONIALS with gentle fade on scroll */}
			<motion.section ref={testimonialsRef} style={{ opacity: testimonialsOpacity }} id="testimonials" initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8 }} className="w-full max-w-5xl mx-auto py-20">
				<h2 className="text-3xl md:text-4xl font-bold text-center mb-12 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">What People Are Saying</h2>
				<div className="grid grid-cols-1 md:grid-cols-3 gap-8">
					{testimonials.map((t, i) => (
						<div key={i} className="rounded-2xl p-8 bg-white/5 border border-white/10 shadow-xl backdrop-blur-md flex flex-col items-center text-center" style={{ backdropFilter: 'blur(18px) saturate(1.2)' }}>
							<div className={`w-16 h-16 rounded-full mb-4 flex items-center justify-center text-xl font-bold text-white border-2 border-white/20 ${t.color}`}> 
								{t.name.split(" ").map(n => n[0]).join("")}
							</div>
							<p className="text-lg text-white mb-4">“{t.content}”</p>
							<div className="text-white/80 font-semibold mb-1">{t.name}</div>
							<div className="text-white/60 text-sm">{t.role}</div>
						</div>
					))}
				</div>
			</motion.section>

			{/* INTEGRATIONS */}
			<motion.section initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8 }} className="w-full max-w-4xl mx-auto py-12">
				<h2 className="text-2xl md:text-3xl font-bold text-center mb-8 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">Integrates With</h2>
				<div className="flex flex-wrap items-center justify-center gap-8">
					{integrations.map((i) => (
						<div key={i.name} className="flex flex-col items-center">
							<img src={i.logo} alt={i.name} className="h-10 mb-2 opacity-90 bg-white rounded-lg p-1" style={{objectFit:'contain', background:'#fff'}} />
							<span className="text-white/70 text-xs">{i.name}</span>
						</div>
					))}
				</div>
			</motion.section>

			{/* FINAL CTA BANNER */}
			<motion.section initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8 }} className="w-full max-w-3xl mx-auto py-16 text-center">
				<h2 className="text-4xl md:text-5xl font-extrabold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">Ready to build the future of data?</h2>
				<p className="text-xl text-white/80 mb-8">Join the next generation of teams using AI to design, document, and ship better databases.</p>
				<Link href="/auth/login">
					<Button size="lg" className="px-10 py-4 text-lg font-bold bg-gradient-to-r from-blue-600 to-teal-500 text-white border-0 shadow-xl rounded-2xl">Get Started Free</Button>
				</Link>
			</motion.section>

			{/* FAQ */}
			<motion.section id="faq" initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.8 }} className="w-full max-w-3xl mx-auto py-16">
				<h2 className="text-2xl md:text-3xl font-bold text-center mb-8 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">Frequently Asked Questions</h2>
				<div className="space-y-6">
					{faqs.map((f, i) => (
						<div key={i} className="rounded-xl bg-white/5 border border-white/10 p-6 backdrop-blur-md" style={{ backdropFilter: 'blur(10px) saturate(1.1)' }}>
							<div className="flex items-center gap-2 mb-2">
								<CheckCircle className="w-5 h-5 text-green-300" />
								<span className="font-semibold text-white">{f.q}</span>
							</div>
							<div className="text-white/80 ml-7">{f.a}</div>
						</div>
					))}
				</div>
			</motion.section>

			{/* FOOTER */}
			<footer className="w-full max-w-7xl mx-auto py-10 flex flex-col md:flex-row items-center justify-between text-white/60 text-sm border-t border-white/10">
				<div className="flex items-center gap-2 mb-4 md:mb-0">
					<Database className="w-5 h-5 text-white/80" />
					<span className="font-bold text-white">SchemaSage</span>
				</div>
				<div>
					&copy; {new Date().getFullYear()} SchemaSage. All rights reserved.
				</div>
			</footer>
		</div>
	);
}