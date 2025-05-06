import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Quote } from "lucide-react";

interface TestimonialProps {
  quote: string;
  author: string;
  role: string;
  company: string;
  avatarUrl?: string;
}

export function Testimonial({
  quote,
  author,
  role,
  company,
  avatarUrl,
}: TestimonialProps) {
  return (
    <Card className="p-6 flex flex-col">
      <Quote className="h-8 w-8 text-primary mb-4" />
      
      <blockquote className="text-lg mb-6">
        "{quote}"
      </blockquote>

      <div className="flex items-center gap-3 mt-auto">
        <Avatar>
          <AvatarImage src={avatarUrl} />
          <AvatarFallback>
            {author.split(" ").map(n => n[0]).join("")}
          </AvatarFallback>
        </Avatar>
        
        <div>
          <div className="font-semibold">{author}</div>
          <div className="text-sm text-muted-foreground">
            {role} at {company}
          </div>
        </div>
      </div>
    </Card>
  );
}