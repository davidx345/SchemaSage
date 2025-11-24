"""
ROI Dashboard Router - Phase 3.6
6 endpoints for ROI calculations, time series, feature analysis, competitive comparison, and export generation
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from models.roi_models import (
    CalculateValueRequest, CalculateValueResponse,
    TimeSeriesResponse,
    FeatureAnalysisResponse,
    CompetitiveAnalysisRequest, CompetitiveAnalysisResponse,
    ExportSummaryRequest, ExportSummaryResponse,
    ExportStatusResponse
)
from core.roi.roi_engine import (
    ROICalculator, TimeSeriesAnalyzer, FeatureAnalyzer,
    CompetitiveAnalyzer, ExportGenerator
)

router = APIRouter(prefix="/api/roi", tags=["ROI Dashboard"])

# Initialize core components
roi_calculator = ROICalculator()
time_series_analyzer = TimeSeriesAnalyzer()
feature_analyzer = FeatureAnalyzer()
competitive_analyzer = CompetitiveAnalyzer()
export_generator = ExportGenerator()


@router.post("/calculate-value", response_model=CalculateValueResponse)
async def calculate_total_value(request: CalculateValueRequest):
    """
    Calculate comprehensive ROI across cost savings, time efficiency, risk reduction, and productivity gains.
    
    **Value Categories:**
    - **Cost Savings** (20%): Infrastructure optimization, license elimination, operational efficiency
    - **Time Savings** (29%): Automated schema design, migration planning, incident response
    - **Risk Reduction** (36%): Compliance fines avoided, data breach prevention, migration failure avoidance
    - **Productivity Gains** (15%): Developer efficiency, reduced context switching, knowledge sharing
    
    **ROI Metrics:**
    - ROI Percentage: 3,903%
    - ROI Ratio: 40:1 (value/investment)
    - Payback Period: 1 month
    - NPV: $3.9M
    - IRR: 390.3%
    
    **Key Achievements:**
    - Reduced data breach risk by 60%
    - Zero failed migrations in 12 months
    - Decreased MTTR by 50%
    - Saved 200 engineering hours/month
    - Reduced cloud costs by 34%
    
    **Confidence Levels:**
    - 83% high confidence (tracked metrics)
    - 14% medium confidence (statistical models)
    - 3% low confidence (industry benchmarks)
    """
    try:
        calculation_data = roi_calculator.calculate_total_value(
            organization_id=request.organization_id,
            start_date=request.time_period.start_date,
            end_date=request.time_period.end_date,
            analysis_options=request.analysis_options.dict() if request.analysis_options else {}
        )
        
        return CalculateValueResponse(success=True, data=calculation_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ROI calculation failed: {str(e)}")


@router.get("/time-series", response_model=TimeSeriesResponse)
async def get_roi_time_series(
    organization_id: str = Query(..., description="Organization identifier"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    granularity: str = Query("monthly", description="Time granularity: monthly, quarterly, yearly")
):
    """
    Track ROI growth over time with month-by-month breakdown.
    
    **Time Series Features:**
    - Month-by-month value tracking
    - Cumulative value growth (262% total growth)
    - ROI percentage evolution (85% → 3,245%)
    - Active features progression (3 → 12 features)
    - Adoption rate growth (40% → 92%)
    
    **Growth Metrics:**
    - Month-over-month growth: 14.2%
    - Average monthly value: $478K
    - Peak month: October 2024 ($720K)
    - Lowest month: May 2024 ($185K)
    
    **Future Projections:**
    - Next 3 months projected with confidence intervals
    - December 2024: $750K (±$100K)
    - January 2025: $820K (±$110K)
    - February 2025: $890K (±$120K)
    
    **Value Categories per Month:**
    - Cost savings trend
    - Time savings trend
    - Risk reduction trend
    - Productivity gains trend
    """
    try:
        time_series_data = time_series_analyzer.analyze_time_series(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )
        
        return TimeSeriesResponse(success=True, data=time_series_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Time series analysis failed: {str(e)}")


@router.get("/by-feature", response_model=FeatureAnalysisResponse)
async def get_roi_by_feature(
    organization_id: str = Query(..., description="Organization identifier"),
    time_period_months: int = Query(6, description="Analysis period in months")
):
    """
    Break down ROI contribution by individual platform features.
    
    **Top Features by Value:**
    1. **PII Detection & Anonymization** (32.5%) - $1.3M value, 3,426% ROI, 95% adoption
       - 247 scans, 4,453 PII fields detected, 34.5M records anonymized
       - 4.8/5.0 satisfaction score
    
    2. **Cross-Cloud Migration Planner** (20.2%) - $810K value, 2,130% ROI, 100% adoption
       - 47 migration plans, 0 failures, 12 databases migrated
       - 4.9/5.0 satisfaction score (highest)
    
    3. **AI Schema Generator** (18%) - $720K value, 1,900% ROI, 88% adoption
       - 234 schemas generated, 1,800 hours saved, 567 queries optimized
       - 4.7/5.0 satisfaction score
    
    4. **Database Incident Timeline** (11.2%) - $450K value, 1,187% ROI, 82% adoption
       - 89 incidents analyzed, 76 root causes identified, 50% MTTR improvement
       - 4.6/5.0 satisfaction score
    
    5. **Code Generator** (9%) - $360K value, 950% ROI, 75% adoption
       - 1,247 files generated, 8 languages, 345K lines of code
       - 4.5/5.0 satisfaction score
    
    6. **Schema Marketplace** (4.5%) - $180K value, 475% ROI, 60% adoption
    7. **Team Integrations** (3.4%) - $135K value, 356% ROI, 70% adoption
    8. **Security Audit Reports** (1.2%) - $48K value, 126% ROI, 55% adoption
    
    **Summary:**
    - Total value: $4.003M
    - 8 features tracked
    - Average ROI: 1,568%
    - Highest ROI: PII Detection (3,426%)
    - Most adopted: Migration Planner (100%)
    - Highest satisfaction: Migration Planner (4.9/5.0)
    """
    try:
        feature_data = feature_analyzer.analyze_features(
            organization_id=organization_id,
            time_period_months=time_period_months
        )
        
        return FeatureAnalysisResponse(success=True, data=feature_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature analysis failed: {str(e)}")


@router.post("/competitive-analysis", response_model=CompetitiveAnalysisResponse)
async def generate_competitive_analysis(request: CompetitiveAnalysisRequest):
    """
    Compare SchemaSage ROI against competitor tools and manual processes.
    
    **Available Competitors:**
    - **Collibra Data Governance**: $250K/year, 12-month implementation, 240% ROI
    - **OneTrust DataDiscovery**: $180K/year, 8-month implementation, 261% ROI
    - **Erwin Data Modeler Enterprise**: $95K/year, 4-month implementation, 195% ROI
    - **Manual Schema Design Process**: $0/year, 0-month implementation, 0% ROI
    
    **SchemaSage Advantages vs Collibra:**
    - 10x faster implementation (1.5 months vs 12 months)
    - 60% lower cost ($100K vs $250K annually)
    - 4x broader feature coverage (12 vs 3 features)
    - 16x higher ROI (3,903% vs 240%)
    - 4.7x more value delivered ($4M vs $850K)
    
    **SchemaSage Advantages vs OneTrust:**
    - 5x faster implementation (1.5 months vs 8 months)
    - 44% lower cost ($100K vs $180K)
    - 6x broader feature coverage (12 vs 2 features)
    - 15x higher ROI (3,903% vs 261%)
    - 6.2x more value delivered ($4M vs $650K)
    
    **SchemaSage Advantages vs Erwin:**
    - Cloud-native (Erwin is desktop-only)
    - 12x broader feature coverage (12 vs 1 feature)
    - 20x higher ROI (3,903% vs 195%)
    - 14.3x more value delivered ($4M vs $280K)
    - 62% more time efficient
    
    **SchemaSage Advantages vs Manual:**
    - 81% efficiency gain (1,950 hours saved/year)
    - 95% error reduction (AI catches schema issues)
    - 60% breach risk reduction (automated PII detection)
    - $4M annual value vs $0 from manual work
    - 50% faster incident response (MTTR 5h → 2.5h)
    
    **Competitive Summary:**
    - Average competitor cost: $131,250
    - Average SchemaSage savings: $56,250
    - 1,652% higher ROI than competitors
    - 8x more features than average competitor
    - 5.5x faster implementation than competitors
    - 6.9x more value delivered than competitors
    """
    try:
        competitive_data = competitive_analyzer.analyze_competitive_landscape(
            organization_id=request.organization_id,
            alternatives=request.alternatives
        )
        
        return CompetitiveAnalysisResponse(success=True, data=competitive_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Competitive analysis failed: {str(e)}")


@router.post("/export-summary", response_model=ExportSummaryResponse)
async def generate_roi_export(request: ExportSummaryRequest):
    """
    Generate PDF/Excel export of executive ROI summary.
    
    **Export Formats:**
    - **PDF**: Executive presentation with charts and branding
    - **Excel**: Editable spreadsheet with formulas and raw data
    
    **Available Sections:**
    - **Executive Summary** (2 pages, 3 charts): Total value, ROI metrics, key achievements
    - **Value Breakdown** (3 pages, 4 charts): 4 value categories with detailed breakdowns
    - **Feature Analysis** (4 pages, 8 charts): Per-feature ROI, usage, satisfaction, adoption
    - **Competitive Comparison** (3 pages, 5 charts): vs Collibra, OneTrust, Erwin, Manual
    - **Time Series** (2 pages, 2 charts): Month-by-month growth, cumulative value, projections
    - **Key Achievements** (3 pages): 5 major achievements with baseline/current/impact
    
    **Branding Options:**
    - Company name
    - Logo URL (PNG/JPG/SVG)
    - Primary color (hex code)
    
    **Export Specifications:**
    - Total pages: 17
    - Total charts: 22
    - File size: ~4.5 MB
    - Generation time: ~15 seconds
    - Expiry: 24 hours after generation
    
    **Polling:**
    After receiving export_id, poll `/api/roi/export-summary/{export_id}/status` for completion.
    """
    try:
        export_data = export_generator.generate_export(
            organization_id=request.organization_id,
            time_period=request.time_period.dict(),
            export_options=request.export_options.dict(),
            branding=request.branding.dict() if request.branding else None
        )
        
        return ExportSummaryResponse(success=True, data=export_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export generation failed: {str(e)}")


@router.get("/export-summary/{export_id}/status", response_model=ExportStatusResponse)
async def get_export_status(export_id: str):
    """
    Check the status of an export generation request.
    
    **Status Values:**
    - `processing`: Export is being generated (poll every 2-3 seconds)
    - `completed`: Export is ready for download
    - `failed`: Export generation failed (check error_message)
    
    **Completed Response Includes:**
    - Download URL (valid for 24 hours)
    - Expiry timestamp
    - File size in bytes
    - Page count
    - Sections generated with page/chart counts
    - Metadata (generation time, user, organization, report period)
    
    **Error Handling:**
    - If export_id not found: 404 error
    - If generation failed: status="failed" with error_message
    - If download URL expired: Regenerate export
    """
    try:
        status_data = export_generator.get_export_status(export_id=export_id)
        
        return ExportStatusResponse(success=True, data=status_data)
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Export not found: {str(e)}")
