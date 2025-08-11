"""
Jenkins Integration Module
Jenkins CI/CD integration for database migration pipelines.
"""
import aiohttp
from typing import Dict, Any

from ...models.cicd import CIPipeline

class JenkinsIntegration:
    """Jenkins CI/CD integration."""
    
    def __init__(self, jenkins_url: str, username: str, api_token: str):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = (username, api_token)
    
    async def create_job(self, job_name: str, job_config: str) -> bool:
        """Create a Jenkins job."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.jenkins_url}/createItem?name={job_name}"
            headers = {"Content-Type": "application/xml"}
            
            async with session.post(url, auth=aiohttp.BasicAuth(*self.auth), headers=headers, data=job_config) as response:
                return response.status == 200
    
    async def trigger_build(self, job_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger a Jenkins build."""
        if parameters:
            url = f"{self.jenkins_url}/job/{job_name}/buildWithParameters"
            data = parameters
        else:
            url = f"{self.jenkins_url}/job/{job_name}/build"
            data = {}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, auth=aiohttp.BasicAuth(*self.auth), data=data) as response:
                if response.status == 201:
                    # Get queue item location from header
                    location = response.headers.get('Location', '')
                    return {"status": "queued", "location": location}
                else:
                    raise Exception(f"Failed to trigger build: {response.status}")
    
    async def get_build_status(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Get Jenkins build status."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.jenkins_url}/job/{job_name}/{build_number}/api/json"
            async with session.get(url, auth=aiohttp.BasicAuth(*self.auth)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
    
    def generate_jenkinsfile(self, pipeline: CIPipeline) -> str:
        """Generate Jenkinsfile for migration pipeline."""
        jenkinsfile = f"""
pipeline {{
    agent any
    
    environment {{
        DATABASE_URL = credentials('database-url')
        SCHEMASAGE_API_KEY = credentials('schemasage-api-key')
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}
        
        stage('Setup') {{
            steps {{
                sh 'pip install -r requirements.txt'
            }}
        }}
        
        stage('Validate Migration') {{
            steps {{
                sh 'python -m schemasage.cli validate-migration'
            }}
        }}
        
        stage('Test Migration') {{
            parallel {{
                stage('Unit Tests') {{
                    steps {{
                        sh 'python -m pytest tests/unit/'
                    }}
                }}
                stage('Integration Tests') {{
                    steps {{
                        sh 'python -m pytest tests/integration/'
                    }}
                }}
            }}
        }}
        
        stage('Deploy to Staging') {{
            when {{
                branch 'develop'
            }}
            steps {{
                sh 'python -m schemasage.cli deploy --environment staging'
            }}
        }}
        
        stage('Deploy to Production') {{
            when {{
                branch 'main'
            }}
            steps {{
                input message: 'Deploy to production?', ok: 'Deploy'
                sh 'python -m schemasage.cli deploy --environment production'
            }}
        }}
    }}
    
    post {{
        always {{
            publishTestResults testResultsPattern: 'test-results.xml'
            archiveArtifacts artifacts: 'migration-logs/**/*', allowEmptyArchive: true
        }}
        failure {{
            emailext (
                subject: "Migration Pipeline Failed: ${{env.JOB_NAME}} - ${{env.BUILD_NUMBER}}",
                body: "The migration pipeline failed. Check the build logs for details.",
                to: "${{env.CHANGE_AUTHOR_EMAIL}}"
            )
        }}
    }}
}}
"""
        return jenkinsfile
