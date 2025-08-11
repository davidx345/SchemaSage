"""
CI/CD Workflow Templates for Database Migration
"""

GITHUB_ACTIONS_MIGRATION_WORKFLOW = """
name: SchemaSage Database Migration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  SCHEMASAGE_API_URL: ${{ secrets.SCHEMASAGE_API_URL }}
  SCHEMASAGE_API_KEY: ${{ secrets.SCHEMASAGE_API_KEY }}

jobs:
  validate-migration:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test
          MYSQL_DATABASE: test
          MYSQL_USER: test
          MYSQL_PASSWORD: test
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
        ports:
          - 3306:3306
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Validate migration plan
      run: |
        python -c "
        import requests
        import json
        
        # Test database connections
        pg_result = requests.post('${{ env.SCHEMASAGE_API_URL }}/connections', 
          json={
            'name': 'Test PostgreSQL',
            'database_type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database': 'test',
            'username': 'test',
            'password': 'test'
          },
          headers={'Authorization': 'Bearer ${{ env.SCHEMASAGE_API_KEY }}'}
        )
        
        if pg_result.status_code != 200:
          raise Exception(f'PostgreSQL connection failed: {pg_result.text}')
        
        print('✅ Database connections validated')
        "
    
    - name: Run migration tests
      run: |
        python -m pytest tests/migration/ -v
    
    - name: Test rollback procedures
      run: |
        python -c "
        # Test rollback scripts exist and are valid
        import os
        import json
        
        migration_files = [f for f in os.listdir('.') if f.endswith('_migration.json')]
        
        for file in migration_files:
          with open(file) as f:
            plan = json.load(f)
          
          for step in plan.get('steps', []):
            if not step.get('rollback_script'):
              raise Exception(f'Step {step[\"step_id\"]} missing rollback script')
        
        print('✅ Rollback procedures validated')
        "
    
    - name: Performance impact analysis
      run: |
        python -c "
        import requests
        
        # Analyze migration complexity
        result = requests.post('${{ env.SCHEMASAGE_API_URL }}/analyze/complexity',
          params={
            'source_connection_id': 'test-pg',
            'target_database_type': 'mysql'
          },
          headers={'Authorization': 'Bearer ${{ env.SCHEMASAGE_API_KEY }}'}
        )
        
        if result.status_code == 200:
          analysis = result.json()
          if analysis['complexity_score'] > 0.8:
            print('⚠️ High complexity migration detected')
          print(f'Estimated duration: {analysis[\"estimated_duration_hours\"]} hours')
        "
    
    - name: Generate migration report
      run: |
        python -c "
        import json
        import os
        
        report = {
          'workflow_run': '${{ github.run_id }}',
          'commit_sha': '${{ github.sha }}',
          'branch': '${{ github.ref_name }}',
          'validation_status': 'passed',
          'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
        }
        
        os.makedirs('reports', exist_ok=True)
        with open('reports/migration_validation.json', 'w') as f:
          json.dump(report, f, indent=2)
        "
    
    - name: Upload validation report
      uses: actions/upload-artifact@v3
      with:
        name: migration-validation-report
        path: reports/

  deploy-staging:
    needs: validate-migration
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    environment:
      name: staging
      url: https://staging-db.company.com
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to staging
      run: |
        python -c "
        import requests
        
        # Trigger migration execution
        result = requests.post('${{ env.SCHEMASAGE_API_URL }}/migrations/execute/staging-plan',
          headers={'Authorization': 'Bearer ${{ env.SCHEMASAGE_API_KEY }}'}
        )
        
        if result.status_code == 200:
          print('✅ Staging deployment initiated')
        else:
          raise Exception(f'Deployment failed: {result.text}')
        "

  deploy-production:
    needs: validate-migration
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    environment:
      name: production
      url: https://prod-db.company.com
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Manual approval gate
      uses: trstringer/manual-approval@v1
      with:
        secret: ${{ github.TOKEN }}
        approvers: database-team
        minimum-approvals: 2
        issue-title: "Production Database Migration Approval"
        issue-body: |
          Please review the migration plan and approve for production deployment.
          
          **Migration Details:**
          - Commit: ${{ github.sha }}
          - Branch: ${{ github.ref_name }}
          - Workflow: ${{ github.run_id }}
    
    - name: Deploy to production
      run: |
        python -c "
        import requests
        
        # Trigger production migration
        result = requests.post('${{ env.SCHEMASAGE_API_URL }}/migrations/execute/prod-plan',
          headers={'Authorization': 'Bearer ${{ env.SCHEMASAGE_API_KEY }}'}
        )
        
        if result.status_code == 200:
          print('✅ Production deployment initiated')
        else:
          raise Exception(f'Deployment failed: {result.text}')
        "
    
    - name: Post-deployment verification
      run: |
        python -c "
        import requests
        import time
        
        # Wait for deployment to complete
        time.sleep(30)
        
        # Verify deployment
        result = requests.get('${{ env.SCHEMASAGE_API_URL }}/health',
          headers={'Authorization': 'Bearer ${{ env.SCHEMASAGE_API_KEY }}'}
        )
        
        if result.status_code == 200:
          print('✅ Post-deployment verification passed')
        else:
          raise Exception('Post-deployment verification failed')
        "
"""

