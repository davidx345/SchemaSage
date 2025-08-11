"""
GitHub Actions Integration Module
GitHub Actions CI/CD integration for database migration pipelines.
"""
import aiohttp
import yaml
import base64
from typing import Dict, List, Any

from ...models.cicd import CIPipeline

class GitHubActionsIntegration:
    """GitHub Actions CI/CD integration."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def create_workflow_file(self, repo_owner: str, repo_name: str, workflow_config: Dict[str, Any]) -> bool:
        """Create GitHub Actions workflow file."""
        workflow_yaml = yaml.dump(workflow_config, default_flow_style=False)
        
        # Create workflow file content
        file_content = {
            "message": "Add SchemaSage migration workflow",
            "content": self._encode_base64(workflow_yaml)
        }
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/contents/.github/workflows/schemasage-migration.yml"
            async with session.put(url, headers=self.headers, json=file_content) as response:
                return response.status == 201
    
    async def trigger_workflow(self, repo_owner: str, repo_name: str, workflow_id: str, ref: str = "main", inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger a GitHub Actions workflow."""
        trigger_data = {
            "ref": ref,
            "inputs": inputs or {}
        }
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/dispatches"
            async with session.post(url, headers=self.headers, json=trigger_data) as response:
                if response.status == 204:
                    return {"status": "triggered"}
                else:
                    raise Exception(f"Failed to trigger workflow: {await response.text()}")
    
    async def get_workflow_runs(self, repo_owner: str, repo_name: str, workflow_id: str) -> List[Dict[str, Any]]:
        """Get workflow run history."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/runs"
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("workflow_runs", [])
                else:
                    return []
    
    async def get_run_status(self, repo_owner: str, repo_name: str, run_id: str) -> Dict[str, Any]:
        """Get specific workflow run status."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}"
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
    
    def generate_migration_workflow(self, pipeline: CIPipeline) -> Dict[str, Any]:
        """Generate GitHub Actions workflow for migration testing."""
        workflow = {
            "name": "SchemaSage Migration Pipeline",
            "on": {
                "push": {
                    "branches": pipeline.target_branches
                },
                "pull_request": {
                    "branches": pipeline.target_branches
                }
            },
            "jobs": {
                "migration-test": {
                    "runs-on": "ubuntu-latest",
                    "services": {
                        "postgres": {
                            "image": "postgres:13",
                            "env": {
                                "POSTGRES_PASSWORD": "postgres"
                            },
                            "options": "--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5"
                        }
                    },
                    "steps": [
                        {
                            "uses": "actions/checkout@v3"
                        },
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {
                                "python-version": "3.11"
                            }
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -r requirements.txt"
                        },
                        {
                            "name": "Run migration validation",
                            "run": "python -m schemasage.cli validate-migration",
                            "env": {
                                "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/test"
                            }
                        },
                        {
                            "name": "Run migration tests",
                            "run": "python -m pytest tests/migration/"
                        },
                        {
                            "name": "Test rollback",
                            "run": "python -m schemasage.cli test-rollback"
                        }
                    ]
                }
            }
        }
        
        return workflow
    
    def _encode_base64(self, content: str) -> str:
        """Encode content to base64."""
        return base64.b64encode(content.encode()).decode()
