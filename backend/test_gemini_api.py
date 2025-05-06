import asyncio
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Get Gemini API key from environment
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

async def test_gemini_api():
    """Test the Gemini API connection and model information"""
    print("\n=== GEMINI API TEST ===\n")
    
    # Check if API key is set
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        print("❌ ERROR: Gemini API key is not set in .env file")
        print("Please add your Gemini API key to the .env file as GEMINI_API_KEY")
        return
    
    try:
        # Configure the Gemini API
        print(f"📝 Configuring Gemini API with key: {api_key[:4]}...{api_key[-4:]}")
        genai.configure(api_key=api_key)
        
        # Get available models
        print("🔍 Fetching available models...")
        models = genai.list_models()
        gemini_models = [m for m in models if "gemini" in m.name]
        
        print(f"\n✅ Successfully connected to Gemini API!")
        print(f"📋 Available Gemini models: {len(gemini_models)}")
        
        for i, model in enumerate(gemini_models):
            print(f"  {i+1}. {model.name}")
            
        # Check if configured model is available
        available_model_names = [m.name for m in gemini_models]
        if model_name in available_model_names:
            print(f"\n✅ Configured model '{model_name}' is available")
        else:
            print(f"\n⚠️ WARNING: Configured model '{model_name}' not found in available models")
            print(f"   Available models: {', '.join(available_model_names)}")
        
        # Test a simple generation with the configured model
        print(f"\n🧪 Testing generation with model '{model_name}'...")
        
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("What is a database schema?")
            
            print("\n✅ Generation successful!")
            print("\nSample response:")
            print("-" * 60)
            print(response.text[:500] + ("..." if len(response.text) > 500 else ""))
            print("-" * 60)
            
            # Get and display model information
            print("\n📊 Model Information:")
            print(f"  Model: {model_name}")
            print(f"  Response tokens: ~{len(response.text.split())}")
            
            if hasattr(response, "candidates") and getattr(response, "candidates"):
                candidate = response.candidates[0]
                if hasattr(candidate, "safety_ratings") and candidate.safety_ratings:
                    print("  Safety ratings:", json.dumps([{r.category: r.probability} for r in candidate.safety_ratings], indent=2))
            
        except Exception as e:
            print(f"\n❌ Error generating content: {str(e)}")
            
    except Exception as e:
        print(f"\n❌ Error connecting to Gemini API: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_gemini_api())
    print("\n=== TEST COMPLETE ===\n")