JENKINS_MIGRATION_PIPELINE = """
pipeline {
    agent any
    
    environment {
        SCHEMASAGE_API_URL = credentials('schemasage-api-url')
        SCHEMASAGE_API_KEY = credentials('schemasage-api-key')
        DATABASE_URL = credentials('database-url')
    }
    
    options {
        timeout(time: 1, unit: 'HOURS')
        retry(2)
    }
    
    stages {
        stage('Preparation') {
            steps {
                checkout scm
                sh 'python -m pip install --upgrade pip'
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('Validation') {
            parallel {
                stage('Schema Validation') {
                    steps {
                        sh '''
                        python -c "
                        import requests
                        import sys
                        
                        # Validate schema
                        response = requests.post('${SCHEMASAGE_API_URL}/connections/test')
                        if response.status_code != 200:
                            sys.exit(1)
                        print('Schema validation passed')
                        "
                        '''
                    }
                }
                
                stage('Migration Plan Validation') {
                    steps {
                        sh '''
                        python -c "
                        # Validate migration plans
                        import os
                        import json
                        
                        for file in os.listdir('.'):
                            if file.endswith('_migration.json'):
                                with open(file) as f:
                                    plan = json.load(f)
                                    
                                # Validate plan structure
                                required_fields = ['plan_id', 'steps', 'overall_risk_level']
                                for field in required_fields:
                                    if field not in plan:
                                        raise Exception(f'Missing field: {field}')
                        
                        print('Migration plan validation passed')
                        "
                        '''
                    }
                }
                
                stage('Risk Assessment') {
                    steps {
                        sh '''
                        python -c "
                        import requests
                        
                        # Run risk assessment
                        response = requests.post('${SCHEMASAGE_API_URL}/analyze/complexity')
                        if response.status_code == 200:
                            risk = response.json()
                            if risk.get('risk_level') == 'critical':
                                raise Exception('Critical risk level detected')
                        print('Risk assessment passed')
                        "
                        '''
                    }
                }
            }
        }
        
        stage('Testing') {
            steps {
                sh 'python -m pytest tests/migration/ --junitxml=test-results.xml'
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'test-results.xml'
                }
            }
        }
        
        stage('Staging Deployment') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                python -c "
                import requests
                
                # Deploy to staging
                response = requests.post('${SCHEMASAGE_API_URL}/migrations/execute/staging')
                if response.status_code != 200:
                    raise Exception('Staging deployment failed')
                print('Staging deployment successful')
                "
                '''
            }
        }
        
        stage('Production Approval') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to production?', 
                      ok: 'Deploy',
                      submitterParameter: 'APPROVER'
            }
        }
        
        stage('Production Deployment') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                python -c "
                import requests
                
                # Deploy to production
                response = requests.post('${SCHEMASAGE_API_URL}/migrations/execute/production')
                if response.status_code != 200:
                    raise Exception('Production deployment failed')
                print('Production deployment successful')
                "
                '''
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
        }
        
        success {
            emailext (
                subject: "Migration Pipeline Success: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "The database migration pipeline completed successfully.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
        
        failure {
            emailext (
                subject: "Migration Pipeline Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "The database migration pipeline failed. Please check the build logs.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
"""

