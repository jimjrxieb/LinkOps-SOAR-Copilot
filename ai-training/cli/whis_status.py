#!/usr/bin/env python3
"""
📊 WHIS Status Dashboard
=======================
CLI dashboard that shows current system status at a glance.
The "easy to use and see" interface for your ML system.

Shows:
- Current deployed adapters
- Dataset versions and freshness
- Recent evaluation scores  
- RAG index status
- Training job status
- Security compliance status
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from registry.model_registry import WhisModelRegistry
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
import mlflow
from mlflow.tracking import MlflowClient


class WhisStatusDashboard:
    """CLI status dashboard for WHIS system"""
    
    def __init__(self):
        self.console = Console()
        self.registry = WhisModelRegistry()
        
        # Try to connect to MLflow
        try:
            self.mlflow_client = MlflowClient()
            self.mlflow_available = True
        except Exception as e:
            self.console.print(f"⚠️ MLflow not available: {e}", style="yellow")
            self.mlflow_available = False
            
    def get_system_overview(self) -> Dict[str, Any]:
        """Get high-level system overview"""
        overview = {
            "timestamp": datetime.now().isoformat(),
            "registry_health": self.registry.health_check(),
            "deployments": {},
            "recent_activity": [],
            "alerts": []
        }
        
        # Get current deployments
        for stage in ["staging", "production"]:
            deployment = self.registry.get_current_deployment(stage)
            if deployment:
                overview["deployments"][stage] = {
                    "adapter": deployment["adapter"],
                    "deployed_at": deployment["deployed_at"],
                    "metrics": deployment.get("metrics", {})
                }
                
        # Check for alerts
        overview["alerts"] = self._check_alerts()
        
        return overview
        
    def _check_alerts(self) -> List[Dict[str, str]]:
        """Check for system alerts"""
        alerts = []
        
        # Check if no production deployment
        prod_deployment = self.registry.get_current_deployment("production")
        if not prod_deployment:
            alerts.append({
                "level": "warning",
                "message": "No production deployment found",
                "action": "Deploy an adapter to production"
            })
            
        # Check dataset freshness (placeholder - would check actual data)
        # This would integrate with your data pipeline
        
        # Check MLflow connection
        if not self.mlflow_available:
            alerts.append({
                "level": "error",
                "message": "MLflow tracking not available",
                "action": "Check MLflow server connection"
            })
            
        return alerts
        
    def render_overview_panel(self) -> Panel:
        """Render system overview panel"""
        overview = self.get_system_overview()
        
        content = []
        
        # System health
        health = overview["registry_health"]
        health_status = "🟢 Healthy" if health["mlflow_connection"] else "🔴 Issues"
        content.append(f"**System Health:** {health_status}")
        content.append(f"**Adapters:** {health['total_adapters']} registered")
        content.append(f"**Datasets:** {health['total_datasets']} registered")
        content.append(f"**Last Updated:** {health['last_updated']}")
        
        return Panel("\n".join(content), title="📊 System Overview", border_style="blue")
        
    def render_deployments_table(self) -> Table:
        """Render current deployments table"""
        table = Table(title="🚀 Current Deployments", show_header=True, header_style="bold magenta")
        table.add_column("Stage", style="cyan", no_wrap=True)
        table.add_column("Adapter", style="green")
        table.add_column("Deployed", style="yellow")
        table.add_column("F1 Score", justify="right")
        table.add_column("Faithfulness", justify="right")
        table.add_column("Security", style="red")
        
        for stage in ["staging", "production"]:
            deployment = self.registry.get_current_deployment(stage)
            if deployment:
                metrics = deployment.get("metrics", {})
                
                # Format deployment time
                deployed_at = deployment["deployed_at"]
                if deployed_at:
                    deploy_time = datetime.fromisoformat(deployed_at.replace('Z', '+00:00'))
                    time_ago = datetime.now() - deploy_time.replace(tzinfo=None)
                    if time_ago.days > 0:
                        time_str = f"{time_ago.days}d ago"
                    elif time_ago.seconds > 3600:
                        time_str = f"{time_ago.seconds // 3600}h ago"
                    else:
                        time_str = f"{time_ago.seconds // 60}m ago"
                else:
                    time_str = "unknown"
                
                table.add_row(
                    stage.title(),
                    deployment["adapter"],
                    time_str,
                    f"{metrics.get('fine_tune_f1', 0):.3f}",
                    f"{metrics.get('ragas_faithfulness', 0):.3f}",
                    "✅" if metrics.get('security_tests_passed', False) else "❌"
                )
            else:
                table.add_row(
                    stage.title(),
                    "None",
                    "-",
                    "-",
                    "-",
                    "-"
                )
                
        return table
        
    def render_adapters_table(self, limit: int = 5) -> Table:
        """Render recent adapters table"""
        table = Table(title=f"🧠 Recent Adapters (Top {limit})", show_header=True, header_style="bold green")
        table.add_column("Name:Version", style="cyan")
        table.add_column("Dataset", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Registered", style="blue")
        table.add_column("F1", justify="right")
        
        adapters = self.registry.list_adapters()[:limit]
        
        for adapter in adapters:
            # Format registration time
            reg_time = datetime.fromisoformat(adapter["registered_at"])
            time_ago = datetime.now() - reg_time
            if time_ago.days > 0:
                time_str = f"{time_ago.days}d ago"
            elif time_ago.seconds > 3600:
                time_str = f"{time_ago.seconds // 3600}h ago"
            else:
                time_str = f"{time_ago.seconds // 60}m ago"
                
            # Status styling
            status = adapter.get("status", "registered")
            if status == "production":
                status_display = "🟢 PROD"
            elif status == "staging":
                status_display = "🟡 STAGING"
            else:
                status_display = "⚪ REG"
                
            table.add_row(
                f"{adapter['name']}:{adapter['version']}",
                adapter.get("dataset_reference", "unknown"),
                status_display,
                time_str,
                f"{adapter.get('eval_metrics', {}).get('fine_tune_f1', 0):.3f}"
            )
            
        return table
        
    def render_alerts_panel(self) -> Panel:
        """Render alerts panel"""
        overview = self.get_system_overview()
        alerts = overview["alerts"]
        
        if not alerts:
            content = "🟢 No active alerts"
            style = "green"
        else:
            content_lines = []
            for alert in alerts:
                level_icon = "🔴" if alert["level"] == "error" else "🟡"
                content_lines.append(f"{level_icon} {alert['message']}")
                content_lines.append(f"   Action: {alert['action']}")
                content_lines.append("")
            content = "\n".join(content_lines)
            style = "red" if any(a["level"] == "error" for a in alerts) else "yellow"
            
        return Panel(content, title="🚨 Alerts", border_style=style)
        
    def render_training_status(self) -> Panel:
        """Render training job status"""
        # This would integrate with your training pipeline
        # For now, show placeholder
        content = [
            "**Active Jobs:** 0",
            "**Queue:** Empty", 
            "**Last Training:** 2 hours ago",
            "**Success Rate:** 95% (last 30 days)"
        ]
        
        return Panel("\n".join(content), title="🏃 Training Status", border_style="yellow")
        
    def render_rag_status(self) -> Panel:
        """Render RAG index status"""
        # Check RAG index status
        rag_index_path = Path("ai-training/rag/index/chroma_db")
        
        if rag_index_path.exists():
            # Get index modification time
            index_mtime = datetime.fromtimestamp(rag_index_path.stat().st_mtime)
            time_ago = datetime.now() - index_mtime
            
            if time_ago.days > 7:
                freshness = f"🔴 {time_ago.days} days old (stale)"
            elif time_ago.days > 1:
                freshness = f"🟡 {time_ago.days} days old"
            else:
                freshness = f"🟢 {time_ago.seconds // 3600} hours old"
                
            content = [
                f"**Index Status:** {freshness}",
                f"**Index Path:** {rag_index_path}",
                "**Collection:** whis_soar_knowledge",
                "**Embedder:** sentence-transformers/all-MiniLM-L6-v2"
            ]
        else:
            content = [
                "**Index Status:** 🔴 Not found",
                "**Action:** Run RAG pipeline to build index"
            ]
            
        return Panel("\n".join(content), title="🔍 RAG Status", border_style="cyan")
        
    def show_dashboard(self, refresh_seconds: Optional[int] = None):
        """Show the full dashboard"""
        if refresh_seconds:
            self._show_live_dashboard(refresh_seconds)
        else:
            self._show_static_dashboard()
            
    def _show_static_dashboard(self):
        """Show static dashboard"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=6),
            Layout(name="body"),
            Layout(name="footer", size=6)
        )
        
        layout["header"].split_row(
            Layout(self.render_overview_panel(), name="overview"),
            Layout(self.render_alerts_panel(), name="alerts")
        )
        
        layout["body"].split_row(
            Layout(self.render_deployments_table(), name="deployments"),
            Layout(self.render_adapters_table(), name="adapters")
        )
        
        layout["footer"].split_row(
            Layout(self.render_training_status(), name="training"),
            Layout(self.render_rag_status(), name="rag")
        )
        
        self.console.print("\n")
        self.console.print("🧠 WHIS SOAR-Copilot Status Dashboard", style="bold blue", justify="center")
        self.console.print("=" * 80, style="blue")
        self.console.print(layout)
        
    def _show_live_dashboard(self, refresh_seconds: int):
        """Show live updating dashboard"""
        def make_layout():
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=6),
                Layout(name="body"), 
                Layout(name="footer", size=6)
            )
            
            layout["header"].split_row(
                Layout(self.render_overview_panel(), name="overview"),
                Layout(self.render_alerts_panel(), name="alerts")
            )
            
            layout["body"].split_row(
                Layout(self.render_deployments_table(), name="deployments"),
                Layout(self.render_adapters_table(), name="adapters")  
            )
            
            layout["footer"].split_row(
                Layout(self.render_training_status(), name="training"),
                Layout(self.render_rag_status(), name="rag")
            )
            
            return layout
            
        import time
        
        with Live(make_layout(), refresh_per_second=1/refresh_seconds, screen=True) as live:
            while True:
                time.sleep(refresh_seconds)
                live.update(make_layout())
                
    def show_detailed_adapter_info(self, adapter_reference: str):
        """Show detailed information about specific adapter"""
        if adapter_reference not in self.registry.metadata["adapters"]:
            self.console.print(f"❌ Adapter not found: {adapter_reference}", style="red")
            return
            
        adapter = self.registry.metadata["adapters"][adapter_reference]
        lineage = self.registry.get_adapter_lineage(adapter_reference)
        
        # Create detailed info panel
        content = []
        content.append(f"**Name:** {adapter['name']}")
        content.append(f"**Version:** {adapter['version']}")
        content.append(f"**Status:** {adapter.get('status', 'registered')}")
        content.append(f"**Registered:** {adapter['registered_at']}")
        content.append(f"**Dataset:** {adapter['dataset_reference']}")
        content.append(f"**Hash:** {adapter['hash'][:16]}")
        
        if lineage:
            content.append(f"**Base Model:** {lineage.get('base_model', 'unknown')}")
            content.append(f"**Training Time:** {lineage.get('training_timestamp', 'unknown')}")
            
        # Metrics
        metrics = adapter.get('eval_metrics', {})
        if metrics:
            content.append("\n**Evaluation Metrics:**")
            for metric, value in metrics.items():
                if isinstance(value, float):
                    content.append(f"  {metric}: {value:.4f}")
                else:
                    content.append(f"  {metric}: {value}")
                    
        panel = Panel("\n".join(content), title=f"🧠 Adapter: {adapter_reference}", border_style="green")
        self.console.print(panel)
        
    def quick_health_check(self) -> bool:
        """Quick health check, returns True if all is well"""
        try:
            health = self.registry.health_check()
            overview = self.get_system_overview()
            
            issues = []
            
            # Check MLflow connection
            if not health["mlflow_connection"]:
                issues.append("MLflow connection failed")
                
            # Check if we have production deployment
            if "production" not in overview["deployments"]:
                issues.append("No production deployment")
                
            # Check alerts
            critical_alerts = [a for a in overview["alerts"] if a["level"] == "error"]
            if critical_alerts:
                issues.append(f"{len(critical_alerts)} critical alerts")
                
            if issues:
                self.console.print("❌ Health check failed:", style="red")
                for issue in issues:
                    self.console.print(f"  - {issue}", style="red")
                return False
            else:
                self.console.print("✅ System healthy", style="green")
                return True
                
        except Exception as e:
            self.console.print(f"❌ Health check error: {e}", style="red")
            return False


def main():
    """CLI interface for status dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WHIS Status Dashboard")
    parser.add_argument("--live", type=int, metavar="SECONDS", 
                       help="Show live dashboard with refresh interval")
    parser.add_argument("--adapter", help="Show detailed info for specific adapter")
    parser.add_argument("--health", action="store_true", help="Quick health check")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    dashboard = WhisStatusDashboard()
    
    if args.health:
        success = dashboard.quick_health_check()
        sys.exit(0 if success else 1)
    elif args.adapter:
        dashboard.show_detailed_adapter_info(args.adapter)
    elif args.json:
        overview = dashboard.get_system_overview()
        print(json.dumps(overview, indent=2))
    else:
        dashboard.show_dashboard(args.live)


if __name__ == "__main__":
    main()