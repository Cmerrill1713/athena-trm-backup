"""
Knowledge Base Auto-Sync
Watches knowledge_base/ folder and auto-embeds changes
"""
import time
import hashlib
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseHandler(FileSystemEventHandler):
    def __init__(self, kb_path: str, embed_script: str):
        self.kb_path = Path(kb_path)
        self.embed_script = embed_script
        self.file_hashes = {}
        self.debounce_time = 2  # Wait 2s before re-embedding
        self.last_embed = 0
        logger.info(f"👁️ Monitoring {kb_path} for changes...")
    
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.md'):
            return
        
        file_path = Path(event.src_path)
        
        # Check if file actually changed (hash comparison)
        try:
            content = file_path.read_text()
            current_hash = hashlib.md5(content.encode()).hexdigest()
            
            if self.file_hashes.get(str(file_path)) == current_hash:
                return  # No actual change
            
            self.file_hashes[str(file_path)] = current_hash
            
            # Debounce: don't re-embed too frequently
            if time.time() - self.last_embed < self.debounce_time:
                logger.debug("Debouncing embed request")
                return
            
            logger.info(f"📝 File changed: {file_path.name}")
            self.trigger_embedding()
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            logger.info(f"➕ New file: {Path(event.src_path).name}")
            time.sleep(0.5)  # Wait for file to be fully written
            self.trigger_embedding()
    
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            logger.info(f"🗑️ File deleted: {Path(event.src_path).name}")
            self.trigger_embedding()
    
    def trigger_embedding(self):
        """Run embedding script"""
        logger.info("🔄 Auto-embedding knowledge base...")
        self.last_embed = time.time()
        
        try:
            result = subprocess.run(
                ["python3", self.embed_script],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.kb_path.parent)
            )
            
            if result.returncode == 0:
                logger.info("✅ Auto-embedding complete")
                # Notify UAI to refresh (optional)
            else:
                logger.error(f"❌ Embedding failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Embedding error: {e}")


def start_watcher(kb_path: str = "./knowledge_base", 
                   embed_script: str = "./embed_knowledge_base.py"):
    """Start watching knowledge base folder"""
    event_handler = KnowledgeBaseHandler(kb_path, embed_script)
    observer = Observer()
    observer.schedule(event_handler, kb_path, recursive=True)
    observer.start()
    
    logger.info(f"🚀 Knowledge Auto-Sync started")
    logger.info(f"   Path: {kb_path}")
    logger.info(f"   Script: {embed_script}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("👋 Stopping Knowledge Auto-Sync")
    
    observer.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_watcher()

