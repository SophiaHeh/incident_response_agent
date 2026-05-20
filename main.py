import os
from dotenv import load_dotenv
from log_parser import CloudWatchLogParser
from rag_pipeline import IncidentKnowledgeBase
from agent import IncidentResponseAgent
from slack_notifier import SlackNotifier

# Load environment variables (e.g., ANTHROPIC_API_KEY, SLACK_WEBHOOK_URL, AWS credentials)
load_dotenv()

def main():
    print("Initializing Intelligent Incident Response Agent...")
    
    # 1. Initialize components
    # Using a placeholder log group name for demonstration
    log_parser = CloudWatchLogParser(log_group_name="/aws/microservices/production-cluster")
    
    knowledge_base = IncidentKnowledgeBase(persist_directory="./chroma_db")
    # Uncomment to ingest data initially:
    # knowledge_base.populate_knowledge_base("./runbooks")
    
    rca_agent = IncidentResponseAgent(model_name="claude-3-opus-20240229")
    slack_notifier = SlackNotifier()
    
    # 2. Fetch and parse logs from CloudWatch
    print("Fetching and filtering logs from CloudWatch...")
    # Mocking hours_back for the demonstration
    try:
        critical_logs = log_parser.get_parsed_logs_for_analysis(hours_back=1)
        if not critical_logs:
            print("No critical errors found in the recent log window.")
            return
            
        print(f"Reduced log noise. Processing {len(critical_logs)} critical log events.")
    except Exception as e:
        print(f"Skipping actual AWS fetch for demo purposes, error: {e}")
        # Injecting dummy log for demonstration if AWS is not configured
        critical_logs = [
            {"timestamp": 1680000000, "message": "ConnectionError: Timeout communicating with payment-service database."}
        ]
        
    # 3. Retrieve historical context from ChromaDB RAG Pipeline
    print("Retrieving historical context from RAG pipeline...")
    # Use the first critical log's message as the query to find similar past incidents
    query = critical_logs[0]['message'] 
    rag_context = knowledge_base.search_similar_incidents(query, n_results=3)
    
    # 4. Perform Root Cause Analysis with Claude API via LangChain
    print("Performing GenAI Root Cause Analysis...")
    rca_report = rca_agent.perform_rca(critical_logs, rag_context)
    
    # 5. Alert the team via Slack Webhook
    print("Sending real-time incident alert to Slack...")
    alert_title = f"Critical Incident Detected: {query[:50]}..."
    
    slack_notifier.send_alert(
        title=alert_title,
        message="A potential microservice failure has been detected. The AI-generated Root Cause Analysis is provided below:",
        context=rca_report
    )
    
    print("Incident Response Workflow Completed Successfully.")
    print("-" * 40)
    print("RCA REPORT:\n")
    print(rca_report)

if __name__ == "__main__":
    main()
