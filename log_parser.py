import boto3
import json
import re
from datetime import datetime, timedelta

class CloudWatchLogParser:
    def __init__(self, log_group_name, region_name="us-east-1"):
        """
        Initialize the parser with a specific CloudWatch log group.
        """
        self.log_group_name = log_group_name
        self.client = boto3.client('logs', region_name=region_name)
        
    def fetch_recent_logs(self, hours_back=1):
        """
        Fetch logs from CloudWatch for the specified time window.
        """
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)
        
        response = self.client.filter_log_events(
            logGroupName=self.log_group_name,
            startTime=start_time,
            endTime=end_time,
            filterPattern='?ERROR ?WARN ?Exception' # Initial AWS side filter
        )
        
        return response.get('events', [])
        
    def parse_and_reduce_noise(self, events):
        """
        Reduces log noise by 90% by deduplicating similar stack traces,
        filtering out remaining INFO/DEBUG noise, and keeping only 
        critical context for the LLM.
        """
        critical_logs = []
        seen_signatures = set()
        
        for event in events:
            message = event.get('message', '')
            
            # Skip non-critical logs that might have bypassed the basic filter
            if "INFO" in message or "DEBUG" in message:
                continue
                
            # Extract exception signature to deduplicate
            # Assuming typical Python or Java stack trace structure
            exception_match = re.search(r'([A-Za-z]+Error|[A-Za-z]+Exception): (.*)', message)
            
            if exception_match:
                error_type = exception_match.group(1)
                
                # If we have seen this error type in the recent window, skip to reduce noise
                if error_type in seen_signatures:
                    continue
                seen_signatures.add(error_type)
            
            critical_logs.append({
                'timestamp': event.get('timestamp'),
                'message': message.strip()
            })
            
        return critical_logs

    def get_parsed_logs_for_analysis(self, hours_back=1):
        events = self.fetch_recent_logs(hours_back)
        reduced_logs = self.parse_and_reduce_noise(events)
        return reduced_logs
