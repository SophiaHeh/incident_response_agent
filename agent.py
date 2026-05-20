import os
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class IncidentResponseAgent:
    def __init__(self, model_name="claude-3-opus-20240229"):
        """
        Initialize the LangChain agent using the Claude API for Root Cause Analysis (RCA).
        """
        # Ensure ANTHROPIC_API_KEY is set in the environment
        self.llm = ChatAnthropic(
            model_name=model_name,
            temperature=0.2, # Low temperature for more deterministic analysis
            max_tokens=2048
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert Site Reliability Engineer (SRE) and Incident Response Agent. "
                       "Your job is to perform Root Cause Analysis (RCA) on microservice failures. "
                       "You will be provided with filtered application logs and historical context from a RAG pipeline. "
                       "Analyze the information and provide a structured response containing: "
                       "1. The likely Root Cause. "
                       "2. Immediate Remediation Steps. "
                       "3. Long-term Prevention Plan."),
            ("user", "Here are the filtered error logs from the current incident:\n{logs}\n\n"
                     "Here is relevant historical context and runbooks from our knowledge base:\n{rag_context}\n\n"
                     "Please provide the Root Cause Analysis.")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
        
    def perform_rca(self, current_logs, rag_context):
        """
        Perform Root Cause Analysis using the Claude LLM.
        """
        # Format logs and context for the prompt
        formatted_logs = "\n".join([f"[{log['timestamp']}] {log['message']}" for log in current_logs])
        formatted_context = "\n\n".join([doc['content'] for doc in rag_context])
        
        print("Starting RCA via Claude API...")
        response = self.chain.invoke({
            "logs": formatted_logs,
            "rag_context": formatted_context
        })
        
        return response
