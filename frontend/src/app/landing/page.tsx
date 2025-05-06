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
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="py-20 px-4 text-center">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            Transform Your Data Into Clear Database Schemas
          </h1>
          <p className="text-xl text-muted-foreground mb-8">
            SchemaSage uses AI to automatically detect and generate database schemas from your existing data, saving you hours of manual work.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg">Get Started Free</Button>
            <Button size="lg" variant="outline">View Demo</Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-muted/50 py-16">
        <div className="container grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { label: "Active Users", value: "10K+" },
            { label: "Schemas Generated", value: "100K+" },
            { label: "Time Saved", value: "50K+ hrs" },
            { label: "Satisfaction Rate", value: "99%" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl font-bold mb-2">{stat.value}</div>
              <div className="text-muted-foreground">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="container">
          <h2 className="text-3xl font-bold text-center mb-12">
            Powerful Features for Database Design
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              icon={Database}
              title="Smart Schema Detection"
              description="Automatically detect database schemas from JSON, CSV, or existing databases with AI-powered analysis."
            />
            <FeatureCard
              icon={Code2}
              title="Code Generation"
              description="Generate TypeScript, Python, SQL, and more from your detected schemas with perfect type safety."
            />
            <FeatureCard
              icon={Wand2}
              title="AI Assistance"
              description="Get smart suggestions for optimizing your schema design and maintaining best practices."
            />
            <FeatureCard
              icon={Zap}
              title="Instant Preview"
              description="See your schema changes in real-time with our interactive visualization tools."
            />
            <FeatureCard
              icon={Shield}
              title="Data Validation"
              description="Ensure your schema matches your data with built-in validation and error checking."
            />
            <FeatureCard
              icon={LineChart}
              title="Performance Analytics"
              description="Analyze and optimize your schema for better database performance."
            />
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="bg-muted/50 py-20">
        <div className="container">
          <h2 className="text-3xl font-bold text-center mb-12">
            Trusted by Developers
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Testimonial
              quote="SchemaSage has completely transformed how we handle database migrations. It's saved us countless hours of manual schema work."
              author="Sarah Chen"
              role="Lead Developer"
              company="TechCorp"
            />
            <Testimonial
              quote="The AI-powered schema detection is incredibly accurate. It's like having a database expert on the team."
              author="Michael Rodriguez"
              role="Senior Engineer"
              company="DataFlow"
            />
            <Testimonial
              quote="We've cut our database design time in half. The code generation features are absolutely fantastic."
              author="Emma Thompson"
              role="CTO"
              company="StartupX"
            />
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20">
        <div className="container">
          <h2 className="text-3xl font-bold text-center mb-12">
            Simple, Transparent Pricing
          </h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <PricingCard
              title="Hobby"
              price="Free"
              description="Perfect for side projects and learning"
              features={[
                "Up to 3 projects",
                "Basic schema detection",
                "Community support",
                "Standard code generation"
              ]}
            />
            <PricingCard
              title="Pro"
              price="$29"
              description="For professional developers"
              features={[
                "Unlimited projects",
                "Advanced AI features",
                "Priority support",
                "Custom code generation",
                "Team collaboration"
              ]}
              highlighted
            />
            <PricingCard
              title="Enterprise"
              price="Custom"
              description="For large teams and organizations"
              features={[
                "Everything in Pro",
                "Custom deployment",
                "24/7 support",
                "SLA guarantees",
                "Training & onboarding"
              ]}
              ctaText="Contact Sales"
            />
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-muted/50 py-20">
        <div className="container max-w-3xl">
          <h2 className="text-3xl font-bold text-center mb-12">
            Frequently Asked Questions
          </h2>
          <FAQ
            items={[
              {
                question: "How accurate is the schema detection?",
                answer: "Our AI-powered schema detection is highly accurate, typically achieving over 95% accuracy for standard data structures. For complex cases, you can always fine-tune the results."
              },
              {
                question: "What programming languages are supported?",
                answer: "We currently support TypeScript, Python, Java, C#, and SQL. We're constantly adding support for more languages based on user feedback."
              },
              {
                question: "Can I import existing database schemas?",
                answer: "Yes! You can import schemas from existing databases, JSON files, CSV files, and more. We support all major database systems."
              },
              {
                question: "Is my data secure?",
                answer: "Absolutely. We never store your actual data - we only analyze the structure to generate schemas. All processing is done locally in your browser or through secure API calls."
              },
              {
                question: "Do you offer refunds?",
                answer: "Yes, we offer a 30-day money-back guarantee for all paid plans. No questions asked."
              },
              {
                question: "Can I use it for commercial projects?",
                answer: "Yes, all our plans support commercial use. The Enterprise plan includes additional features for large-scale commercial deployments."
              }
            ]}
          />
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container max-w-3xl text-center">
          <h2 className="text-3xl font-bold mb-6">
            Ready to Transform Your Database Design?
          </h2>
          <p className="text-xl text-muted-foreground mb-8">
            Join thousands of developers who are already saving time with SchemaSage.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg">Get Started Free</Button>
            <Button size="lg" variant="outline">Schedule Demo</Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-semibold mb-4">Product</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-muted-foreground hover:text-primary">Features</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Pricing</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Documentation</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Updates</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4">Company</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-muted-foreground hover:text-primary">About</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Blog</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Careers</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Contact</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4">Resources</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-muted-foreground hover:text-primary">Community</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Help Center</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Partners</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Status</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4">Legal</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-muted-foreground hover:text-primary">Privacy</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Terms</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Security</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-primary">Cookies</a></li>
            </ul>
          </div>
        </div>
        <div className="container mt-8 pt-8 border-t">
          <div className="flex justify-between items-center">
            <p className="text-sm text-muted-foreground">
              © 2025 SchemaSage. All rights reserved.
            </p>
            <div className="flex gap-4">
              <a href="#" className="text-muted-foreground hover:text-primary">
                Twitter
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary">
                GitHub
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary">
                Discord
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}