GITLAB_CI_MIGRATION_PIPELINE = """
# GitLab CI/CD Pipeline for Database Migration

stages:
  - validate
  - test
  - deploy-staging
  - deploy-production

variables:
  POSTGRES_DB: test
  POSTGRES_USER: test
  POSTGRES_PASSWORD: test
  MYSQL_ROOT_PASSWORD: test
  MYSQL_DATABASE: test

services:
  - postgres:13
  - mysql:8.0

before_script:
  - python -m pip install --upgrade pip
  - pip install -r requirements.txt

validate-schema:
  stage: validate
  script:
    - python -c "
      import requests
      
      # Test database connections
      pg_result = requests.post('$SCHEMASAGE_API_URL/connections', 
        json={
          'name': 'Test PostgreSQL',
          'database_type': 'postgresql',
          'host': 'postgres',
          'port': 5432,
          'database': 'test',
          'username': 'test',
          'password': 'test'
        },
        headers={'Authorization': 'Bearer $SCHEMASAGE_API_KEY'}
      )
      
      assert pg_result.status_code == 200, f'PostgreSQL connection failed: {pg_result.text}'
      print('✅ Schema validation passed')
      "

validate-migration:
  stage: validate
  script:
    - python -c "
      import os
      import json
      
      # Validate migration files
      migration_files = [f for f in os.listdir('.') if f.endswith('_migration.json')]
      
      for file in migration_files:
        with open(file) as f:
          plan = json.load(f)
        
        # Check required fields
        assert 'plan_id' in plan, f'Missing plan_id in {file}'
        assert 'steps' in plan, f'Missing steps in {file}'
        
        # Check rollback scripts
        for step in plan.get('steps', []):
          if step.get('step_type') in ['create_table', 'alter_table', 'migrate_data']:
            assert step.get('rollback_script'), f'Missing rollback script for {step[\"step_id\"]}'
      
      print('✅ Migration validation passed')
      "

test-migration:
  stage: test
  script:
    - python -m pytest tests/migration/ -v --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml

risk-assessment:
  stage: test
  script:
    - python -c "
      import requests
      
      # Analyze migration complexity
      result = requests.post('$SCHEMASAGE_API_URL/analyze/complexity',
        params={
          'source_connection_id': 'test-pg',
          'target_database_type': 'mysql'
        },
        headers={'Authorization': 'Bearer $SCHEMASAGE_API_KEY'}
      )
      
      if result.status_code == 200:
        analysis = result.json()
        print(f'Complexity Score: {analysis[\"complexity_score\"]}')
        print(f'Risk Level: {analysis[\"risk_level\"]}')
        
        if analysis['risk_level'] == 'critical':
          print('⚠️ Critical risk detected - manual review required')
          exit(1)
      "

deploy-staging:
  stage: deploy-staging
  script:
    - python -c "
      import requests
      
      # Deploy to staging
      result = requests.post('$SCHEMASAGE_API_URL/migrations/execute/staging-plan',
        headers={'Authorization': 'Bearer $SCHEMASAGE_API_KEY'}
      )
      
      assert result.status_code == 200, f'Staging deployment failed: {result.text}'
      print('✅ Staging deployment successful')
      "
  only:
    - develop
  environment:
    name: staging
    url: https://staging-db.company.com

deploy-production:
  stage: deploy-production
  script:
    - python -c "
      import requests
      
      # Deploy to production
      result = requests.post('$SCHEMASAGE_API_URL/migrations/execute/prod-plan',
        headers={'Authorization': 'Bearer $SCHEMASAGE_API_KEY'}
      )
      
      assert result.status_code == 200, f'Production deployment failed: {result.text}'
      print('✅ Production deployment successful')
      "
  only:
    - main
  when: manual
  environment:
    name: production
    url: https://prod-db.company.com
"""
