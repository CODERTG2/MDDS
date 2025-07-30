import os
import tempfile
import pandas as pd
from dotenv import load_dotenv

# Fix temp directory issue before importing ragas
temp_dir = "/Users/tanmayshubhgarg/Documents/Projects/DePaulProject/temp"
os.makedirs(temp_dir, exist_ok=True)
os.environ['TMPDIR'] = temp_dir

from langchain_community.document_loaders import DirectoryLoader
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

# Import RAGAS components
try:
    from ragas.testset import TestsetGenerator
    from ragas.testset.evolutions import simple, reasoning, multi_context
except ImportError:
    try:
        from ragas import TestsetGenerator
        from ragas.testset import simple, reasoning, multi_context
    except ImportError:
        print("❌ RAGAS import failed. Please install: pip install ragas")
        exit(1)

# Load environment variables
load_dotenv()

# --- 1. Set up your environment ---
# Make sure to set your Azure OpenAI API key in .env file

# --- 2. Load your documents ---
# Check if papersfortesting directory exists and has proper files
papers_dir = "./papersfortesting/"

if not os.path.exists(papers_dir):
    print(f"❌ Directory {papers_dir} not found. Creating dummy document.")
    from langchain_core.documents import Document
    documents = [Document(
        page_content="Medical devices are regulated by the FDA to ensure safety and efficacy. "
                   "Blood glucose monitors help diabetic patients track their blood sugar levels. "
                   "These devices must undergo rigorous testing before market approval.",
        metadata={"source": "dummy_medical_device_info.txt"}
    )]
else:
    # Check for valid document files
    valid_extensions = ['.pdf', '.txt', '.docx', '.md']
    files = [f for f in os.listdir(papers_dir) 
             if any(f.lower().endswith(ext) for ext in valid_extensions)]
    
    if not files:
        print(f"❌ No valid documents found in {papers_dir}")
        print("📄 Creating dummy medical device document for testing.")
        from langchain_core.documents import Document
        documents = [Document(
            page_content="Medical devices are regulated by the FDA to ensure safety and efficacy. "
                       "Blood glucose monitors help diabetic patients track their blood sugar levels. "
                       "These devices must undergo rigorous testing before market approval. "
                       "Continuous glucose monitors provide real-time glucose readings. "
                       "Machine learning algorithms are increasingly used in diagnostic devices.",
            metadata={"source": "dummy_medical_device_info.txt"}
        )]
    else:
        print(f"✅ Found {len(files)} documents in {papers_dir}")
        try:
            loader = DirectoryLoader(
                papers_dir,
                glob="**/*",
                use_multithreading=True,
                silent_errors=True,
                sample_size=3  # Limit to 3 documents for testing
            )
            documents = loader.load()
            
            if not documents:
                print("❌ Failed to load documents. Using dummy document.")
                from langchain_core.documents import Document
                documents = [Document(
                    page_content="Medical devices are regulated by the FDA to ensure safety and efficacy. "
                               "Blood glucose monitors help diabetic patients track their blood sugar levels.",
                    metadata={"source": "dummy_medical_device_info.txt"}
                )]
            else:
                print(f"✅ Successfully loaded {len(documents)} documents")
                # Add proper metadata
                for doc in documents:
                    if "source" in doc.metadata:
                        doc.metadata["filename"] = os.path.basename(doc.metadata["source"])
                        
        except Exception as e:
            print(f"❌ Error loading documents: {e}")
            print("📄 Creating dummy document for demonstration.")
            from langchain_core.documents import Document
            documents = [Document(
                page_content="Medical devices are regulated by the FDA to ensure safety and efficacy. "
                           "Blood glucose monitors help diabetic patients track their blood sugar levels.",
                metadata={"source": "dummy_medical_device_info.txt"}
            )]


# --- 3. Initialize Azure OpenAI Models ---
# Using Azure OpenAI instead of regular OpenAI to match your project setup
try:
    generator_llm = AzureChatOpenAI(
        azure_endpoint="https://aoai-camp.openai.azure.com/",
        api_version="2024-12-01-preview",
        deployment_name="abbott_researcher",  # Your deployment name
        api_key=os.getenv("AZURE_OPEN_AI_KEY"),
        temperature=0.1
    )
    
    critic_llm = AzureChatOpenAI(
        azure_endpoint="https://aoai-camp.openai.azure.com/",
        api_version="2024-12-01-preview",
        deployment_name="abbott_researcher",  # Your deployment name
        api_key=os.getenv("AZURE_OPEN_AI_KEY"),
        temperature=0.1
    )
    
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint="https://aoai-camp.openai.azure.com/",
        api_version="2024-12-01-preview", 
        deployment="text-embedding-ada-002",  # Your embedding deployment
        api_key=os.getenv("AZURE_OPEN_AI_KEY")
    )
    
    print("✅ Azure OpenAI models initialized successfully")
    
except Exception as e:
    print(f"❌ Error initializing Azure OpenAI models: {e}")
    print("Please check your .env file contains AZURE_OPEN_AI_KEY")
    exit(1)

# --- 4. Create the TestsetGenerator ---
# The TestsetGenerator is the main class for creating your test data.
try:
    generator = TestsetGenerator.from_langchain(
        generator_llm,
        critic_llm,
        embeddings
    )
    print("✅ TestsetGenerator initialized successfully")
except Exception as e:
    print(f"❌ Error creating TestsetGenerator: {e}")
    exit(1)

# --- 5. Generate the Test Set ---
# Here, we specify the number of questions to generate (test_size=5 for testing).
# We also define the distribution of question types we want.
print("🔄 Generating test set... This may take a few minutes.")

try:
    testset = generator.generate_with_langchain_docs(
        documents,
        test_size=5,  # Start with 5 questions for testing
        raise_exceptions=False,
        with_debugging_logs=True,
        distributions={
            simple: 0.5,      # 50% simple questions
            reasoning: 0.25,  # 25% reasoning questions
            multi_context: 0.25 # 25% multi-context questions
        }
    )
    print(f"✅ Successfully generated test set with {len(testset)} questions")
    
except Exception as e:
    print(f"❌ Error generating test set: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# --- 6. View and save the generated test set ---
try:
    # The generated test set can be easily converted to a pandas DataFrame.
    df = testset.to_pandas()

    # Display the full content of the DataFrame
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 100)  # Limit column width for readability

    print("\n" + "="*80)
    print("GENERATED TEST SET")
    print("="*80)
    print(df.head())

    # Save to CSV file
    output_file = "medical_device_test_set.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✅ Test set successfully generated and saved to {output_file}")
    
    # Print summary
    print(f"\n📊 SUMMARY:")
    print(f"   - Total questions: {len(df)}")
    print(f"   - Document sources: {len(documents)}")
    print(f"   - Output file: {output_file}")
    
    if len(df) > 0:
        print(f"\n🔍 SAMPLE QUESTION:")
        print(f"   Q: {df.iloc[0]['question'][:100]}...")
        print(f"   A: {df.iloc[0]['answer'][:100]}...")

except Exception as e:
    print(f"❌ Error processing test set: {e}")
    import traceback
    traceback.print_exc()

