import os
import sys
import warnings

# Disable telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
warnings.filterwarnings("ignore", message=".*telemetry.*")

# Add current directory to path
sys.path.append(os.getcwd())

# Try to load .env file if dotenv is available, otherwise skip
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed. Set GROQ_API_KEY as environment variable.")

def main():
    """Simple QA demo with file processing"""
    
    # Check for file argument
    if len(sys.argv) < 2:
        print("Usage: python example.py <file_path>")
        print("Example: python example.py documents/my_file.pdf")
        return
    
    file_path = sys.argv[1]
    
    # Validate file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    # Check API key (try different variable names)
    groq_key = os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key")
    if not groq_key:
        print("Please set GROQ_API_KEY environment variable")
        print("Windows: set GROQ_API_KEY=your-key-here")
        print("Linux/Mac: export GROQ_API_KEY=your-key-here")
        print("Or create a .env file with: GROQ_API_KEY=your-key-here")
        return
    
    # Set the environment variable for consistency
    os.environ["GROQ_API_KEY"] = groq_key
    
    print(f"Processing file: {file_path}")
    
    try:
        # Import QA service
        from services.qa_service import QAService
        
        # Initialize QA system
        qa_service = QAService()
        
        # Process file directly (no file reading needed)
        print("Processing document...")
        result = qa_service.process_file(file_path, user_id=1)
        
        if not result['success']:
            print(f"❌ Error: {result['message']}")
            return
        
        print(f"✅ Document processed: {result['chunks_created']} chunks created")
        print(f"Processing time: {result['processing_time']:.1f}s")
        
        # Interactive Q&A
        print("\n=== Ask questions about your document ===")
        print("Type 'quit' to exit")
        print("Type 'history' to see previous questions")
        print("Type 'stats' to see statistics\n")
        
        while True:
            question = input("Question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if question.lower() == 'history':
                print("\n=== Recent Questions ===")
                history = qa_service.get_query_history(user_id=1, limit=5)
                if history:
                    for i, query in enumerate(history, 1):
                        print(f"{i}. Q: {query['question'][:60]}...")
                        print(f"   A: {query['answer'][:60]}...")
                        print(f"   Time: {query['response_time']:.1f}s, Confidence: {query['confidence_score']}")
                        print()
                else:
                    print("No previous questions found.")
                print("-" * 50)
                continue
            
            if question.lower() == 'stats':
                print("\n=== Statistics ===")
                stats = qa_service.get_query_stats()
                print(f"Total queries: {stats['total_queries']}")
                print(f"Unique users: {stats['unique_users']}")
                print(f"Average response time: {stats['avg_response_time']}s")
                print("-" * 50)
                continue
            
            if not question:
                continue
            
            print("Thinking...")
            response = qa_service.ask_question(question, user_id=1)
            
            print(f"\nAnswer: {response['answer']}")
            print(f"Confidence: {response['confidence_score']}")
            print(f"Response time: {response['response_time']:.1f}s")
            print("-" * 50)
        
        print("Goodbye!")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all required services are available")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()